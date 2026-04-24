"""
HiChIP Pipeline Orchestrator

Runs the full HiChIP analysis pipeline end-to-end:
  1. FASTQ splitting       (FastqSplitter, n_chunks parallel jobs)
  2. Parallel alignment    (BWA MEM -5SP -T0, per chunk)
  3. BAM merge + BEDPE     (samtools merge + pysam dedup by 5' coordinate)
  4. MboI purification     (FragmentIndex + purify_bedpe)
  5. Background model      (randomised positions, distance-decay stats)

Key differences from ChIA-PET:
  - No linker filtering step (enzyme-based, not linker-based)
  - BWA MEM -5SP -T0 flags (HiChIP chimeric read handling)
  - Filter -F 2304 (drop unmapped + secondary) instead of MAPQ cutoff
  - MboI restriction fragment purification (replaces linker dedup)
  - Background model generates randomised PETs preserving distance

Output layout::

    <output_dir>/
    ├── splits/          per-chunk FASTQ + BAM files (removed after merge)
    ├── aligned/         merged name-sorted BAM
    ├── bedpe/           raw BEDPE + deduplicated BEDPE
    ├── purified/        MboI-filtered BEDPE + removed PETs + stats
    ├── background/      randomised background BEDPE + distance stats
    └── qc/              per-step stats + timing report

Validated configuration (500k read pairs, 76bp, hg38):
  - 6 chunks × 4 threads = 13s alignment
  - 37.2% unique valid PETs after dedup
  - 88.2% retention after MboI purification
  - Total pipeline time ~41s

References:
    Bhattacharyya et al. (2019) HiChIP: efficient and sensitive enrichment of
    protein-directed chromatin architecture. Nature Methods.
"""

import itertools
import json
import os
import random
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import system info utility
from ..utils.system_info import save_system_info

# Resolve the bin directory of the active Python / conda environment so that
# child processes (multiprocessing) can find bwa and samtools on PATH.
_ENV_BIN = str(Path(sys.executable).parent)

import numpy as np
import pysam

from ..utils.logging import get_logger
from .purifying import FragmentIndex, purify_bedpe

logger = get_logger(__name__)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} min"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


def _fmt_int(val: Any) -> str:
    """Format an integer-like value with thousands separators; 'N/A' otherwise."""
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, int):
        return f"{val:,}"
    if isinstance(val, float) and float(val).is_integer():
        return f"{int(val):,}"
    return "N/A" if val is None else str(val)


def _fmt_pct(numer: Any, denom: Any) -> str:
    """Return 'xx.xx%' if both are positive numbers; 'N/A' otherwise."""
    try:
        n = float(numer)
        d = float(denom)
        if d > 0:
            return f"{100 * n / d:.2f}%"
    except (TypeError, ValueError):
        pass
    return "N/A"


def _json_default(obj: Any):
    """JSON fallback for numpy / defaultdict / Path / set objects."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, "keys") and hasattr(obj, "values"):
        return dict(obj)
    return str(obj)


def _save_step_stats(
    steps_dir: str,
    key: str,
    stats: Any,
    timing_key: Optional[str] = None,
    seconds: Optional[float] = None,
) -> None:
    """Persist one step's stats (+ timing) to JSON so that a later
    ``start_from`` resume can reload the values rather than showing N/A."""
    try:
        os.makedirs(steps_dir, exist_ok=True)
        path = os.path.join(steps_dir, f"{key}.json")
        payload = {key: stats, "timing_key": timing_key, "seconds": seconds}
        with open(path, "w") as fh:
            json.dump(payload, fh, default=_json_default, indent=2)
    except Exception as exc:  # best-effort persistence
        logger.warning(f"  Could not persist {key} to {steps_dir}: {exc}")


def _load_prior_steps(steps_dir: str) -> Dict[str, Any]:
    """Load any previously-saved per-step JSONs back into a dict."""
    out: Dict[str, Any] = {"timing": {}}
    if not os.path.isdir(steps_dir):
        return out
    for fname in os.listdir(steps_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(steps_dir, fname)
        try:
            with open(path) as fh:
                payload = json.load(fh)
        except Exception as exc:
            logger.warning(f"  Ignoring unreadable step file {path}: {exc}")
            continue
        key = fname[: -len(".json")]
        if isinstance(payload, dict) and key in payload:
            out[key] = payload[key]
            tkey = payload.get("timing_key")
            secs = payload.get("seconds")
            if tkey and isinstance(secs, (int, float)):
                out["timing"][tkey] = float(secs)
        else:
            out[key] = payload
    return out


# ─── sanity checks ────────────────────────────────────────────────────────────

def _sanity_check_purification(stats: Dict, sample_id: str) -> List[str]:
    """
    Run sanity checks on MboI purification stats.
    Returns a list of warning strings (empty = all OK).
    """
    warnings = []
    total = stats.get("total", 0)
    if total == 0:
        warnings.append("WARN: 0 PETs passed to purification step")
        return warnings

    kept_pct   = 100 * stats["kept"] / total
    same_pct   = 100 * stats["removed_same_fragment"] / total
    unmap_pct  = 100 * stats["removed_unmappable"] / total
    short_pct  = 100 * stats["removed_short_insert"] / total
    accounted  = (stats["kept"] + stats["removed_same_fragment"]
                  + stats["removed_unmappable"] + stats["removed_short_insert"])

    if accounted != total:
        warnings.append(
            f"FAIL: accounting error — kept+removed={accounted} != total={total}"
        )
    if not (20 <= kept_pct <= 90):
        warnings.append(
            f"WARN: kept {kept_pct:.1f}% outside expected HiChIP range (20-90%)"
        )
    if same_pct > 60:
        warnings.append(
            f"WARN: same-fragment {same_pct:.1f}% > 60% — possible self-ligation issue"
        )
    if unmap_pct > 30:
        warnings.append(
            f"WARN: unmappable {unmap_pct:.1f}% > 30% — check fragment BED coverage"
        )
    return warnings


def _sanity_check_bedpe(valid: int, total: int, unmapped: int) -> List[str]:
    """Sanity checks on BEDPE conversion step."""
    warnings = []
    if total == 0:
        warnings.append("WARN: BAM contains 0 read groups")
        return warnings
    valid_pct = 100 * valid / total
    unmap_pct = 100 * unmapped / total
    if valid_pct < 5:
        warnings.append(
            f"WARN: only {valid_pct:.1f}% valid PETs — very low alignment rate"
        )
    if unmap_pct > 80:
        warnings.append(
            f"WARN: {unmap_pct:.1f}% pairs unmapped — check genome index / read length"
        )
    return warnings


# ─── pipeline ─────────────────────────────────────────────────────────────────

class HiChIPPipeline:
    """
    End-to-end HiChIP pipeline orchestrator.

    Parameters
    ----------
    genome_index : str
        Path to BWA-indexed genome FASTA (must have .amb, .ann, .bwt etc.).
    fragment_bed : str
        Restriction fragment BED file (from restriction_sites.py, e.g. MboI).
    threads : int
        Total CPU threads. Split across parallel alignment jobs.
    n_chunks : int
        Number of FASTQ chunks for parallel BWA jobs (default 6).
        BWA threads per job = threads // n_chunks.
    min_insert_size : int
        Minimum insert size for MboI purification (default 100 bp).
    genome_fai : str, optional
        Path to genome .fai index (for background model chromosome sizes).
        Inferred from genome_index + '.fai' if not provided.
    keep_intermediates : bool
        Retain per-chunk FASTQ/BAM files after merge (default False).
    random_seed : int
        Seed for background model randomisation (default 42).
    """

    def __init__(
        self,
        genome_index: str,
        fragment_bed: str,
        threads: int = 24,
        n_chunks: int = 6,
        min_insert_size: int = 100,
        genome_fai: Optional[str] = None,
        keep_intermediates: bool = False,
        random_seed: int = 42,
        # Loop calling parameters (ChIA-PET style background model)
        genome_size: str = 'hs',
        qvalue: float = 0.01,
        alpha: float = 0.05,
        standard_chroms_only: bool = True,
        cytoband_file: Optional[str] = None,
        background_samples: int = 10000,
    ):
        self.genome_index = genome_index
        self.fragment_bed = fragment_bed
        self.threads = threads
        self.n_chunks = n_chunks
        self.min_insert_size = min_insert_size
        self.genome_fai = genome_fai or f"{genome_index}.fai"
        self.keep_intermediates = keep_intermediates
        self.random_seed = random_seed

        # Loop calling config
        self.genome_size = genome_size
        self.qvalue = qvalue
        self.alpha = alpha
        self.standard_chroms_only = standard_chroms_only
        self.cytoband_file = cytoband_file
        self.background_samples = background_samples

        # Derived: BWA threads per chunk
        self.bwa_threads = max(1, threads // n_chunks)

        self._validate()

    def _validate(self):
        """Check required files exist before running."""
        missing = []
        for ext in ['.amb', '.ann', '.bwt', '.pac', '.sa']:
            if not Path(f"{self.genome_index}{ext}").exists():
                missing.append(f"{self.genome_index}{ext}")
        if missing:
            raise FileNotFoundError(f"BWA index incomplete. Missing: {missing}")
        if not Path(self.fragment_bed).exists():
            raise FileNotFoundError(f"Fragment BED not found: {self.fragment_bed}")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        fastq_r1: Optional[str] = None,
        fastq_r2: Optional[str] = None,
        output_dir: str = "./results",
        sample_id: str = "sample",
        start_from: int = 1,
    ) -> Dict:
        """
        Run the full HiChIP pipeline, or resume from a later step.

        Parameters
        ----------
        fastq_r1 : str, optional
            Path to R1 FASTQ (gzipped or plain). Required when ``start_from<=1``.
        fastq_r2 : str, optional
            Path to R2 FASTQ (gzipped or plain). Required when ``start_from<=1``.
        output_dir : str
            Root output directory (created if absent).
        sample_id : str
            Sample name used as file prefix.
        start_from : int
            Step to resume from:
              1=split FASTQ, 2=align chunks, 3=merge BAMs,
              4=BAM→BEDPE dedup, 5=MboI purification, 6=background model.
            Default 1 runs the full pipeline. When resuming, the pre-computed
            outputs from previous steps must exist under ``output_dir``.

        Returns
        -------
        dict
            Collected stats from every step + timing breakdown.
        """
        t_pipeline = time.time()
        if start_from < 1 or start_from > 6:
            raise ValueError(
                f"start_from must be between 1 and 6 (got {start_from})"
            )
        if start_from == 1 and (not fastq_r1 or not fastq_r2):
            raise ValueError(
                "fastq_r1 and fastq_r2 are required when start_from=1"
            )

        # Capture system configuration before pipeline starts
        out = Path(output_dir)
        qc_dir = out / "qc"
        steps_dir = qc_dir / "steps"
        qc_dir.mkdir(parents=True, exist_ok=True)
        steps_dir.mkdir(parents=True, exist_ok=True)
        system_info_path = qc_dir / "system_configuration.txt"
        save_system_info(str(system_info_path))
        logger.info(f"System configuration saved to {system_info_path}")

        splits_dir     = out / "splits"
        aligned_dir    = out / "aligned"
        bedpe_dir      = out / "bedpe"
        purified_dir   = out / "purified"
        background_dir = out / "background"
        peaks_dir      = out / "peaks"
        loops_dir      = out / "loops"
        classified_dir = loops_dir / "classified"
        templates_dir  = loops_dir / "templates"
        results_dir    = loops_dir / "results"

        for d in [splits_dir, aligned_dir, bedpe_dir,
                  purified_dir, background_dir,
                  peaks_dir, classified_dir, templates_dir, results_dir]:
            d.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 70)
        logger.info("CHR3D  —  HiChIP PIPELINE")
        logger.info("=" * 70)
        logger.info(f"  Sample ID    : {sample_id}")
        logger.info(f"  R1           : {fastq_r1}")
        logger.info(f"  R2           : {fastq_r2}")
        logger.info(f"  Genome       : {self.genome_index}")
        logger.info(f"  Fragments    : {self.fragment_bed}")
        logger.info(f"  Threads      : {self.threads}  ({self.n_chunks} chunks × {self.bwa_threads}t)")
        logger.info(f"  Min insert   : {self.min_insert_size} bp")
        logger.info(f"  Output dir   : {output_dir}")
        logger.info(f"  Start from   : step {start_from}")
        logger.info("=" * 70)

        timing: Dict[str, float] = {}
        all_stats: Dict[str, Any] = {"sample_id": sample_id, "start_from": start_from}

        # Reload any previously-persisted per-step stats so that resuming
        # does not wipe values produced by earlier runs.
        prior = _load_prior_steps(str(steps_dir))
        for key in ("split_stats", "bedpe_stats", "purify_stats",
                    "bg_stats", "loop_stats"):
            if key in prior:
                all_stats[key] = prior[key]
        if "n_chunks" in prior:
            all_stats["n_chunks"] = prior["n_chunks"]
        for step, secs in prior.get("timing", {}).items():
            if step != "total":
                timing[step] = secs

        merged_bam  = str(aligned_dir / f"{sample_id}.namesorted.bam")
        dedup_bedpe = str(bedpe_dir / f"{sample_id}.dedup.bedpe")
        kept_bedpe  = str(purified_dir / f"{sample_id}.filter.byres")

        # ── Step 1: Split FASTQ ────────────────────────────────────────
        if start_from <= 1:
            logger.info("\n[STEP 1] Splitting FASTQ...")
            t0 = time.time()
            chunks = self._split_fastq(fastq_r1, fastq_r2, str(splits_dir))
            timing["split"] = time.time() - t0
            all_stats["n_chunks"] = len(chunks)
            _save_step_stats(
                str(steps_dir), "split_stats",
                {"n_chunks": len(chunks)},
                timing_key="split", seconds=timing["split"],
            )
            # Also persist n_chunks standalone for convenience.
            _save_step_stats(str(steps_dir), "n_chunks", len(chunks))
            logger.info(f"  {len(chunks)} chunks in {_fmt_time(timing['split'])}")
        else:
            logger.info("\n[STEP 1] SKIPPED (resume mode)")
            chunks = []

        # ── Step 2: Parallel alignment ─────────────────────────────────
        if start_from <= 2:
            logger.info("\n[STEP 2] Parallel BWA MEM alignment...")
            t0 = time.time()
            chunk_bams = self._align_parallel(chunks, str(splits_dir))
            timing["alignment"] = time.time() - t0
            logger.info(f"  Done in {_fmt_time(timing['alignment'])}")
        else:
            logger.info("\n[STEP 2] SKIPPED (resume mode)")
            chunk_bams = sorted(
                str(p) for p in splits_dir.glob("chunk_*.namesorted.bam")
            )

        # ── Step 3: Merge BAMs ─────────────────────────────────────────
        if start_from <= 3:
            logger.info("\n[STEP 3] Merging chunk BAMs...")
            t0 = time.time()
            self._merge_bams(chunk_bams, merged_bam)
            timing["merge"] = time.time() - t0
            logger.info(f"  Merged BAM: {Path(merged_bam).stat().st_size / 1e6:.1f} MB"
                        f"  in {_fmt_time(timing['merge'])}")
        else:
            logger.info("\n[STEP 3] SKIPPED (resume mode)")
            if start_from <= 4 and not Path(merged_bam).exists():
                raise FileNotFoundError(
                    f"Cannot resume from step {start_from}: missing {merged_bam}"
                )

        # ── Step 4: BAM → BEDPE + dedup ───────────────────────────────
        if start_from <= 4:
            logger.info("\n[STEP 4] BAM → BEDPE + deduplication...")
            t0 = time.time()
            bedpe_stats = self._bam_to_dedup_bedpe(merged_bam, dedup_bedpe)
            timing["bedpe"] = time.time() - t0
            all_stats["bedpe_stats"] = bedpe_stats
            _save_step_stats(
                str(steps_dir), "bedpe_stats", bedpe_stats,
                timing_key="bedpe", seconds=timing["bedpe"],
            )

            bedpe_warns = _sanity_check_bedpe(
                bedpe_stats["valid"], bedpe_stats["total"], bedpe_stats["unmapped"]
            )
            for w in bedpe_warns:
                logger.warning(f"  {w}")

            logger.info(
                f"  Read pairs : {bedpe_stats['total']:,}\n"
                f"  Unmapped   : {bedpe_stats['unmapped']:,}  "
                f"({100*bedpe_stats['unmapped']/max(bedpe_stats['total'],1):.1f}%)\n"
                f"  Duplicates : {bedpe_stats['duplicates']:,}  "
                f"({100*bedpe_stats['duplicates']/max(bedpe_stats['total'],1):.1f}%)\n"
                f"  Valid PETs : {bedpe_stats['valid']:,}  "
                f"({100*bedpe_stats['valid']/max(bedpe_stats['total'],1):.1f}%)\n"
                f"  Done in {_fmt_time(timing['bedpe'])}"
            )
        else:
            logger.info("\n[STEP 4] SKIPPED (resume mode)")
            if start_from <= 5 and not Path(dedup_bedpe).exists():
                raise FileNotFoundError(
                    f"Cannot resume from step {start_from}: missing {dedup_bedpe}"
                )

        # ── Step 5: MboI purification ──────────────────────────────────
        if start_from <= 5:
            logger.info("\n[STEP 5] MboI restriction fragment purification...")
            t0 = time.time()
            purify_stats = self._run_purification(
                dedup_bedpe, str(purified_dir), sample_id
            )
            timing["purification"] = time.time() - t0
            all_stats["purify_stats"] = purify_stats
            _save_step_stats(
                str(steps_dir), "purify_stats", purify_stats,
                timing_key="purification", seconds=timing["purification"],
            )

            purify_warns = _sanity_check_purification(purify_stats, sample_id)
            for w in purify_warns:
                logger.warning(f"  {w}")

            total = purify_stats["total"]
            logger.info(
                f"  Total PETs    : {total:,}\n"
                f"  Kept          : {purify_stats['kept']:,}  "
                f"({100*purify_stats['kept']/max(total,1):.1f}%)\n"
                f"  Same fragment : {purify_stats['removed_same_fragment']:,}  "
                f"({100*purify_stats['removed_same_fragment']/max(total,1):.1f}%)\n"
                f"  Unmappable    : {purify_stats['removed_unmappable']:,}  "
                f"({100*purify_stats['removed_unmappable']/max(total,1):.1f}%)\n"
                f"  Short insert  : {purify_stats['removed_short_insert']:,}  "
                f"({100*purify_stats['removed_short_insert']/max(total,1):.1f}%)\n"
                f"  Done in {_fmt_time(timing['purification'])}"
            )
        else:
            logger.info("\n[STEP 5] SKIPPED (resume mode)")
            if not Path(kept_bedpe).exists():
                raise FileNotFoundError(
                    f"Cannot resume from step {start_from}: missing {kept_bedpe}"
                )

        # ── Step 6: Background model + loop calling ────────────────────
        logger.info("\n[STEP 6] Generating background model...")
        t0 = time.time()
        bg_stats = self._run_background_model(
            kept_bedpe, str(background_dir), sample_id
        )
        timing["background"] = time.time() - t0
        all_stats["bg_stats"] = bg_stats
        _save_step_stats(
            str(steps_dir), "bg_stats", bg_stats,
            timing_key="background", seconds=timing["background"],
        )
        logger.info(
            f"  Background PETs : {bg_stats['n_background']:,}\n"
            f"  Mean distance   : {bg_stats.get('mean_distance', 0):,.0f} bp\n"
            f"  Done in {_fmt_time(timing['background'])}"
        )

        # Loop calling via ChIA-PET-style background model (peaks → classify
        # → templates → NB sampling → p-values → FDR).
        logger.info("\n[STEP 6b] Peak calling + loop calling...")
        t0 = time.time()
        loop_stats = self._run_loop_calling(
            kept_bedpe=kept_bedpe,
            peaks_dir=str(peaks_dir),
            classified_dir=str(classified_dir),
            templates_dir=str(templates_dir),
            results_dir=str(results_dir),
            sample_id=sample_id,
        )
        timing["loop_calling"] = time.time() - t0
        all_stats["loop_stats"] = loop_stats
        _save_step_stats(
            str(steps_dir), "loop_stats", loop_stats,
            timing_key="loop_calling", seconds=timing["loop_calling"],
        )
        logger.info(f"  Done in {_fmt_time(timing['loop_calling'])}")

        # ── Cleanup intermediates ──────────────────────────────────────
        if not self.keep_intermediates and start_from <= 2:
            self._cleanup_splits(str(splits_dir))

        # ── QC report ─────────────────────────────────────────────────
        timing["total"] = time.time() - t_pipeline
        all_stats["timing"] = timing
        self._write_qc_report(all_stats, str(qc_dir), sample_id)

        logger.info("\n" + "=" * 70)
        logger.info("HiChIP PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"  Total time   : {_fmt_time(timing['total'])}")
        for step, secs in timing.items():
            if step != "total":
                logger.info(f"  {step:<20}: {_fmt_time(secs)}")
        logger.info(f"  Output dir   : {output_dir}")
        logger.info("=" * 70)

        return all_stats

    # ------------------------------------------------------------------
    # Private step implementations
    # ------------------------------------------------------------------

    def _split_fastq(
        self, fastq_r1: str, fastq_r2: str, split_dir: str
    ) -> List[Tuple[str, str]]:
        """Split FASTQ into n_chunks using FastqSplitter."""
        from ..hic.bulk_hic import FastqSplitter

        splitter = FastqSplitter(n_chunks=self.n_chunks)
        chunks = splitter.split(
            fastq1=fastq_r1,
            fastq2=fastq_r2,
            output_dir=split_dir,
            prefix="chunk",
        )
        for i, (r1, r2) in enumerate(chunks):
            n = sum(1 for _ in open(r1)) // 4
            logger.info(f"    chunk_{i:03d}: {n:,} reads")
        return chunks

    def _align_parallel(
        self, chunks: List[Tuple[str, str]], split_dir: str
    ) -> List[str]:
        """
        Align each chunk with BWA MEM -5SP -T0 in parallel.
        Returns list of name-sorted BAM paths.
        """
        import multiprocessing

        jobs = []
        bam_paths = []
        for i, (r1, r2) in enumerate(chunks):
            bam_out = os.path.join(split_dir, f"chunk_{i:03d}.namesorted.bam")
            log_out = os.path.join(split_dir, f"chunk_{i:03d}.bwa.log")
            jobs.append((r1, r2, bam_out, log_out, i))
            bam_paths.append(bam_out)

        processes = []
        for r1, r2, bam_out, log_out, idx in jobs:
            p = multiprocessing.Process(
                target=self._align_one_chunk,
                args=(r1, r2, bam_out, log_out, idx),
            )
            p.start()
            processes.append(p)

        failed = []
        for i, p in enumerate(processes):
            p.join()
            if p.exitcode != 0:
                failed.append(i)

        if failed:
            raise RuntimeError(f"BWA alignment failed for chunks: {failed}")

        logger.info(f"  All {len(chunks)} BWA jobs completed")
        return bam_paths

    def _align_one_chunk(
        self, r1: str, r2: str, bam_out: str, log_out: str, idx: int
    ):
        """Run BWA MEM -5SP -T0 for one chunk (called in subprocess)."""
        cmd = (
            f"export PATH={_ENV_BIN}:$PATH && "
            f"bwa mem -5SP -T0 -t {self.bwa_threads} "
            f"{self.genome_index} {r1} {r2} 2>{log_out} "
            f"| samtools view -@ 2 -b -F 2304 "
            f"| samtools sort -n -@ 2 -m 2G -o {bam_out} -"
        )
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            raise RuntimeError(f"chunk {idx} BWA failed (rc={result.returncode})")
        logger.info(f"    chunk_{idx:03d} done")

    def _merge_bams(self, bam_paths: List[str], merged_bam: str):
        """Merge name-sorted BAMs with samtools merge -n."""
        merge_threads = min(self.threads, 12)
        samtools = os.path.join(_ENV_BIN, "samtools")
        cmd = [samtools, "merge", "-n", f"-@{merge_threads}", "-f",
               merged_bam] + bam_paths
        subprocess.run(cmd, check=True, capture_output=True)

    def _bam_to_dedup_bedpe(self, bam_path: str, out_bedpe: str) -> Dict:
        """
        Convert name-sorted BAM → BEDPE, deduplicated by 5' coordinate.
        Mirrors the validated logic from run_hichip_simple.sh.
        """
        seen  = set()
        total = valid = dup = unmapped = 0

        with pysam.AlignmentFile(bam_path, "rb") as bam, \
             open(out_bedpe, "w") as out:
            for name, grp in itertools.groupby(bam, key=lambda r: r.query_name):
                alns  = list(grp)
                total += 1

                r1s = [a for a in alns if a.is_read1  and not a.is_unmapped]
                r2s = [a for a in alns if a.is_read2  and not a.is_unmapped]
                if not r1s or not r2s:
                    unmapped += 1
                    continue

                r1 = max(r1s, key=lambda a: a.mapping_quality)
                r2 = max(r2s, key=lambda a: a.mapping_quality)

                pos1 = r1.reference_end   if r1.is_reverse else r1.reference_start
                pos2 = r2.reference_end   if r2.is_reverse else r2.reference_start
                s1   = "-" if r1.is_reverse else "+"
                s2   = "-" if r2.is_reverse else "+"
                c1, c2 = r1.reference_name, r2.reference_name

                # Canonical ordering (lower chrom / pos first)
                if c1 > c2 or (c1 == c2 and pos1 > pos2):
                    c1, c2, pos1, pos2, s1, s2 = c2, c1, pos2, pos1, s2, s1

                key = (c1, pos1, c2, pos2)
                if key in seen:
                    dup += 1
                    continue
                seen.add(key)

                score = min(r1.mapping_quality, r2.mapping_quality)
                out.write(
                    f"{c1}\t{pos1}\t{pos1+1}\t{c2}\t{pos2}\t{pos2+1}"
                    f"\t{name}\t{score}\t{s1}\t{s2}\n"
                )
                valid += 1

        return {"total": total, "unmapped": unmapped,
                "duplicates": dup, "valid": valid}

    def _run_purification(
        self, dedup_bedpe: str, purified_dir: str, sample_id: str
    ) -> Dict:
        """Run MboI restriction fragment purification."""
        logger.info("  Loading MboI fragment index...")
        idx = FragmentIndex(self.fragment_bed)
        logger.info(f"  {idx.n_fragments:,} fragments across {len(idx.starts)} chroms")

        kept_path    = os.path.join(purified_dir, f"{sample_id}.filter.byres")
        removed_path = os.path.join(purified_dir, f"{sample_id}.insameres")
        stats_path   = os.path.join(purified_dir, f"{sample_id}.purify_stats.txt")

        stats = purify_bedpe(
            bedpe_file=dedup_bedpe,
            fragment_index=idx,
            output_kept=kept_path,
            output_removed=removed_path,
            min_insert_size=self.min_insert_size,
        )

        # Write stats file
        with open(stats_path, "w") as f:
            for k, v in stats.items():
                f.write(f"{k}\t{v}\n")

        return stats

    def _run_background_model(
        self, kept_bedpe: str, bg_dir: str, sample_id: str
    ) -> Dict:
        """
        Build background model by randomising intra-chromosomal PET positions
        while preserving the empirical distance distribution.
        """
        rng = random.Random(self.random_seed)

        # Load chromosome sizes from .fai
        chrom_sizes: Dict[str, int] = {}
        if Path(self.genome_fai).exists():
            with open(self.genome_fai) as fh:
                for line in fh:
                    parts = line.strip().split("\t")
                    if len(parts) >= 2:
                        chrom_sizes[parts[0]] = int(parts[1])

        # Parse purified PETs
        chrom_counts: Dict[str, int] = defaultdict(int)
        distances: List[int] = []
        pets: List[Tuple] = []

        with open(kept_bedpe) as fh:
            for line in fh:
                fields = line.strip().split("\t")
                if len(fields) < 10:
                    continue
                c1, p1, c2, p2 = fields[0], int(fields[1]), fields[3], int(fields[4])
                s1, s2 = fields[8], fields[9]
                chrom_counts[c1] += 1
                chrom_counts[c2] += 1
                if c1 == c2:
                    distances.append(abs(p2 - p1))
                pets.append((c1, p1, c2, p2, s1, s2, fields[6], fields[7]))

        total_pets = len(pets)

        # Randomise intra-chromosomal positions preserving distance
        bg_bedpe = os.path.join(bg_dir, f"{sample_id}.background.bedpe")
        n_bg = 0
        with open(bg_bedpe, "w") as out:
            for c1, p1, c2, p2, s1, s2, name, score in pets:
                if c1 != c2 or c1 not in chrom_sizes:
                    continue
                dist = abs(p2 - p1)
                max_start = chrom_sizes[c1] - dist - 1000
                # Skip if chromosome is too small to fit the 1000bp margin
                if max_start < 1000:
                    continue
                new_p1 = rng.randint(1000, max_start)
                new_p2 = new_p1 + dist
                out.write(
                    f"{c1}\t{new_p1}\t{new_p1+1}\t"
                    f"{c2}\t{new_p2}\t{new_p2+1}\t"
                    f"{name}\t{score}\t{s1}\t{s2}\n"
                )
                n_bg += 1

        # Compute distance-decay statistics
        bg_stats: Dict = {
            "total_pets": total_pets,
            "n_background": n_bg,
            "chrom_counts": dict(chrom_counts),
        }
        if distances:
            arr = np.array(distances)
            bg_stats["mean_distance"]   = float(np.mean(arr))
            bg_stats["median_distance"] = float(np.median(arr))
            bg_stats["min_distance"]    = int(np.min(arr))
            bg_stats["max_distance"]    = int(np.max(arr))

            # Log-binned histogram for distance decay
            log_bins = np.logspace(np.log10(max(1000, arr.min())),
                                   np.log10(arr.max()), 20)
            hist, edges = np.histogram(arr, bins=log_bins)
            bg_stats["distance_decay"] = {
                "bin_starts": [float(e) for e in edges[:-1]],
                "counts": [int(c) for c in hist],
            }

        # Write stats file
        stats_path = os.path.join(bg_dir, f"{sample_id}.background.stats")
        with open(stats_path, "w") as f:
            f.write("Background Model Statistics\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total PETs         : {total_pets:,}\n")
            f.write(f"Background PETs    : {n_bg:,}\n\n")
            f.write("Chromosome Contact Frequencies:\n")
            total_contacts = sum(chrom_counts.values())
            for chrom in sorted(chrom_counts):
                cnt = chrom_counts[chrom]
                f.write(f"  {chrom:<8}: {cnt:>8,}  ({100*cnt/max(total_contacts,1):.2f}%)\n")
            if distances:
                f.write("\nDistance Statistics (intra-chromosomal):\n")
                f.write(f"  Mean   : {bg_stats['mean_distance']:,.0f} bp\n")
                f.write(f"  Median : {bg_stats['median_distance']:,.0f} bp\n")
                f.write(f"  Min    : {bg_stats['min_distance']:,} bp\n")
                f.write(f"  Max    : {bg_stats['max_distance']:,} bp\n")

        logger.info(f"  Stats: {stats_path}")
        return bg_stats

    def _run_loop_calling(
        self,
        kept_bedpe: str,
        peaks_dir: str,
        classified_dir: str,
        templates_dir: str,
        results_dir: str,
        sample_id: str,
    ) -> Dict:
        """
        Full loop calling using ChIA-PET-style background model:
          a. Peak calling from purified BEDPE (MACS3)
          b. classify_pets + export_by_category → P2P / P2D / D2D files
          c. extract_templates → templates.csv
          d. BackgroundSamplingPhase1 → NB parameters
          e. calculate_pvalues → p-values
          f. apply_fdr_corrections → significant loops CSV
        """
        from .peak_calling import PeakCaller
        from .background_model import (
            load_peaks,
            classify_pets,
            extract_templates,
            BackgroundSamplingPhase1,
            calculate_pvalues,
            apply_fdr_corrections,
        )
        from .background_model.classify_pets import (
            summarize_classification,
            export_by_category,
        )

        stats: Dict = {}

        # --- a: Peak calling on the purified BEDPE (both anchors → BED → MACS3) ---
        logger.info("  [a] Peak calling (MACS3 on purified BEDPE)...")
        peak_caller = PeakCaller(
            genome_size=self.genome_size,
            qvalue_cutoff=self.qvalue,
            conda_env=None,
        )
        peak_prefix = os.path.join(peaks_dir, sample_id)
        peak_stats = peak_caller.call_peaks_from_bedpe(
            bedpe_file=kept_bedpe,
            output_prefix=peak_prefix,
            method='BED',
        )
        peaks_file = peak_stats.get('peaks_file', '')
        stats['peak_stats'] = peak_stats

        if not peaks_file or not os.path.exists(peaks_file):
            logger.warning("  No peaks file found — skipping loop calling")
            return {'skipped': True, 'reason': 'no peaks file', 'peak_stats': peak_stats}
        logger.info(f"    Peaks: {peak_stats.get('num_peaks', 'N/A')} at {peaks_file}")

        # --- b: Classify PETs ---
        logger.info("  [b] Classifying PETs (P2P / P2D / D2D)...")
        peaks_by_chr, peak_ids_by_chr, peaks_df = load_peaks(
            peaks_file,
            standard_chroms_only=self.standard_chroms_only,
            cytoband_file=self.cytoband_file,
        )

        pets_df = classify_pets(
            bedpe_file=kept_bedpe,
            peaks_by_chr=peaks_by_chr,
            peak_ids_by_chr=peak_ids_by_chr,
            peaks_df=peaks_df,
            n_cores=self.threads,
        )

        classify_counts = summarize_classification(pets_df)
        stats['classify'] = classify_counts
        logger.info(f"    P2P: {classify_counts.get('P2P', 0):,}  "
                    f"P2D: {classify_counts.get('P2D', 0):,}  "
                    f"D2D: {classify_counts.get('D2D', 0):,}")

        classify_prefix = os.path.join(classified_dir, sample_id)
        export_by_category(pets_df, classify_prefix)

        p2p_file = f"{classify_prefix}.P2P_pets.txt"
        d2d_file = f"{classify_prefix}.D2D_pets.txt"

        # --- c: Extract templates ---
        logger.info("  [c] Extracting templates from P2P PETs...")
        templates_csv = os.path.join(templates_dir, f"{sample_id}_templates.csv")
        extract_templates(
            p2p_file=p2p_file,
            peak_file=peaks_file,
            output_file=templates_csv,
            standard_chroms_only=self.standard_chroms_only,
            cytoband_file=self.cytoband_file,
        )
        stats['templates_csv'] = templates_csv

        # --- d: Background sampling phase 1 (NB fitting) ---
        logger.info("  [d] Background sampling phase 1 (NB parameter estimation)...")
        templates_nb_csv = os.path.join(
            templates_dir, f"{sample_id}_templates_with_nb.csv"
        )
        sampler = BackgroundSamplingPhase1(samples_per_template=self.background_samples, n_cores=self.threads)
        sampler.load_d2d_pets(d2d_file)
        sampler.process_templates(
            templates_file=templates_csv,
            output_file=templates_nb_csv,
        )
        stats['templates_nb_csv'] = templates_nb_csv

        # --- e: Background sampling phase 2 (p-values) ---
        logger.info("  [e] Calculating p-values (PMF / NB)...")
        pvalues_csv = os.path.join(
            templates_dir, f"{sample_id}_templates_with_pvalues.csv"
        )
        calculate_pvalues(
            templates_file=templates_nb_csv,
            output_file=pvalues_csv,
        )
        stats['pvalues_csv'] = pvalues_csv

        # --- f: FDR correction ---
        logger.info("  [f] Applying FDR correction...")
        loops_csv = os.path.join(
            results_dir, f"{sample_id}_significant_loops.csv"
        )
        apply_fdr_corrections(
            input_file=pvalues_csv,
            output_file=loops_csv,
            alpha=self.alpha,
        )
        stats['loops_csv'] = loops_csv
        logger.info(f"    Loops output: {loops_csv}")

        return stats

    def _cleanup_splits(self, split_dir: str):
        """Remove per-chunk FASTQ and BAM files."""
        import shutil
        if Path(split_dir).exists():
            shutil.rmtree(split_dir)
            logger.info(f"  Removed split directory: {split_dir}")

    def _write_qc_report(
        self, all_stats: Dict, qc_dir: str, sample_id: str
    ):
        """Write a tab-separated QC summary (txt) plus a structured JSON."""
        qc_path   = os.path.join(qc_dir, f"{sample_id}.hichip_qc.txt")
        json_path = os.path.join(qc_dir, f"{sample_id}.hichip_qc.json")
        timing  = all_stats.get("timing", {}) or {}
        bedpe   = all_stats.get("bedpe_stats", {}) or {}
        purify  = all_stats.get("purify_stats", {}) or {}
        bg      = all_stats.get("bg_stats", {}) or {}
        loops   = all_stats.get("loop_stats", {}) or {}

        total_pairs = bedpe.get("total")
        valid_pets  = bedpe.get("valid")
        kept_pets   = purify.get("kept")

        classify   = loops.get("classify", {}) if isinstance(loops, dict) else {}
        peak_stats = loops.get("peak_stats", {}) if isinstance(loops, dict) else {}

        # --- txt (tab-separated, one metric per row) -----------------------
        with open(qc_path, "w") as f:
            f.write(f"sample_id\t{sample_id}\n")
            f.write(f"total_read_pairs\t{_fmt_int(total_pairs)}\n")
            f.write(f"valid_pets_after_dedup\t{_fmt_int(valid_pets)}\n")
            f.write(f"valid_pet_pct\t{_fmt_pct(valid_pets, total_pairs)}\n")
            f.write(f"kept_after_purification\t{_fmt_int(kept_pets)}\n")
            f.write(f"purification_retention_pct\t"
                    f"{_fmt_pct(kept_pets, valid_pets)}\n")
            f.write(f"same_fragment_pct\t"
                    f"{_fmt_pct(purify.get('removed_same_fragment'), valid_pets)}\n")
            f.write(f"background_pets\t{_fmt_int(bg.get('n_background'))}\n")
            f.write(f"peaks_called\t{_fmt_int(peak_stats.get('num_peaks'))}\n")
            f.write(f"p2p_pets\t{_fmt_int(classify.get('P2P'))}\n")
            f.write(f"p2d_pets\t{_fmt_int(classify.get('P2D'))}\n")
            f.write(f"d2d_pets\t{_fmt_int(classify.get('D2D'))}\n")
            f.write(f"significant_loops_csv\t{loops.get('loops_csv', 'N/A')}\n")
            for step, secs in timing.items():
                try:
                    f.write(f"time_{step}_s\t{float(secs):.1f}\n")
                except (TypeError, ValueError):
                    f.write(f"time_{step}_s\tN/A\n")

        # --- json (easily fetched programmatically) ------------------------
        def _safe_pct(n, d):
            try:
                n, d = float(n), float(d)
                if d > 0:
                    return round(100.0 * n / d, 4)
            except (TypeError, ValueError):
                pass
            return None

        summary = {
            "sample_id": sample_id,
            "bedpe": {
                "total_read_pairs":       total_pairs,
                "valid_pets_after_dedup": valid_pets,
                "unmapped":               bedpe.get("unmapped"),
                "duplicates":             bedpe.get("duplicates"),
                "valid_pet_pct":          _safe_pct(valid_pets, total_pairs),
            },
            "purification": {
                "total_input":               purify.get("total"),
                "kept_after_purification":   kept_pets,
                "removed_same_fragment":     purify.get("removed_same_fragment"),
                "removed_unmappable":        purify.get("removed_unmappable"),
                "removed_short_insert":      purify.get("removed_short_insert"),
                "purification_retention_pct": _safe_pct(kept_pets, valid_pets),
                "same_fragment_pct":         _safe_pct(purify.get("removed_same_fragment"),
                                                       valid_pets),
            },
            "background": {
                "background_pets": bg.get("n_background"),
                "mean_distance":   bg.get("mean_distance"),
            },
            "loop_calling": {
                "peaks_called":         peak_stats.get("num_peaks"),
                "peaks_file":           peak_stats.get("peaks_file"),
                "p2p_pets":             classify.get("P2P"),
                "p2d_pets":             classify.get("P2D"),
                "d2d_pets":             classify.get("D2D"),
                "templates_csv":        loops.get("templates_csv"),
                "significant_loops_csv": loops.get("loops_csv"),
            },
            "timing_seconds": {k: float(v) for k, v in timing.items()
                                if isinstance(v, (int, float))},
            "raw_stats": {
                "bedpe_stats":   bedpe,
                "purify_stats":  purify,
                "bg_stats":      bg,
                "loop_stats":    loops,
            },
        }
        with open(json_path, "w") as f:
            json.dump(summary, f, default=_json_default, indent=2)

        logger.info(f"  QC report: {qc_path}")
        logger.info(f"  QC JSON  : {json_path}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    import argparse
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--r1",         required=True, help="R1 FASTQ")
    p.add_argument("--r2",         required=True, help="R2 FASTQ")
    p.add_argument("--genome",     required=True, help="BWA genome index")
    p.add_argument("--fragments",  required=True, help="Restriction fragment BED")
    p.add_argument("--output-dir", required=True, help="Output directory")
    p.add_argument("--sample-id",  default="sample", help="Sample prefix")
    p.add_argument("--threads",    type=int, default=24, help="Total CPU threads")
    p.add_argument("--n-chunks",   type=int, default=6,  help="Parallel BWA jobs")
    p.add_argument("--min-insert", type=int, default=100,
                   help="Min insert size for purification")
    p.add_argument("--keep-intermediates", action="store_true",
                   help="Keep per-chunk files after merge")
    return p.parse_args()


def main():
    args = parse_args()
    pipeline = HiChIPPipeline(
        genome_index=args.genome,
        fragment_bed=args.fragments,
        threads=args.threads,
        n_chunks=args.n_chunks,
        min_insert_size=args.min_insert,
        keep_intermediates=args.keep_intermediates,
    )
    pipeline.run(
        fastq_r1=args.r1,
        fastq_r2=args.r2,
        output_dir=args.output_dir,
        sample_id=args.sample_id,
    )


if __name__ == "__main__":
    main()