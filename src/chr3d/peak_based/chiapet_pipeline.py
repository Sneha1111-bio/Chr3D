# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.logging import get_logger
from ..utils.system_info import save_system_info

logger = get_logger(__name__)


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
    if isinstance(val, (int,)):
        return f"{val:,}"
    if isinstance(val, float) and float(val).is_integer():
        return f"{int(val):,}"
    return "N/A" if val is None else str(val)


def _fmt_pct(numer: Any, denom: Any) -> str:
    """Return 'xx.xx%' if both are positive ints; 'N/A' otherwise."""
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
    try:
        import numpy as np  # local import to avoid hard dep at module load
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except ImportError:
        pass
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, "keys") and hasattr(obj, "values"):
        return dict(obj)
    return str(obj)


class ChiaPetPipeline:
    """End-to-end ChIA-PET pipeline orchestrator."""

    def __init__(
        self,
        genome_index: str,
        linkers: list,
        threads: int = 4,
        mapq: int = 30,
        genome_size: str = 'hs',
        qvalue: float = 0.05,
        alpha: float = 0.05,
        min_score: int = 20,
        min_tag: int = 15,
        max_tag: int = 40,
        standard_chroms_only: bool = True,
        cytoband_file: Optional[str] = None,
        keep_intermediates: bool = False,
    ):
        self.genome_index = genome_index
        self.linkers = linkers
        self.threads = threads
        self.mapq = mapq
        self.genome_size = genome_size
        self.qvalue = qvalue
        self.alpha = alpha
        self.min_score = min_score
        self.min_tag = min_tag
        self.max_tag = max_tag
        self.standard_chroms_only = standard_chroms_only
        self.cytoband_file = cytoband_file
        self.keep_intermediates = keep_intermediates

    def run(
        self,
        fastq_r1: Optional[str] = None,
        fastq_r2: Optional[str] = None,
        output_dir: str = './results',
        sample_id: str = 'sample',
        start_from: int = 1,
    ) -> Dict:
        """Run the full ChIA-PET pipeline, or resume from a later step."""
        pipeline_start = time.time()
        if start_from < 1 or start_from > 4:
            raise ValueError(
                f"start_from must be between 1 and 4 (got {start_from})"
            )
        if start_from == 1 and (not fastq_r1 or not fastq_r2):
            raise ValueError(
                "fastq_r1 and fastq_r2 are required when start_from=1"
            )

        out = Path(output_dir)
        qc_dir = out / 'qc'
        steps_dir = qc_dir / 'steps'
        qc_dir.mkdir(parents=True, exist_ok=True)
        steps_dir.mkdir(parents=True, exist_ok=True)
        system_info_path = qc_dir / 'system_configuration.txt'
        save_system_info(str(system_info_path))
        logger.info(f"System configuration saved to {system_info_path}")

        filtered_dir  = out / 'filtered'
        mapped_dir    = out / 'mapped'
        peaks_dir     = out / 'peaks'
        loops_dir     = out / 'loops'
        classified_dir = loops_dir / 'classified'
        templates_dir  = loops_dir / 'templates'
        results_dir    = loops_dir / 'results'

        for d in [filtered_dir, mapped_dir, peaks_dir,
                  classified_dir, templates_dir, results_dir]:
            d.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 70)
        logger.info("CHR3D  —  ChIA-PET PIPELINE")
        logger.info("=" * 70)
        logger.info(f"  Sample ID  : {sample_id}")
        logger.info(f"  R1         : {fastq_r1}")
        logger.info(f"  R2         : {fastq_r2}")
        logger.info(f"  Genome     : {self.genome_index}")
        logger.info(f"  Linkers    : {self.linkers}")
        logger.info(f"  Threads    : {self.threads}")
        logger.info(f"  MAPQ       : {self.mapq}")
        logger.info(f"  Genome sz  : {self.genome_size}")
        logger.info(f"  Q-value    : {self.qvalue}")
        logger.info(f"  FDR alpha  : {self.alpha}")
        logger.info(f"  Output dir : {output_dir}")
        logger.info(f"  Start from : step {start_from}")
        logger.info("=" * 70)

        timing: Dict[str, float] = {}
        all_stats: Dict[str, Any] = {'sample_id': sample_id, 'start_from': start_from}

        prior = self._load_prior_steps(str(steps_dir))
        for key in ('filter_stats', 'map_stats', 'peak_stats', 'loop_stats'):
            if key in prior:
                all_stats[key] = prior[key]
        if 'timing' in prior:
            for step, secs in prior['timing'].items():
                if step != 'total':
                    timing[step] = secs

        if start_from <= 1:
            logger.info("\n[STEP 1] Linker filtering...")
            t0 = time.time()
            filt_r1, filt_r2, filter_stats = self._run_linker_filtering(
                fastq_r1, fastq_r2, str(filtered_dir), sample_id
            )
            timing['linker_filtering'] = time.time() - t0
            all_stats['filter_stats'] = filter_stats
            self._save_step_stats(
                str(steps_dir), 'filter_stats', filter_stats,
                timing_key='linker_filtering', seconds=timing['linker_filtering'],
            )
            logger.info(f"  Done in {_fmt_time(timing['linker_filtering'])}")
        else:
            logger.info("\n[STEP 1] SKIPPED (resume mode)")
            filt_r1 = os.path.join(str(filtered_dir), f"{sample_id}_filtered_R1.fastq")
            filt_r2 = os.path.join(str(filtered_dir), f"{sample_id}_filtered_R2.fastq")

        if start_from <= 2:
            logger.info("\n[STEP 2] Mapping (BWA + samtools + BEDPE)...")
            t0 = time.time()
            map_stats = self._run_mapping(
                filt_r1, filt_r2, str(mapped_dir), sample_id
            )
            timing['mapping'] = time.time() - t0
            all_stats['map_stats'] = map_stats
            self._save_step_stats(
                str(steps_dir), 'map_stats', map_stats,
                timing_key='mapping', seconds=timing['mapping'],
            )
            logger.info(f"  Done in {_fmt_time(timing['mapping'])}")

            dedup_bedpe = map_stats['final_bedpe']
            filtered_bam = map_stats['filtered_bam']
        else:
            logger.info("\n[STEP 2] SKIPPED (resume mode)")
            dedup_bedpe  = os.path.join(str(mapped_dir), f"{sample_id}.dedup.bedpe")
            filtered_bam = os.path.join(str(mapped_dir), f"{sample_id}.q{self.mapq}.bam")
            if not os.path.exists(dedup_bedpe):
                raise FileNotFoundError(
                    f"Cannot resume from step {start_from}: missing {dedup_bedpe}"
                )

        if start_from <= 3:
            logger.info("\n[STEP 3] Peak calling (MACS3)...")
            t0 = time.time()
            peak_stats = self._run_peak_calling(
                filtered_bam, str(peaks_dir), sample_id
            )
            timing['peak_calling'] = time.time() - t0
            all_stats['peak_stats'] = peak_stats
            self._save_step_stats(
                str(steps_dir), 'peak_stats', peak_stats,
                timing_key='peak_calling', seconds=timing['peak_calling'],
            )
            logger.info(f"  Done in {_fmt_time(timing['peak_calling'])}")
            peaks_file = peak_stats.get('peaks_file', '')
        else:
            logger.info("\n[STEP 3] SKIPPED (resume mode)")
            peaks_file = os.path.join(str(peaks_dir), f"{sample_id}_peaks.narrowPeak")
            if not os.path.exists(peaks_file):
                raise FileNotFoundError(
                    f"Cannot resume from step {start_from}: missing {peaks_file}"
                )
            if 'peak_stats' not in all_stats:
                all_stats['peak_stats'] = {
                    'peaks_file': peaks_file,
                    'resumed': True,
                }

        logger.info("\n[STEP 4] Background model & loop calling...")
        t0 = time.time()
        loop_stats = self._run_background_model(
            dedup_bedpe=dedup_bedpe,
            peaks_file=peaks_file,
            classified_dir=str(classified_dir),
            templates_dir=str(templates_dir),
            results_dir=str(results_dir),
            sample_id=sample_id,
        )
        timing['background_model'] = time.time() - t0
        all_stats['loop_stats'] = loop_stats
        self._save_step_stats(
            str(steps_dir), 'loop_stats', loop_stats,
            timing_key='background_model', seconds=timing['background_model'],
        )
        logger.info(f"  Done in {_fmt_time(timing['background_model'])}")

        timing['total'] = time.time() - pipeline_start
        all_stats['timing'] = timing
        self._write_qc_report(all_stats, str(qc_dir), sample_id)

        logger.info("\n" + "=" * 70)
        logger.info("ChIA-PET PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"  Total time : {_fmt_time(timing['total'])}")
        for step, secs in timing.items():
            if step != 'total':
                logger.info(f"  {step:<22}: {_fmt_time(secs)}")
        logger.info(f"  Results dir: {results_dir}")
        logger.info("=" * 70)

        return all_stats

    def _run_linker_filtering(
        self, r1: str, r2: str, out_dir: str, sample_id: str
    ):
        """Run parasail-based linker filtering."""
        from .linker_filtering import LinkerFilter
        import gzip
        import shutil

        filt = LinkerFilter(
            linker_sequences=self.linkers,
            n_threads=self.threads,
            min_alignment_score=self.min_score,
            min_tag_length=self.min_tag,
            max_tag_length=self.max_tag,
        )

        stats = filt.filter_fastq_parallel(
            fastq_r1=r1,
            fastq_r2=r2,
            output_prefix=sample_id,
            output_dir=out_dir,
        )

        n_linkers = len(self.linkers)
        linkers_are_rc = (
            n_linkers == 2 and
            stats.get('linkers_are_rc_pairs', False)
        )

        if linkers_are_rc:
            same_linker_cats = [(1, 2), (2, 1)]
        else:
            same_linker_cats = [(i, i) for i in range(1, n_linkers + 1)]

        merged_r1 = os.path.join(out_dir, f"{sample_id}_filtered_R1.fastq")
        merged_r2 = os.path.join(out_dir, f"{sample_id}_filtered_R2.fastq")

        with open(merged_r1, 'w') as out1, open(merged_r2, 'w') as out2:
            for i, j in same_linker_cats:
                cat_r1 = os.path.join(out_dir, f"{sample_id}.{i}_{j}.R1.fastq")
                cat_r2 = os.path.join(out_dir, f"{sample_id}.{i}_{j}.R2.fastq")
                for src, dst in [(cat_r1, out1), (cat_r2, out2)]:
                    if os.path.exists(src):
                        with open(src) as f:
                            shutil.copyfileobj(f, dst)

        stats['merged_r1'] = merged_r1
        stats['merged_r2'] = merged_r2

        return merged_r1, merged_r2, stats

    def _run_mapping(
        self, r1: str, r2: str, out_dir: str, sample_id: str
    ) -> Dict:
        """Run BWA mapping + MAPQ filter + BEDPE conversion + deduplication."""
        from .mapping import PETMapper

        mapper = PETMapper(
            genome_index=self.genome_index,
            mapping_quality_cutoff=self.mapq,
            n_threads=self.threads,
        )

        stats = mapper.map_paired_fastq(
            fastq_r1=r1,
            fastq_r2=r2,
            output_prefix=sample_id,
            output_dir=out_dir,
            keep_bam=True,
            remove_duplicates=True,
        )

        stats['filtered_bam'] = os.path.join(out_dir, f"{sample_id}.q{self.mapq}.bam")
        stats['final_bedpe']   = os.path.join(out_dir, f"{sample_id}.dedup.bedpe")

        return stats

    def _run_peak_calling(
        self, bam_file: str, out_dir: str, sample_id: str
    ) -> Dict:
        """Call peaks with MACS3 from the filtered BAM."""
        from .peak_calling import PeakCaller

        caller = PeakCaller(
            genome_size=self.genome_size,
            qvalue_cutoff=self.qvalue,
        )

        output_prefix = os.path.join(out_dir, sample_id)
        stats = caller.call_peaks_from_bam(bam_file, output_prefix)
        return stats

    def _run_background_model(
        self,
        dedup_bedpe: str,
        peaks_file: str,
        classified_dir: str,
        templates_dir: str,
        results_dir: str,
        sample_id: str,
    ) -> Dict:
        """
        Run all five background-model steps:
          4a. classify_pets + export_by_category → P2P / P2D / D2D files
          4b. extract_templates → templates.csv
          4c. BackgroundSamplingPhase1 → NB parameters
          4d. calculate_pvalues → p-values
          4e. apply_fdr_corrections → significant loops CSV
        """
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

        stats = {}

        if not peaks_file or not os.path.exists(peaks_file):
            logger.warning("  No peaks file found — skipping background model")
            return {'skipped': True, 'reason': 'no peaks file'}

        peaks_by_chr, peak_ids_by_chr, peaks_df = load_peaks(
            peaks_file,
            standard_chroms_only=self.standard_chroms_only,
            cytoband_file=self.cytoband_file,
        )

        pets_df = classify_pets(
            bedpe_file=dedup_bedpe,
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

        templates_csv = os.path.join(templates_dir, f"{sample_id}_templates.csv")

        extract_templates(
            p2p_file=p2p_file,
            peak_file=peaks_file,
            output_file=templates_csv,
            standard_chroms_only=self.standard_chroms_only,
            cytoband_file=self.cytoband_file,
        )
        stats['templates_csv'] = templates_csv

        templates_nb_csv = os.path.join(templates_dir, f"{sample_id}_templates_with_nb.csv")

        sampler = BackgroundSamplingPhase1(
            n_cores=self.threads,
        )
        sampler.load_d2d_pets(d2d_file)
        sampler.process_templates(
            templates_file=templates_csv,
            output_file=templates_nb_csv,
        )
        stats['templates_nb_csv'] = templates_nb_csv

        pvalues_csv = os.path.join(templates_dir, f"{sample_id}_templates_with_pvalues.csv")

        calculate_pvalues(
            templates_file=templates_nb_csv,
            output_file=pvalues_csv,
        )
        stats['pvalues_csv'] = pvalues_csv

        loops_csv = os.path.join(results_dir, f"{sample_id}_significant_loops.csv")

        apply_fdr_corrections(
            input_file=pvalues_csv,
            output_file=loops_csv,
            alpha=self.alpha,
        )
        stats['loops_csv'] = loops_csv
        logger.info(f"    Loops output: {loops_csv}")

        return stats

    def _save_step_stats(
        self,
        steps_dir: str,
        key: str,
        stats: Any,
        timing_key: Optional[str] = None,
        seconds: Optional[float] = None,
    ) -> None:
        """Persist a single step's stats (+ its timing) as JSON for resume."""
        try:
            path = os.path.join(steps_dir, f"{key}.json")
            payload = {
                key: stats,
                'timing_key': timing_key,
                'seconds': seconds,
            }
            with open(path, 'w') as fh:
                json.dump(payload, fh, default=_json_default, indent=2)
        except Exception as exc:
            logger.warning(f"  Could not persist {key} to {steps_dir}: {exc}")

    def _load_prior_steps(self, steps_dir: str) -> Dict[str, Any]:
        """Load any previously-saved step JSONs back into a stats dict."""
        out: Dict[str, Any] = {'timing': {}}
        if not os.path.isdir(steps_dir):
            return out
        for fname in os.listdir(steps_dir):
            if not fname.endswith('.json'):
                continue
            path = os.path.join(steps_dir, fname)
            try:
                with open(path) as fh:
                    payload = json.load(fh)
            except Exception as exc:
                logger.warning(f"  Ignoring unreadable step file {path}: {exc}")
                continue
            key = fname[:-len('.json')]
            if isinstance(payload, dict) and key in payload:
                out[key] = payload[key]
                tkey = payload.get('timing_key')
                secs = payload.get('seconds')
                if tkey and isinstance(secs, (int, float)):
                    out['timing'][tkey] = float(secs)
            else:
                out[key] = payload
        return out

    def _write_qc_report(self, all_stats: Dict, qc_dir: str, sample_id: str):
        """Write a plain-text QC / timing summary and a JSON companion."""
        report_path = os.path.join(qc_dir, f"{sample_id}_pipeline_summary.txt")
        json_path   = os.path.join(qc_dir, f"{sample_id}_pipeline_summary.json")
        timing = all_stats.get('timing', {}) or {}
        filter_stats = all_stats.get('filter_stats', {}) or {}
        map_stats    = all_stats.get('map_stats', {}) or {}
        peak_stats   = all_stats.get('peak_stats', {}) or {}
        loop_stats   = all_stats.get('loop_stats', {}) or {}

        raw_map   = map_stats.get('raw', {}) or {}
        bedpe_map = map_stats.get('bedpe', {}) or {}
        classify  = loop_stats.get('classify', {}) or {}

        total_reads_lf = filter_stats.get('total_reads', filter_stats.get('total_pairs'))
        valid_pets_lf  = filter_stats.get('valid_pets',  filter_stats.get('passing_pairs'))

        total_reads_map    = raw_map.get('total_reads')
        mapped_reads       = raw_map.get('mapped_reads')
        properly_paired    = raw_map.get('properly_paired')
        valid_pairs_bedpe  = bedpe_map.get('valid_pairs')
        duplicates_removed = map_stats.get('duplicates_removed')

        num_peaks  = peak_stats.get('num_peaks')
        peaks_file = peak_stats.get('peaks_file', 'N/A')

        p2p = classify.get('P2P', classify.get('p2p_count'))
        p2d = classify.get('P2D', classify.get('p2d_count'))
        d2d = classify.get('D2D', classify.get('d2d_count'))

        templates_csv = loop_stats.get('templates_csv', 'N/A')
        loops_csv     = loop_stats.get('loops_csv', 'N/A')

        summary = {
            'sample_id': sample_id,
            'linker_filtering': {
                'total_reads':        total_reads_lf,
                'valid_pets':         valid_pets_lf,
                'pass_rate_pct':      None if (total_reads_lf in (None, 0) or valid_pets_lf is None)
                                        else round(100.0 * valid_pets_lf / total_reads_lf, 4),
                'same_linker_pets':   filter_stats.get('same_linker_pets'),
                'diff_linker_pets':   filter_stats.get('diff_linker_pets'),
            },
            'mapping': {
                'total_reads':        total_reads_map,
                'mapped_reads':       mapped_reads,
                'properly_paired':    properly_paired,
                'valid_pairs_bedpe':  valid_pairs_bedpe,
                'duplicates_removed': duplicates_removed,
            },
            'peak_calling': {
                'num_peaks':  num_peaks,
                'peaks_file': peaks_file,
            },
            'loop_calling': {
                'p2p_pets':      p2p,
                'p2d_pets':      p2d,
                'd2d_pets':      d2d,
                'templates_csv': templates_csv,
                'loops_csv':     loops_csv,
            },
            'timing_seconds': {k: float(v) for k, v in timing.items()},
            'raw_stats': {
                'filter_stats': filter_stats,
                'map_stats':    map_stats,
                'peak_stats':   peak_stats,
                'loop_stats':   loop_stats,
            },
        }

        lines = [
            "=" * 70,
            f"ChIA-PET PIPELINE SUMMARY  —  {sample_id}",
            "=" * 70,
            "",
            "--- Linker Filtering ---",
            f"  Total read pairs   : {_fmt_int(total_reads_lf)}",
            f"  Passing pairs      : {_fmt_int(valid_pets_lf)}",
            f"  Passing rate       : {_fmt_pct(valid_pets_lf, total_reads_lf)}",
            "",
            "--- Mapping ---",
            f"  Total reads        : {_fmt_int(total_reads_map)}",
            f"  Mapped reads       : {_fmt_int(mapped_reads)}",
            f"  Properly paired    : {_fmt_int(properly_paired)}",
            f"  Valid pairs (BEDPE): {_fmt_int(valid_pairs_bedpe)}",
            f"  Duplicates removed : {_fmt_int(duplicates_removed)}",
            "",
            "--- Peak Calling ---",
            f"  Peaks called       : {_fmt_int(num_peaks)}",
            f"  Peaks file         : {peaks_file}",
            "",
            "--- Loop Calling ---",
            f"  P2P PETs           : {_fmt_int(p2p)}",
            f"  P2D PETs           : {_fmt_int(p2d)}",
            f"  D2D PETs           : {_fmt_int(d2d)}",
            f"  Templates          : {templates_csv}",
            f"  Loops (FDR)        : {loops_csv}",
            "",
            "--- Timing ---",
        ]
        for step, secs in timing.items():
            if step != 'total':
                lines.append(f"  {step:<22}: {_fmt_time(secs)}")
        lines.append(f"  {'Total':<22}: {_fmt_time(timing.get('total', 0))}")
        lines.append("=" * 70)

        with open(report_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

        with open(json_path, 'w') as f:
            json.dump(summary, f, default=_json_default, indent=2)

        logger.info(f"  QC report saved to: {report_path}")
        logger.info(f"  QC JSON  saved to : {json_path}")
