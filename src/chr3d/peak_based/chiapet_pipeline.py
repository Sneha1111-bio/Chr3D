"""
ChIA-PET Pipeline Orchestrator

Runs the full ChIA-PET analysis pipeline end-to-end:
  1. Linker filtering   (LinkerFilter / parasail SIMD)
  2. Mapping            (PETMapperV3 / BWA)
  3. Peak calling       (PeakCaller / MACS3)
  4. Background model   (classify → extract → phase1 → phase2 → FDR)

Output layout:
  <output-dir>/
  ├── filtered/       linker-filtered FASTQ files + stats
  ├── mapped/         BAM, BEDPE, dedup BEDPE + flagstat
  ├── peaks/          MACS3 broadPeak / narrowPeak + summits
  ├── loops/
  │   ├── classified/ P2P / P2D / D2D PET files
  │   ├── templates/  templates.csv, templates_with_nb.csv
  │   └── results/    p-values CSV, FDR-corrected loops CSV
  └── qc/             per-step stats + timing report
"""

import os
import time
from pathlib import Path
from typing import Dict, Optional

from ..utils.logging import get_logger

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


class ChiaPetPipeline:
    """
    End-to-end ChIA-PET pipeline orchestrator.

    Parameters
    ----------
    genome_index : str
        Path to BWA-indexed genome FASTA.
    linkers : list[str]
        One or more linker sequences to filter against.
    threads : int
        CPU threads for BWA / samtools / linker filtering.
    mapq : int
        Minimum mapping quality for BAM filtering (default 30).
    genome_size : str
        MACS3 genome size string ('hs', 'mm', or integer; default 'hs').
    qvalue : float
        MACS3 q-value cutoff (default 0.05).
    alpha : float
        FDR significance threshold (default 0.05).
    min_score : int
        Minimum parasail alignment score for linker matching (default 20).
    min_tag : int
        Minimum tag length after linker removal (default 15).
    max_tag : int
        Maximum tag length after linker removal (default 40).
    standard_chroms_only : bool
        Restrict loop calling to chr1-22 + chrX/Y (default True).
    cytoband_file : str, optional
        Path to UCSC cytoband file for centromere exclusion.
    keep_intermediates : bool
        Keep intermediate BAM files (default False).
    """

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

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_dir: str,
        sample_id: str = 'sample',
    ) -> Dict:
        """
        Run the full ChIA-PET pipeline.

        Parameters
        ----------
        fastq_r1 : str
            Path to R1 FASTQ (gzipped or plain).
        fastq_r2 : str
            Path to R2 FASTQ (gzipped or plain).
        output_dir : str
            Root output directory (created if absent).
        sample_id : str
            Sample name used as file prefix.

        Returns
        -------
        dict
            Collected stats from every pipeline step + timing breakdown.
        """
        pipeline_start = time.time()

        out = Path(output_dir)
        filtered_dir  = out / 'filtered'
        mapped_dir    = out / 'mapped'
        peaks_dir     = out / 'peaks'
        loops_dir     = out / 'loops'
        classified_dir = loops_dir / 'classified'
        templates_dir  = loops_dir / 'templates'
        results_dir    = loops_dir / 'results'
        qc_dir         = out / 'qc'

        for d in [filtered_dir, mapped_dir, peaks_dir,
                  classified_dir, templates_dir, results_dir, qc_dir]:
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
        logger.info("=" * 70)

        timing = {}
        all_stats = {'sample_id': sample_id}

        # ------------------------------------------------------------------
        # Step 1: Linker filtering
        # ------------------------------------------------------------------
        logger.info("\n[STEP 1] Linker filtering...")
        t0 = time.time()
        filt_r1, filt_r2, filter_stats = self._run_linker_filtering(
            fastq_r1, fastq_r2, str(filtered_dir), sample_id
        )
        timing['linker_filtering'] = time.time() - t0
        all_stats['filter_stats'] = filter_stats
        logger.info(f"  Done in {_fmt_time(timing['linker_filtering'])}")

        # ------------------------------------------------------------------
        # Step 2: Mapping
        # ------------------------------------------------------------------
        logger.info("\n[STEP 2] Mapping (BWA + samtools + BEDPE)...")
        t0 = time.time()
        map_stats = self._run_mapping(
            filt_r1, filt_r2, str(mapped_dir), sample_id
        )
        timing['mapping'] = time.time() - t0
        all_stats['map_stats'] = map_stats
        logger.info(f"  Done in {_fmt_time(timing['mapping'])}")

        dedup_bedpe = map_stats['final_bedpe']
        filtered_bam = map_stats['filtered_bam']

        # ------------------------------------------------------------------
        # Step 3: Peak calling (MACS3 on filtered BAM)
        # ------------------------------------------------------------------
        logger.info("\n[STEP 3] Peak calling (MACS3)...")
        t0 = time.time()
        peak_stats = self._run_peak_calling(
            filtered_bam, str(peaks_dir), sample_id
        )
        timing['peak_calling'] = time.time() - t0
        all_stats['peak_stats'] = peak_stats
        logger.info(f"  Done in {_fmt_time(timing['peak_calling'])}")

        peaks_file = peak_stats.get('peaks_file', '')

        # ------------------------------------------------------------------
        # Step 4: Background model  (classify → extract → phase1 → phase2 → FDR)
        # ------------------------------------------------------------------
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
        logger.info(f"  Done in {_fmt_time(timing['background_model'])}")

        # ------------------------------------------------------------------
        # Write QC / timing report
        # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    def _run_linker_filtering(
        self, r1: str, r2: str, out_dir: str, sample_id: str
    ):
        """
        Run parasail-based linker filtering (LinkerFilterV3).

        filter_fastq_parallel produces per-category FASTQ files named
        ``{prefix}.{i}_{j}.R1.fastq``.  For single-linker ChIA-PET the
        useful category is ``1_1`` (same-linker).  We merge all same-linker
        categories into a single pair of files for the mapping step.
        """
        from .linker_filtering import LinkerFilterV3
        import gzip
        import shutil

        filt = LinkerFilterV3(
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

        # Determine which output categories to merge for mapping.
        # Category files: {prefix}.{i}_{j}.R1.fastq
        #
        # If the two linkers are RC pairs (e.g. A & RC(A)), then:
        #   1_2 and 2_1 are the real "same-linker" PETs (A on one end, RC(A) on other)
        #   1_1 and 2_2 would be same-strand duplicates — typically empty
        # Otherwise (truly distinct linkers):
        #   1_1 and 2_2 are same-linker
        n_linkers = len(self.linkers)
        linkers_are_rc = (
            n_linkers == 2 and
            stats.get('linkers_are_rc_pairs', False)
        )

        if linkers_are_rc:
            # 1_2 + 2_1: the useful RC-pair categories
            same_linker_cats = [(1, 2), (2, 1)]
        else:
            # i_i: homo-linker categories
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
        from .mapping import PETMapperV3

        mapper = PETMapperV3(
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

        # Surface key output paths for later steps
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

        # --- 4a: Classify PETs ---
        logger.info("  [4a] Classifying PETs (P2P / P2D / D2D)...")
        if not peaks_file or not os.path.exists(peaks_file):
            logger.warning("  No peaks file found — skipping background model")
            return {'skipped': True, 'reason': 'no peaks file'}

        # load_peaks returns (peaks_by_chr, peak_ids_by_chr, peaks_df)
        peaks_by_chr, peak_ids_by_chr, peaks_df = load_peaks(
            peaks_file,
            standard_chroms_only=self.standard_chroms_only,
            cytoband_file=self.cytoband_file,
        )

        # classify_pets returns a DataFrame with 'category' column
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

        # export_by_category writes {prefix}.P2P_pets.txt, .P2D_pets.txt, .D2D_pets.txt
        classify_prefix = os.path.join(classified_dir, sample_id)
        export_by_category(pets_df, classify_prefix)

        p2p_file = f"{classify_prefix}.P2P_pets.txt"
        d2d_file = f"{classify_prefix}.D2D_pets.txt"

        # --- 4b: Extract templates ---
        logger.info("  [4b] Extracting templates from P2P PETs...")
        templates_csv = os.path.join(templates_dir, f"{sample_id}_templates.csv")

        extract_templates(
            p2p_file=p2p_file,
            peak_file=peaks_file,
            output_file=templates_csv,
            standard_chroms_only=self.standard_chroms_only,
            cytoband_file=self.cytoband_file,
        )
        stats['templates_csv'] = templates_csv

        # --- 4c: Background sampling phase 1 (NB fitting) ---
        logger.info("  [4c] Background sampling phase 1 (NB parameter estimation)...")
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

        # --- 4d: Background sampling phase 2 (p-values) ---
        logger.info("  [4d] Calculating p-values (PMF / NB)...")
        pvalues_csv = os.path.join(templates_dir, f"{sample_id}_templates_with_pvalues.csv")

        calculate_pvalues(
            templates_file=templates_nb_csv,
            output_file=pvalues_csv,
        )
        stats['pvalues_csv'] = pvalues_csv

        # --- 4e: FDR correction ---
        logger.info("  [4e] Applying FDR correction...")
        loops_csv = os.path.join(results_dir, f"{sample_id}_significant_loops.csv")

        apply_fdr_corrections(
            input_file=pvalues_csv,
            output_file=loops_csv,
            alpha=self.alpha,
        )
        stats['loops_csv'] = loops_csv
        logger.info(f"    Loops output: {loops_csv}")

        return stats

    # ------------------------------------------------------------------
    # QC report
    # ------------------------------------------------------------------

    def _write_qc_report(self, all_stats: Dict, qc_dir: str, sample_id: str):
        """Write a plain-text QC / timing summary."""
        report_path = os.path.join(qc_dir, f"{sample_id}_pipeline_summary.txt")
        timing = all_stats.get('timing', {})
        filter_stats = all_stats.get('filter_stats', {})
        map_stats    = all_stats.get('map_stats', {})
        peak_stats   = all_stats.get('peak_stats', {})
        loop_stats   = all_stats.get('loop_stats', {})

        lines = [
            "=" * 70,
            f"ChIA-PET PIPELINE SUMMARY  —  {sample_id}",
            "=" * 70,
            "",
            "--- Linker Filtering ---",
            f"  Total read pairs   : {filter_stats.get('total_pairs', 'N/A'):,}" if isinstance(filter_stats.get('total_pairs'), int) else f"  Total read pairs   : {filter_stats.get('total_pairs', 'N/A')}",
            f"  Passing pairs      : {filter_stats.get('passing_pairs', 'N/A')}",
            f"  Passing rate       : {filter_stats.get('pass_rate', 'N/A')}",
            "",
            "--- Mapping ---",
            f"  Total reads        : {map_stats.get('raw', {}).get('total_reads', 'N/A')}",
            f"  Mapped reads       : {map_stats.get('raw', {}).get('mapped_reads', 'N/A')}",
            f"  Properly paired    : {map_stats.get('raw', {}).get('properly_paired', 'N/A')}",
            f"  Valid pairs (BEDPE): {map_stats.get('bedpe', {}).get('valid_pairs', 'N/A')}",
            f"  Duplicates removed : {map_stats.get('duplicates_removed', 'N/A')}",
            "",
            "--- Peak Calling ---",
            f"  Peaks called       : {peak_stats.get('num_peaks', 'N/A')}",
            f"  Peaks file         : {peak_stats.get('peaks_file', 'N/A')}",
            "",
            "--- Loop Calling ---",
            f"  P2P PETs           : {loop_stats.get('classify', {}).get('p2p_count', 'N/A')}",
            f"  D2D PETs           : {loop_stats.get('classify', {}).get('d2d_count', 'N/A')}",
            f"  Templates          : {loop_stats.get('templates_csv', 'N/A')}",
            f"  Loops (FDR)        : {loop_stats.get('loops_csv', 'N/A')}",
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

        logger.info(f"  QC report saved to: {report_path}")
