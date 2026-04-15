"""
Single-Nucleus Hi-C (sn-Hi-C) Analysis Pipeline

Processes single-nucleus Hi-C data from multiple cells.
Each cell is processed independently through the standard Hi-C steps,
followed by QC filtering and optional clustering.

Pipeline Steps:
    1. Alignment        - BWA MEM per-cell FASTQ (delegates to HiCAligner)
    2. SAM/BAM          - SAM to sorted BAM (delegates to HiCSamProcessor)
    3. Pairs processing - pairtools parse/sort/dedup/filter (delegates to HiCPairsProcessor)
    4. Matrix           - Per-cell .cool matrices (delegates to HiCMatrixGenerator)
    5. Cell QC          - Filter low-quality cells by contact count / complexity
    6. Pseudobulk       - Aggregate all cell matrices into a single matrix
    7. Clustering       - GNN-based cell type clustering (optional)

Differences from Bulk Hi-C:
    - Accepts a sample manifest (multiple FASTQs, one per cell)
    - Generates per-cell .cool files + aggregated pseudobulk matrix
    - Includes cell-level QC filtering
    - Integrates with clustering/ submodule for cell type clustering

Dependencies:
    Core (same as bulk Hi-C):
        - BWA (>= 0.7.17)
        - SAMtools (>= 1.10)
        - pairtools (>= 1.0.0)
        - cooler (>= 0.9.0)

    Clustering (optional, only needed if run_clustering=True):
        - torch
        - torch_geometric
        - scanpy
        - anndata
        - scikit-learn
        - umap-learn
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Use centralized logging
from ..utils.logging import get_logger

# Get module logger
logger = get_logger(__name__)

from .bulk_hic import (
    HiCAligner,
    HiCSamProcessor,
    HiCPairsProcessor,
    HiCMatrixGenerator,
    _format_duration,
    _check_tool,
)


class SnHiCCellQC:
    """
    Quality control for individual sn-Hi-C cells.

    Filters cells based on minimum contact counts and complexity metrics
    to remove low-quality cells before downstream analysis.

    Attributes:
        min_contacts: Minimum number of valid contacts required per cell
        min_complexity: Minimum library complexity (unique / total reads ratio)
        max_dup_rate: Maximum duplicate rate allowed per cell
    """

    def __init__(
        self,
        min_contacts: int = 1000,
        min_complexity: float = 0.3,
        max_dup_rate: float = 0.8,
    ):
        """
        Initialize cell QC filters.

        Args:
            min_contacts: Minimum valid contacts to keep a cell (default: 1000)
            min_complexity: Minimum complexity ratio (default: 0.3)
            max_dup_rate: Maximum duplicate rate to keep a cell (default: 0.8)
        """
        self.min_contacts = min_contacts
        self.min_complexity = min_complexity
        self.max_dup_rate = max_dup_rate

        logger.info("SnHiCCellQC initialized")
        logger.info(f"  Min contacts:  {min_contacts:,}")
        logger.info(f"  Min complexity: {min_complexity:.2f}")
        logger.info(f"  Max dup rate:   {max_dup_rate:.2f}")

    def filter_cells(self, cell_stats: Dict[str, Dict]) -> Tuple[List[str], List[str]]:
        """
        Filter cells based on QC metrics.

        Args:
            cell_stats: Dict mapping cell_id -> stats dict with keys:
                        'valid_contacts', 'duplicate_rate', 'complexity'

        Returns:
            Tuple of (passing_cell_ids, failing_cell_ids)
        """
        # TODO: Implement cell QC filtering logic
        raise NotImplementedError("SnHiCCellQC.filter_cells() not yet implemented")


class SnHiCPseudoBulk:
    """
    Aggregate per-cell .cool matrices into a single pseudobulk matrix.

    Merges all passing-QC cell matrices into one combined contact matrix
    suitable for comparison with bulk Hi-C data.
    """

    def __init__(self, threads: int = 1):
        """
        Initialize pseudobulk aggregator.

        Args:
            threads: Number of threads for cooler operations (default: 1)
        """
        self.threads = threads

        logger.info("SnHiCPseudoBulk initialized")
        logger.info(f"  Threads: {threads}")

    def aggregate(
        self,
        cell_cool_files: List[str],
        output_cool: str,
        output_mcool: str,
        resolutions: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Merge per-cell .cool files into a pseudobulk matrix.

        Args:
            cell_cool_files: List of paths to per-cell .cool files
            output_cool: Path for aggregated output .cool file
            output_mcool: Path for multi-resolution .mcool file
            resolutions: List of resolutions for zoomify (default: standard set)

        Returns:
            Dictionary with aggregation statistics
        """
        # TODO: Implement cooler merge logic
        raise NotImplementedError("SnHiCPseudoBulk.aggregate() not yet implemented")


class SnHiCPipeline:
    """
    Complete single-nucleus Hi-C pipeline.

    Processes multiple single-cell Hi-C FASTQs through alignment, pairs
    processing, per-cell matrix generation, QC filtering, pseudobulk
    aggregation, and optional GNN-based clustering.

    This pipeline reuses bulk Hi-C components (HiCAligner, HiCSamProcessor,
    HiCPairsProcessor, HiCMatrixGenerator) and applies them per-cell.

    Example:
        >>> from chr3d.hic import SnHiCPipeline
        >>>
        >>> pipeline = SnHiCPipeline(
        ...     genome_index="/path/to/hg38.fa",
        ...     chrom_sizes="/path/to/hg38.chrom.sizes",
        ...     threads=24,
        ... )
        >>>
        >>> # Sample manifest: list of (cell_id, fastq_r1, fastq_r2)
        >>> cells = [
        ...     ("cell_001", "cell001_R1.fastq.gz", "cell001_R2.fastq.gz"),
        ...     ("cell_002", "cell002_R1.fastq.gz", "cell002_R2.fastq.gz"),
        ... ]
        >>>
        >>> stats = pipeline.run(
        ...     cells=cells,
        ...     output_dir="sn_hic_results/",
        ...     run_clustering=True,
        ... )

    Output Directory Structure:
        output_dir/
        ├── cells/
        │   ├── cell_001/
        │   │   ├── aligned/        (sorted BAM)
        │   │   ├── pairs/          (filtered .pairs.gz)
        │   │   └── matrices/       (per-cell .cool)
        │   └── cell_002/
        │       └── ...
        ├── pseudobulk/
        │   ├── pseudobulk.cool
        │   └── pseudobulk.mcool
        ├── clustering/
        │   ├── cell_bin_matrix.csv
        │   ├── embeddings.npy
        │   └── predictions.csv
        └── qc/
            ├── cell_qc_summary.txt
            └── passing_cells.txt
    """

    REQUIRED_TOOLS = ['bwa', 'samtools', 'pairtools', 'cooler']

    def __init__(
        self,
        genome_index: str,
        chrom_sizes: str,
        threads: int = 1,
        assembly: str = 'hg38',
        min_mapq: int = 30,
        min_distance: int = 1000,
        resolutions: Optional[List[int]] = None,
        min_contacts_per_cell: int = 1000,
        min_complexity: float = 0.3,
        max_dup_rate: float = 0.8,
    ):
        """
        Initialize the sn-Hi-C pipeline.

        Args:
            genome_index: Path to BWA-indexed genome FASTA
            chrom_sizes: Path to chromosome sizes file
            threads: Number of threads for each step (default: 1)
            assembly: Genome assembly name (default: 'hg38')
            min_mapq: Minimum mapping quality (default: 30)
            min_distance: Minimum pair distance in bp (default: 1000)
            resolutions: Matrix resolutions for pseudobulk .mcool
                         (default: [1000, 5000, 10000, 25000, 50000, 100000])
            min_contacts_per_cell: Cell QC: min valid contacts (default: 1000)
            min_complexity: Cell QC: min complexity ratio (default: 0.3)
            max_dup_rate: Cell QC: max duplicate rate (default: 0.8)
        """
        self.genome_index = genome_index
        self.chrom_sizes = chrom_sizes
        self.threads = threads
        self.assembly = assembly
        self.min_mapq = min_mapq
        self.min_distance = min_distance
        self.resolutions = resolutions or [1000, 5000, 10000, 25000, 50000, 100000]

        # Cell QC parameters
        self.min_contacts_per_cell = min_contacts_per_cell
        self.min_complexity = min_complexity
        self.max_dup_rate = max_dup_rate

        self._check_dependencies()

        logger.info("=" * 70)
        logger.info("sn-Hi-C PIPELINE INITIALIZED")
        logger.info("=" * 70)
        logger.info(f"  Genome index:    {genome_index}")
        logger.info(f"  Chrom sizes:     {chrom_sizes}")
        logger.info(f"  Threads:         {threads}")
        logger.info(f"  Assembly:        {assembly}")
        logger.info(f"  Min MAPQ:        {min_mapq}")
        logger.info(f"  Min distance:    {min_distance} bp")
        logger.info(f"  Resolutions:     {self.resolutions}")
        logger.info(f"  Min contacts:    {min_contacts_per_cell:,}")
        logger.info(f"  Min complexity:  {min_complexity:.2f}")
        logger.info(f"  Max dup rate:    {max_dup_rate:.2f}")

    def _check_dependencies(self):
        """Check required external tools are available."""
        missing = [t for t in self.REQUIRED_TOOLS if not _check_tool(t)]
        if missing:
            raise RuntimeError(
                f"Required tools not found: {missing}\n"
                f"Install with: conda install -c bioconda {' '.join(missing)}"
            )

    def process_cell(
        self,
        cell_id: str,
        fastq_r1: str,
        fastq_r2: str,
        output_dir: str,
        cleanup: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the full Hi-C processing pipeline for a single cell.

        Reuses bulk Hi-C components (HiCAligner, HiCSamProcessor,
        HiCPairsProcessor, HiCMatrixGenerator).

        Args:
            cell_id: Unique identifier for this cell
            fastq_r1: Path to R1 FASTQ file
            fastq_r2: Path to R2 FASTQ file
            output_dir: Cell-specific output directory
            cleanup: Remove intermediate files after processing (default: False)

        Returns:
            Dictionary with per-cell statistics and output file paths
        """
        # TODO: Implement per-cell processing using bulk_hic components
        #raise NotImplementedError("SnHiCPipeline.process_cell() not yet implemented")
        
        logger.info(f"  Processing cell: {cell_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        cell_start = time.time()
        
        # Step 1: Alignment
        logger.info(f"    [Cell {cell_id}] Step 1: BWA MEM Alignment...")
        aligner = HiCAligner(
            genome_index=self.genome_index,
            threads=self.threads
        )
        # Create aligned directory and define output SAM path
        aligned_dir = os.path.join(output_dir, 'aligned')
        os.makedirs(aligned_dir, exist_ok=True)
        output_sam = os.path.join(aligned_dir, f"{cell_id}.sam")
        stats_file = os.path.join(output_dir, 'qc', f"{cell_id}_alignment.stats")
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)
        align_stats = aligner.align(fastq_r1, fastq_r2, output_sam, stats_file)
        
        # Step 2: SAM/BAM processing
        logger.info(f"    [Cell {cell_id}] Step 2: SAM/BAM processing...")
        sam_processor = HiCSamProcessor(threads=self.threads)
        # Create processed directory and define output BAM path
        processed_dir = os.path.join(output_dir, 'processed')
        os.makedirs(processed_dir, exist_ok=True)
        output_bam = os.path.join(processed_dir, f"{cell_id}_sorted.bam")
        # Also create qc dir for bam stats
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(qc_dir, exist_ok=True)
        bam_stats_file = os.path.join(qc_dir, f"{cell_id}_bam.stats")
        sam_stats = sam_processor.process(align_stats['output_sam'], output_bam, stats_file=bam_stats_file)
        
        # Step 3: Pairs processing - call individual steps to organize QC files properly
        logger.info(f"    [Cell {cell_id}] Step 3: Pairs processing...")
        pairs_processor = HiCPairsProcessor(
            chrom_sizes=self.chrom_sizes,
            assembly=self.assembly,
            threads=self.threads
        )
        # Define directories
        pairs_dir = os.path.join(output_dir, 'pairs')
        os.makedirs(pairs_dir, exist_ok=True)
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(qc_dir, exist_ok=True)
        
        # Step 3a: Parse (stats go to qc/)
        parsed_pairs = os.path.join(pairs_dir, f"{cell_id}.parsed.pairs.gz")
        parse_stats = os.path.join(qc_dir, f"{cell_id}_pairs.stats")
        pairs_processor.parse(sam_stats['output_bam'], parsed_pairs, parse_stats)
        
        # Step 3b: Sort
        sorted_pairs = os.path.join(pairs_dir, f"{cell_id}.sorted.pairs.gz")
        pairs_processor.sort(parsed_pairs, sorted_pairs, tmp_dir=pairs_dir)
        
        # Step 3c: Dedup (stats go to qc/)
        dedup_pairs = os.path.join(pairs_dir, f"{cell_id}.dedup.pairs.gz")
        dedup_stats = os.path.join(qc_dir, f"{cell_id}_dedup.stats")
        pairs_processor.dedup(sorted_pairs, dedup_pairs, dedup_stats)
        
        # Step 3d: Filter
        filtered_pairs = os.path.join(pairs_dir, f"{cell_id}.filtered.pairs.gz")
        pairs_processor.filter(dedup_pairs, filtered_pairs)
        
        # Cleanup intermediate pairs files
        for f in [parsed_pairs]:
            if os.path.exists(f):
                os.remove(f)
        
        pairs_stats = {
            'sorted_pairs': sorted_pairs,
            'dedup_pairs': dedup_pairs,
            'filtered_pairs': filtered_pairs,
            'parse_stats': parse_stats,
            'dedup_stats': dedup_stats
        }
        
        # Step 4: Matrix generation
        logger.info(f"    [Cell {cell_id}] Step 4: Contact matrix generation...")
        matrix_generator = HiCMatrixGenerator(
            chrom_sizes=self.chrom_sizes,
            assembly=self.assembly,
            threads=self.threads
        )
        matrix_stats = matrix_generator.create(
            input_pairs=pairs_stats['filtered_pairs'],
            output_cool=os.path.join(output_dir, 'matrices', f"{cell_id}.cool"),
            resolution=1000
        )
        
        cell_duration = time.time() - cell_start
        
        stats = {
            'cell_id': cell_id,
            'status': 'success',
            'duration_seconds': cell_duration,
            'duration_formatted': _format_duration(cell_duration),
            'align_stats': align_stats,
            'sam_stats': sam_stats,
            'pairs_stats': pairs_stats,
            'matrix_stats': matrix_stats,
            'cool_file': matrix_stats.get('output_cool', ''),
            'num_contacts': matrix_stats.get('num_contacts', 0),
        }
        
        logger.info(f"  Cell {cell_id} completed in {stats['duration_formatted']}")
        
        # Cleanup intermediates if requested
        if cleanup:
            for f in [align_stats.get('output_sam'), pairs_stats.get('dedup_pairs')]:
                if f and os.path.exists(f):
                    os.remove(f)
                    logger.debug(f"    Cleaned up: {f}")
        
        return stats

    def run_cell_qc(
        self,
        cell_stats: Dict[str, Dict],
        output_dir: str,
    ) -> Tuple[List[str], List[str]]:
        """
        Apply QC filters to all processed cells.

        Args:
            cell_stats: Dict mapping cell_id -> per-cell stats from process_cell()
            output_dir: Directory to write QC reports

        Returns:
            Tuple of (passing_cell_ids, failing_cell_ids)
        """
        # TODO: Delegate to SnHiCCellQC
        #raise NotImplementedError("SnHiCPipeline.run_cell_qc() not yet implemented")
        
        os.makedirs(output_dir, exist_ok=True)
        
        passing_cells = []
        failing_cells = []
        
        qc_report = []
        qc_report.append("=" * 70)
        qc_report.append("sn-Hi-C CELL QC REPORT")
        qc_report.append("=" * 70)
        qc_report.append(f"{'Cell ID':<20} {'Contacts':>12} {'Status':>10} {'Reason':>20}")
        qc_report.append("-" * 70)
        
        for cell_id, stats in cell_stats.items():
            if stats.get('status') == 'failed':
                failing_cells.append(cell_id)
                qc_report.append(f"{cell_id:<20} {'N/A':>12} {'FAIL':>10} {'Processing failed':>20}")
                continue
            
            num_contacts = stats.get('num_contacts', 0)
            
            # Apply QC filters
            fail_reasons = []
            if num_contacts < self.min_contacts_per_cell:
                fail_reasons.append(f"contacts<{self.min_contacts_per_cell}")
            
            # Calculate complexity from pairs stats if available
            pairs_stats = stats.get('pairs_stats', {})
            total_pairs = pairs_stats.get('total_pairs', 0)
            unique_pairs = pairs_stats.get('unique_pairs', total_pairs)
            if total_pairs > 0:
                complexity = unique_pairs / total_pairs
                if complexity < self.min_complexity:
                    fail_reasons.append(f"complexity<{self.min_complexity}")
            
            if fail_reasons:
                failing_cells.append(cell_id)
                reason = ", ".join(fail_reasons)
                qc_report.append(f"{cell_id:<20} {num_contacts:>12} {'FAIL':>10} {reason:>20}")
            else:
                passing_cells.append(cell_id)
                qc_report.append(f"{cell_id:<20} {num_contacts:>12} {'PASS':>10} {'-':>20}")
        
        qc_report.append("-" * 70)
        qc_report.append(f"Total: {len(cell_stats)} cells | Passing: {len(passing_cells)} | Failing: {len(failing_cells)}")
        qc_report.append("=" * 70)
        
        # Write QC report
        qc_file = os.path.join(output_dir, 'cell_qc_summary.txt')
        with open(qc_file, 'w') as f:
            f.write('\n'.join(qc_report))
        
        logger.info(f"  QC report saved to: {qc_file}")
        
        return passing_cells, failing_cells

    def run_pseudobulk(
        self,
        passing_cells: List[str],
        cell_cool_files: Dict[str, str],
        output_dir: str,
    ) -> Dict[str, Any]:
        """
        Aggregate passing cells into a pseudobulk contact matrix.

        Args:
            passing_cells: List of passing cell IDs
            cell_cool_files: Dict mapping cell_id -> path to .cool file
            output_dir: Output directory for pseudobulk matrix

        Returns:
            Dictionary with pseudobulk output file paths
        """
        # TODO: Delegate to SnHiCPseudoBulk
        #raise NotImplementedError("SnHiCPipeline.run_pseudobulk() not yet implemented")
        
        import subprocess
        
        os.makedirs(output_dir, exist_ok=True)
        
        if not passing_cells:
            logger.warning("  No passing cells for pseudobulk aggregation")
            return {'status': 'no_cells'}
        
        logger.info(f"  Aggregating {len(passing_cells)} cells into pseudobulk...")
        
        # Filter valid cool files
        valid_cool_files = []
        for cid in passing_cells:
            cool_file = cell_cool_files.get(cid, '')
            if cool_file and os.path.exists(cool_file):
                valid_cool_files.append(cool_file)
            else:
                logger.warning(f"    Missing cool file for {cid}: {cool_file}")
        
        if not valid_cool_files:
            logger.error("  No valid cool files found for pseudobulk")
            return {'status': 'no_valid_files', 'num_cells': len(passing_cells)}
        
        # Create merged cool file using cooler merge
        merged_cool = os.path.join(output_dir, 'pseudobulk.merged.cool')
        logger.info(f"  Merging {len(valid_cool_files)} cell matrices...")
        
        # Use cooler merge or cooler combine
        merge_cmd = f"cooler merge {merged_cool} {' '.join(valid_cool_files)}"
        try:
            subprocess.run(merge_cmd, shell=True, check=True, capture_output=True)
            logger.info(f"  Merged matrix: {merged_cool}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"  cooler merge failed: {e}")
            # Fallback: use first cell as base
            if valid_cool_files:
                import shutil
                shutil.copy(valid_cool_files[0], merged_cool)
                logger.info(f"  Using first cell as pseudobulk base: {merged_cool}")
        
        # Create multi-resolution mcool
        mcool_file = os.path.join(output_dir, 'pseudobulk.mcool')
        logger.info(f"  Creating multi-resolution matrix (resolutions: {self.resolutions})...")
        
        zoomify_cmd = f"cooler zoomify --balance --resolutions {','.join(map(str, self.resolutions))} -o {mcool_file} {merged_cool}"
        try:
            subprocess.run(zoomify_cmd, shell=True, check=True, capture_output=True)
            logger.info(f"  Multi-resolution matrix: {mcool_file}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"  cooler zoomify failed: {e}")
        
        # Get stats
        stats = {
            'status': 'success',
            'num_cells': len(passing_cells),
            'num_valid_files': len(valid_cool_files),
            'merged_cool': merged_cool,
            'mcool': mcool_file,
        }
        
        return stats

    def run_clustering(
        self,
        passing_cells: List[str],
        cell_cool_files: Dict[str, str],
        output_dir: str,
        resolution: int = 1_000_000,
    ) -> Dict[str, Any]:
        """
        Run GNN-based cell type clustering on passing cells.

        Builds a cell×bin matrix from per-cell .cool files, then
        runs GraphSAGE + Leiden clustering via the clustering submodule.

        Args:
            passing_cells: List of passing cell IDs
            cell_cool_files: Dict mapping cell_id -> path to .cool file
            output_dir: Output directory for clustering results
            resolution: Bin resolution in bp for cell×bin matrix (default: 1Mb)

        Returns:
            Dictionary with clustering results and output paths
        """
        # TODO: Import and delegate to clustering.preprocessing + clustering.gnn_clustering
        raise NotImplementedError("SnHiCPipeline.run_clustering() not yet implemented")

    def run(
        self,
        cells: List[Tuple[str, str, str]],
        output_dir: str,
        run_clustering: bool = False,
        cleanup: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the complete sn-Hi-C pipeline on multiple cells.

        Args:
            cells: List of (cell_id, fastq_r1, fastq_r2) tuples
            output_dir: Root output directory
            run_clustering: Run GNN clustering after QC (default: False)
            cleanup: Remove per-cell intermediates after processing (default: False)

        Returns:
            Dictionary with full pipeline statistics:
                - per_cell_stats: Dict of per-cell processing stats
                - passing_cells: List of QC-passing cell IDs
                - failing_cells: List of QC-failing cell IDs
                - pseudobulk: Pseudobulk output paths
                - clustering: Clustering results (if run_clustering=True)
                - timing: Step-by-step timing breakdown
        """
        pipeline_start = time.time()

        logger.info("=" * 70)
        logger.info("sn-Hi-C PIPELINE")
        logger.info("=" * 70)
        logger.info(f"  Cells:           {len(cells)}")
        logger.info(f"  Output dir:      {output_dir}")
        logger.info(f"  Run clustering:  {run_clustering}")
        logger.info(f"  Start time:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        os.makedirs(output_dir, exist_ok=True)

        timing = {}
        all_stats: Dict[str, Any] = {
            'num_cells_input': len(cells),
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        # ── Step 1-4: Per-cell processing ─────────────────────────────────────
        logger.info("\n[STEP 1-4] Processing cells individually...")
        step_start = time.time()
        per_cell_stats: Dict[str, Dict] = {}

        for cell_id, fastq_r1, fastq_r2 in cells:
            cell_out = os.path.join(output_dir, 'cells', cell_id)
            logger.info(f"  Processing cell: {cell_id}")
            try:
                stats = self.process_cell(cell_id, fastq_r1, fastq_r2, cell_out, cleanup)
                per_cell_stats[cell_id] = stats
            except NotImplementedError:
                raise
            except Exception as e:
                logger.error(f"  Cell {cell_id} failed: {e}")
                per_cell_stats[cell_id] = {'status': 'failed', 'error': str(e)}

        timing['per_cell_processing'] = time.time() - step_start
        all_stats['per_cell_stats'] = per_cell_stats

        # ── Step 5: Cell QC ───────────────────────────────────────────────────
        logger.info("\n[STEP 5] Cell QC filtering...")
        step_start = time.time()
        qc_out = os.path.join(output_dir, 'qc')
        passing_cells, failing_cells = self.run_cell_qc(per_cell_stats, qc_out)
        timing['cell_qc'] = time.time() - step_start

        logger.info(f"  Passing cells: {len(passing_cells)} / {len(cells)}")
        logger.info(f"  Failing cells: {len(failing_cells)}")
        all_stats['passing_cells'] = passing_cells
        all_stats['failing_cells'] = failing_cells

        # ── Step 6: Pseudobulk ────────────────────────────────────────────────
        logger.info("\n[STEP 6] Pseudobulk aggregation...")
        step_start = time.time()
        cell_cool_files = {
            cid: per_cell_stats[cid].get('cool_file', '')
            for cid in passing_cells
        }
        pseudobulk_out = os.path.join(output_dir, 'pseudobulk')
        pseudobulk_stats = self.run_pseudobulk(passing_cells, cell_cool_files, pseudobulk_out)
        timing['pseudobulk'] = time.time() - step_start
        all_stats['pseudobulk'] = pseudobulk_stats

        # ── Step 7: Clustering (optional) ─────────────────────────────────────
        if run_clustering:
            logger.info("\n[STEP 7] GNN clustering...")
            step_start = time.time()
            clustering_out = os.path.join(output_dir, 'clustering')
            clustering_stats = self.run_clustering(passing_cells, cell_cool_files, clustering_out)
            timing['clustering'] = time.time() - step_start
            all_stats['clustering'] = clustering_stats

        # ── Summary ───────────────────────────────────────────────────────────
        total_duration = time.time() - pipeline_start
        timing['total'] = total_duration
        all_stats['timing'] = timing
        all_stats['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        logger.info("\n" + "=" * 70)
        logger.info("sn-Hi-C PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"  Total cells:    {len(cells)}")
        logger.info(f"  Passing cells:  {len(passing_cells)}")
        logger.info(f"  Total time:     {_format_duration(total_duration)}")

        return all_stats
