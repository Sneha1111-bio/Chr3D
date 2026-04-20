#!/usr/bin/env python3
"""
Chr3D Command Line Interface

Usage:
    chr3d bulk-hic   Run the bulk Hi-C pipeline (single sample)
    chr3d sn-hic     Run the single-nucleus Hi-C pipeline (multiple cells)
    chr3d chia-pet   Run the ChIA-PET pipeline (linker filter → map → peaks → loops)
    chr3d hichip     Run the HiChIP pipeline (align → dedup → MboI purify → background)
    chr3d digest     Generate restriction fragment BED from genome FASTA

Examples:
    # Bulk Hi-C
    chr3d bulk-hic \\
        --r1 sample_R1.fastq.gz \\
        --r2 sample_R2.fastq.gz \\
        --genome /path/to/hg38.fa \\
        --chrom-sizes /path/to/hg38.chrom.sizes \\
        --output-dir ./results/my_sample \\
        --sample-id my_sample

    # sn-Hi-C (manifest file with one cell per line: cell_id<TAB>R1.fastq.gz<TAB>R2.fastq.gz)
    chr3d sn-hic \\
        --manifest cells.tsv \\
        --genome /path/to/hg38.fa \\
        --chrom-sizes /path/to/hg38.chrom.sizes \\
        --output-dir ./results/sn_hic

    # ChIA-PET
    chr3d chia-pet \\
        --r1 sample_R1.fastq.gz \\
        --r2 sample_R2.fastq.gz \\
        --genome /path/to/hg38.fa \\
        --linkers ACGCGATATCGCG \\
        --output-dir ./results/chiapet \\
        --sample-id my_sample

    # HiChIP
    chr3d hichip \\
        --r1 sample_R1.fastq.gz \\
        --r2 sample_R2.fastq.gz \\
        --genome /path/to/hg38.fa \\
        --fragments /path/to/hg38_MboI_fragments.bed \\
        --output-dir ./results/hichip \\
        --sample-id my_sample
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

from .utils.logging import setup_logging, get_logger

logger = get_logger('chr3d')


# =============================================================================
# Bulk Hi-C command
# =============================================================================

def cmd_bulk_hic(args):
    """Run the complete bulk Hi-C pipeline for a single sample."""
    from .hic.bulk_hic import HiCPipeline

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("CHR3D  —  BULK Hi-C PIPELINE")
    logger.info("=" * 70)
    logger.info(f"  Sample ID    : {args.sample_id}")
    logger.info(f"  R1           : {args.r1}")
    logger.info(f"  R2           : {args.r2}")
    logger.info(f"  Genome       : {args.genome}")
    logger.info(f"  Chrom sizes  : {args.chrom_sizes}")
    logger.info(f"  Output dir   : {output_dir}")
    logger.info(f"  Threads      : {args.threads}")
    logger.info(f"  Assembly     : {args.assembly}")
    logger.info(f"  Min MAPQ     : {args.min_mapq}")
    logger.info(f"  Min distance : {args.min_distance} bp")
    logger.info(f"  Resolutions  : {args.resolutions}")
    logger.info(f"  Splits       : {args.splits}")
    logger.info(f"  Call TADs    : {not args.no_tads}")
    logger.info(f"  Call loops   : {not args.no_loops}")
    logger.info(f"  Loop FDR     : {args.loop_fdr}")
    logger.info(f"  Call comps   : {not args.no_compartments}")
    logger.info(f"  Phasing track: {args.compartment_phasing_track or 'None'}") 
    logger.info(f"  Keep files   : {args.keep_intermediates}")
    logger.info(f"  RE enzyme    : {getattr(args, 'restriction_enzyme', None) or 'none (DNase/Micro-C)'}")
    logger.info(f"  Fragment BED : {getattr(args, 'fragment_bed', None) or 'auto-generate'}")
    logger.info("=" * 70)

    try:
        resolutions = [int(r) for r in args.resolutions.split(',')]
        tad_windows = (
            [int(w) for w in args.tad_windows.split(',')]
            if args.tad_windows else None
        )

        # Handle restriction enzyme / fragment BED
        fragment_bed = getattr(args, 'fragment_bed', None)
        restriction_enzyme = getattr(args, 'restriction_enzyme', None)
        if restriction_enzyme and restriction_enzyme.lower() != 'none' and not fragment_bed:
            from .utils.restriction_sites import RestrictionSiteGenerator
            enzyme_tag = restriction_enzyme.replace('^', '').replace('/', '_')
            frag_out = output_dir / f'fragments_{enzyme_tag}.bed'
            if frag_out.exists():
                logger.info(f"Fragment BED already exists, reusing: {frag_out}")
            else:
                logger.info(f"Generating restriction fragments for {restriction_enzyme} ...")
                gen = RestrictionSiteGenerator(restriction_enzyme)
                gen.generate_sites(args.genome, str(frag_out))
            fragment_bed = str(frag_out)

        pipeline = HiCPipeline(
            genome_index=args.genome,
            chrom_sizes=args.chrom_sizes,
            threads=args.threads,
            assembly=args.assembly,
            min_mapq=args.min_mapq,
            min_distance=args.min_distance,
            resolutions=resolutions,
            n_splits=args.splits,
            call_tads=not args.no_tads,
            tad_windows=tad_windows,
            call_loops=not args.no_loops,
            loop_fdr=args.loop_fdr,
            call_compartments=not args.no_compartments,
            compartment_phasing_track=args.compartment_phasing_track,
            fragment_bed=fragment_bed,
        )

        stats = pipeline.run(
            fastq1=args.r1,
            fastq2=args.r2,
            output_dir=output_dir,
            sample_id=args.sample_id,
            cleanup=not args.keep_intermediates,
            start_from=args.start_from,
        )

        _print_bulk_hic_summary(stats, output_dir, args.sample_id)
        return 0

    except Exception as e:
        logger.error(f"Bulk Hi-C pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _print_bulk_hic_summary(stats: dict, output_dir: Path, sample_id: str):
    """Print a clean summary after bulk Hi-C completes."""
    outputs  = stats.get('final_outputs', {})
    timing   = stats.get('timing', {})
    tad_s    = stats.get('tad_calling', {})
    loop_s   = stats.get('loop_calling', {})

    logger.info("\n" + "=" * 70)
    logger.info("BULK Hi-C COMPLETE")
    logger.info("=" * 70)
    logger.info("Output files:")
    logger.info(f"  Sorted BAM      : {outputs.get('sorted_bam', 'N/A')}")
    logger.info(f"  Sorted pairs    : {outputs.get('sorted_pairs', 'N/A')}")
    logger.info(f"  Filtered pairs  : {outputs.get('filtered_pairs', 'N/A')}")
    logger.info(f"  Contact matrix  : {outputs.get('cool_matrix', 'N/A')}")
    logger.info(f"  Multi-res matrix: {outputs.get('mcool_matrix', 'N/A')}")
    if outputs.get('tads_dir'):
        logger.info(f"  TADs dir        : {outputs['tads_dir']}")
        if tad_s.get('summary_tsv'):
            logger.info(f"  TAD summary     : {tad_s['summary_tsv']}")
        logger.info(f"  TAD combos OK   : {tad_s.get('n_success', 'N/A')}")
    if outputs.get('loops_dir'):
        logger.info(f"  Loops dir       : {outputs['loops_dir']}")
        if loop_s.get('summary_tsv'):
            logger.info(f"  Loop summary    : {loop_s['summary_tsv']}")
        n_loops = loop_s.get('n_loops', {})
        if n_loops:
            for res, n in n_loops.items():
                logger.info(f"    {res//1000}kb loops   : {n}")
    comp_s = stats.get('compartment_calling', {})
    if outputs.get('compartments_dir'):
        logger.info(f"  Compartments dir: {outputs['compartments_dir']}")
        if comp_s.get('summary_tsv'):
            logger.info(f"  Comp. summary   : {comp_s['summary_tsv']}")
        for res in comp_s.get('resolutions', []):
            logger.info(f"    {res//1000}kb compartments: done")

    if timing:
        logger.info("Timing:")
        for step, secs in timing.items():
            if step != 'total':
                logger.info(f"  {step:<30}: {_fmt_time(secs)}")
        logger.info(f"  {'Total':<30}: {_fmt_time(timing.get('total', 0))}")

    logger.info("=" * 70)


# =============================================================================
# sn-Hi-C command
# =============================================================================

def cmd_sn_hic(args):
    """Run the sn-Hi-C pipeline over multiple cells from a manifest file."""
    from .hic.sn_hic import SnHiCPipeline

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse manifest: cell_id <TAB> R1 <TAB> R2
    cells = _parse_manifest(args.manifest)
    if not cells:
        logger.error(f"No cells found in manifest: {args.manifest}")
        return 1

    logger.info("=" * 70)
    logger.info("CHR3D  —  sn-Hi-C PIPELINE")
    logger.info("=" * 70)
    logger.info(f"  Manifest     : {args.manifest}")
    logger.info(f"  Cells        : {len(cells)}")
    logger.info(f"  Genome       : {args.genome}")
    logger.info(f"  Chrom sizes  : {args.chrom_sizes}")
    logger.info(f"  Output dir   : {output_dir}")
    logger.info(f"  Threads      : {args.threads}")
    logger.info(f"  Assembly     : {args.assembly}")
    logger.info(f"  Min MAPQ     : {args.min_mapq}")
    logger.info(f"  Min distance : {args.min_distance} bp")
    logger.info(f"  Resolutions  : {args.resolutions}")
    logger.info(f"  Splits       : {args.splits}")
    logger.info(f"  Min contacts : {args.min_contacts}")
    logger.info(f"  Keep files   : {args.keep_intermediates}")
    logger.info("=" * 70)

    try:
        resolutions = [int(r) for r in args.resolutions.split(',')]

        pipeline = SnHiCPipeline(
            genome_index=args.genome,
            chrom_sizes=args.chrom_sizes,
            threads=args.threads,
            assembly=args.assembly,
            min_mapq=args.min_mapq,
            min_distance=args.min_distance,
            resolutions=resolutions,
            min_contacts_per_cell=args.min_contacts,
        )

        stats = pipeline.run(
            cells=cells,
            output_dir=str(output_dir),
            run_clustering=False,       # Clustering left for future implementation
            cleanup=not args.keep_intermediates,
            start_from=args.start_from,
        )

        _print_sn_hic_summary(stats, output_dir)
        return 0

    except Exception as e:
        logger.error(f"sn-Hi-C pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _parse_manifest(manifest_path: str):
    """
    Parse sn-Hi-C manifest file.

    Expected format (tab-separated, with or without header):
        cell_id    R1.fastq.gz    R2.fastq.gz
    """
    cells = []
    with open(manifest_path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) != 3:
                logger.warning(f"  Manifest line {lineno} skipped (expected 3 tab-separated columns): {line[:50]}...")
                continue
            cell_id, r1, r2 = parts
            # Skip header line
            if cell_id.strip().lower() in ('cell_id', 'id', 'sample', 'sample_id'):
                continue
            if not Path(r1).exists():
                logger.warning(f"  Cell {cell_id}: R1 not found: {r1}")
            if not Path(r2).exists():
                logger.warning(f"  Cell {cell_id}: R2 not found: {r2}")
            cells.append((cell_id.strip(), r1.strip(), r2.strip()))
    return cells


def _print_sn_hic_summary(stats: dict, output_dir: Path):
    """Print a clean summary after sn-Hi-C completes."""
    timing         = stats.get('timing', {})
    passing_cells  = stats.get('passing_cells', [])
    failing_cells  = stats.get('failing_cells', [])
    n_input        = stats.get('num_cells_input', 0)

    logger.info("\n" + "=" * 70)
    logger.info("sn-Hi-C COMPLETE")
    logger.info("=" * 70)
    logger.info(f"  Cells processed : {n_input}")
    logger.info(f"  Cells passing QC: {len(passing_cells)}")
    logger.info(f"  Cells failing QC: {len(failing_cells)}")
    logger.info(f"  Output dir      : {output_dir}")
    logger.info(f"  Pseudobulk cool : {output_dir}/pseudobulk/pseudobulk.cool")
    logger.info(f"  Cell QC report  : {output_dir}/qc/cell_qc_summary.txt")

    if timing:
        logger.info("Timing:")
        for step, secs in timing.items():
            if step != 'total':
                logger.info(f"  {step:<25}: {_fmt_time(secs)}")
        logger.info(f"  {'Total':<25}: {_fmt_time(timing.get('total', 0))}")

    logger.info("=" * 70)


# =============================================================================
# Shared helpers
# =============================================================================

def _fmt_time(seconds: float) -> str:
    """Format seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f} min"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


# =============================================================================
# HiChIP command
# =============================================================================

def cmd_hichip(args):
    """Run the complete HiChIP pipeline."""
    from .peak_based.hichip_pipline import HiChIPPipeline

    pipeline = HiChIPPipeline(
        genome_index=args.genome,
        fragment_bed=args.fragments,
        threads=args.threads,
        n_chunks=args.n_chunks,
        min_insert_size=args.min_insert,
        keep_intermediates=args.keep_intermediates,
    )
    try:
        stats = pipeline.run(
            fastq_r1=args.r1,
            fastq_r2=args.r2,
            output_dir=args.output_dir,
            sample_id=args.sample_id,
            start_from=args.start_from,
        )
        return 0
    except Exception as e:
        logger.error(f"HiChIP pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


# =============================================================================
# ChIA-PET command
# =============================================================================

def cmd_chia_pet(args):
    """Run the complete ChIA-PET pipeline."""
    from .peak_based.chiapet_pipeline import ChiaPetPipeline

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    linkers = [s.strip() for s in args.linkers.split(',') if s.strip()]

    logger.info("=" * 70)
    logger.info("CHR3D  —  ChIA-PET PIPELINE")
    logger.info("=" * 70)
    logger.info(f"  Sample ID    : {args.sample_id}")
    logger.info(f"  R1           : {args.r1}")
    logger.info(f"  R2           : {args.r2}")
    logger.info(f"  Genome       : {args.genome}")
    logger.info(f"  Linkers      : {linkers}")
    logger.info(f"  Threads      : {args.threads}")
    logger.info(f"  MAPQ         : {args.mapq}")
    logger.info(f"  Genome size  : {args.genome_size}")
    logger.info(f"  Q-value      : {args.qvalue}")
    logger.info(f"  FDR alpha    : {args.alpha}")
    logger.info(f"  Std chroms   : {args.standard_chroms}")
    logger.info(f"  Cytoband     : {args.cytoband}")
    logger.info(f"  Output dir   : {output_dir}")
    logger.info("=" * 70)

    try:
        pipeline = ChiaPetPipeline(
            genome_index=args.genome,
            linkers=linkers,
            threads=args.threads,
            mapq=args.mapq,
            genome_size=args.genome_size,
            qvalue=args.qvalue,
            alpha=args.alpha,
            min_score=args.min_score,
            min_tag=args.min_tag,
            max_tag=args.max_tag,
            standard_chroms_only=args.standard_chroms,
            cytoband_file=args.cytoband,
            keep_intermediates=args.keep_intermediates,
        )

        stats = pipeline.run(
            fastq_r1=args.r1,
            fastq_r2=args.r2,
            output_dir=str(output_dir),
            sample_id=args.sample_id,
            start_from=args.start_from,
        )

        _print_chia_pet_summary(stats, output_dir, args.sample_id)
        return 0

    except Exception as e:
        logger.error(f"ChIA-PET pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _print_chia_pet_summary(stats: dict, output_dir: Path, sample_id: str):
    """Print clean summary after ChIA-PET pipeline completes."""
    timing     = stats.get('timing', {})
    peak_stats = stats.get('peak_stats', {})
    loop_stats = stats.get('loop_stats', {})
    classify   = loop_stats.get('classify', {})

    logger.info("\n" + "=" * 70)
    logger.info("ChIA-PET COMPLETE")
    logger.info("=" * 70)
    logger.info(f"  Peaks called     : {peak_stats.get('num_peaks', 'N/A')}")
    logger.info(f"  P2P PETs         : {classify.get('P2P', 'N/A')}")
    logger.info(f"  D2D PETs         : {classify.get('D2D', 'N/A')}")
    logger.info(f"  Loops (FDR)      : {loop_stats.get('loops_csv', 'N/A')}")
    logger.info(f"  QC report        : {output_dir}/qc/{sample_id}_pipeline_summary.txt")

    if timing:
        logger.info("Timing:")
        for step, secs in timing.items():
            if step != 'total':
                logger.info(f"  {step:<22}: {_fmt_time(secs)}")
        logger.info(f"  {'Total':<22}: {_fmt_time(timing.get('total', 0))}")

    logger.info("=" * 70)


# =============================================================================
# Argument parser
# =============================================================================

def _add_common_hic_args(parser):
    """Add arguments shared between bulk-hic and sn-hic."""
    # Required
    req = parser.add_argument_group('required arguments')
    req.add_argument('--genome',      required=True, metavar='PATH',
                     help='BWA-indexed genome FASTA (e.g. /ref/hg38.fa)')
    req.add_argument('--chrom-sizes', required=True, metavar='PATH',
                     help='Chromosome sizes file (e.g. hg38.chrom.sizes)')
    req.add_argument('--output-dir',  required=True, metavar='DIR',
                     help='Output directory (created if it does not exist)')

    # Processing
    proc = parser.add_argument_group('processing')
    proc.add_argument('--threads',    type=int, default=4,    metavar='N',
                      help='Number of CPU threads (default: 4)')
    proc.add_argument('--splits',     type=int, default=0,    metavar='N',
                      help='Split FASTQ into N chunks for parallel alignment; '
                           '0 = no splitting (default: 0)')
    proc.add_argument('--assembly',   default='hg38', metavar='NAME',
                      help='Genome assembly name written into .cool metadata (default: hg38)')

    # Filtering
    filt = parser.add_argument_group('filtering')
    filt.add_argument('--min-mapq',     type=int, default=30,
                      metavar='INT', help='Minimum BWA mapping quality (default: 30)')
    filt.add_argument('--min-distance', type=int, default=1000,
                      metavar='BP',  help='Minimum pair distance in bp (default: 1000)')
    filt.add_argument('--resolutions',  default='1000,5000,10000',
                      metavar='CSV',
                      help='Comma-separated list of matrix resolutions in bp '
                           '(default: 1000,5000,10000)')

    # TAD calling
    tad = parser.add_argument_group('TAD calling')
    tad.add_argument('--no-tads', action='store_true',
                     help='Skip TAD / insulation score calling (default: run)')
    tad.add_argument('--tad-windows', default=None, metavar='CSV',
                     help='Comma-separated insulation window sizes in bp '
                          '(default: 30000,50000,100000,200000,500000,1000000)')

    # Loop calling
    lp = parser.add_argument_group('loop calling')
    lp.add_argument('--no-loops', action='store_true',
                    help='Skip Hi-C loop calling (default: run)')
    lp.add_argument('--loop-fdr', type=float, default=0.1, metavar='FLOAT',
                    help='FDR threshold for loop significance (default: 0.1)')

    # Restriction enzyme
    re_grp = parser.add_argument_group('restriction enzyme')
    re_grp.add_argument('--restriction-enzyme', default=None, metavar='NAME_OR_SITE',
                        help='Restriction enzyme name (HindIII, DpnII, MboI, BglII, Arima) '
                             'or recognition site with cut position (e.g. A^AGCTT). '
                             'Use "none" for DNase Hi-C / Micro-C (default: none)')
    re_grp.add_argument('--fragment-bed', default=None, metavar='BED',
                        help='Pre-computed restriction fragment BED file. '
                             'If provided with --restriction-enzyme, skips auto-generation.')

    # A/B Compartment calling
    comp = parser.add_argument_group('compartment calling')
    comp.add_argument('--no-compartments', action='store_true',
                      help='Skip A/B compartment calling (default: run)')
    comp.add_argument('--compartment-phasing-track', default=None, metavar='BED',
                      help='BED file (chrom,start,end,value) to orient E1 sign, '
                           'e.g. gene density track (default: None, sign unoriented)')

    # Output control
    out = parser.add_argument_group('output')
    out.add_argument('--keep-intermediates', action='store_true',
                     help='Keep intermediate BAM / pairs files (default: delete them)')

    # Resume
    resume = parser.add_argument_group('resume')
    resume.add_argument('--start-from', type=int, default=1, choices=range(1, 8),
                        metavar='STEP',
                        help='Resume from step N (1-7). 1=alignment, 2=SAM/BAM, '
                             '3=pairs, 4=matrix, 5=TADs, 6=loops, 7=compartments. '
                             'Default: 1 (full pipeline). When resuming, prior outputs '
                             'must exist at canonical paths under --output-dir.')

    # Logging
    log = parser.add_argument_group('logging')
    log.add_argument('-v', '--verbose', action='store_true',
                     help='Enable DEBUG-level logging')
    log.add_argument('--log-file', metavar='FILE',
                     help='Write log to FILE in addition to stdout')


def build_parser():
    parser = argparse.ArgumentParser(
        prog='chr3d',
        description='Chr3D  —  Hi-C data processing pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', metavar='COMMAND')

    # ------------------------------------------------------------------
    # bulk-hic
    # ------------------------------------------------------------------
    bulk = subparsers.add_parser(
        'bulk-hic',
        help='Bulk Hi-C pipeline  (1 sample: alignment → samtools → pairtools → cooltools)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
Bulk Hi-C Pipeline
==================
Steps:
  1. Alignment    BWA MEM  →  SAM
  2. SAM/BAM      samtools sort / index  →  sorted BAM  +  flagstat
  3. Pairs        pairtools parse / sort / dedup / filter  →  .pairs.gz
  4. Matrix       cooler cload / zoomify  →  .cool  +  .mcool

Output layout:
  <output-dir>/
  ├── aligned/     sorted BAM + flagstat
  ├── pairs/       .pairs.gz files
  └── matrices/    .cool + .mcool
""",
    )
    inp = bulk.add_argument_group('inputs')
    inp.add_argument('--r1',        metavar='FASTQ',
                     help='R1 FASTQ file (required unless --start-from > 1)')
    inp.add_argument('--r2',        metavar='FASTQ',
                     help='R2 FASTQ file (required unless --start-from > 1)')
    inp.add_argument('--sample-id', default='sample', metavar='STR',
                     help='Sample identifier used in output file names (default: sample)')
    _add_common_hic_args(bulk)
    bulk.set_defaults(func=cmd_bulk_hic)

    # ------------------------------------------------------------------
    # sn-hic
    # ------------------------------------------------------------------
    sn = subparsers.add_parser(
        'sn-hic',
        help='Single-nucleus Hi-C pipeline  (N cells: per-cell loop → pseudobulk)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
Single-Nucleus Hi-C Pipeline
=============================
Steps (run for EACH cell in the manifest):
  1. Alignment    BWA MEM  →  SAM
  2. SAM/BAM      samtools sort / index  →  sorted BAM  +  flagstat
  3. Pairs        pairtools parse / sort / dedup / filter  →  .pairs.gz
  4. Matrix       cooler cload / zoomify  →  per-cell .cool

After all cells:
  5. Cell QC      Filter cells by min-contacts threshold
  6. Pseudobulk   cooler merge passing cells  →  pseudobulk .cool + .mcool

Manifest format (tab-separated, no header):
  cell_id    R1.fastq.gz    R2.fastq.gz

Output layout:
  <output-dir>/
  ├── cells/
  │   ├── <cell_id>/
  │   │   ├── aligned/    sorted BAM
  │   │   ├── pairs/      .pairs.gz
  │   │   └── matrices/   per-cell .cool
  │   └── ...
  ├── pseudobulk/          pseudobulk.cool + pseudobulk.mcool
  └── qc/                  cell_qc_summary.txt + passing_cells.txt
""",
    )
    inp = sn.add_argument_group('inputs')
    inp.add_argument('--manifest', required=True, metavar='TSV',
                     help='Tab-separated manifest: cell_id  R1.fastq.gz  R2.fastq.gz')
    _add_common_hic_args(sn)

    qc = sn.add_argument_group('cell QC')
    qc.add_argument('--min-contacts', type=int, default=1000, metavar='INT',
                    help='Minimum valid contacts to keep a cell (default: 1000)')

    sn.set_defaults(func=cmd_sn_hic)

    # ------------------------------------------------------------------
    # chia-pet
    # ------------------------------------------------------------------
    chia = subparsers.add_parser(
        'chia-pet',
        help='ChIA-PET pipeline  (linker filtering → mapping → peak calling → loop calling)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
ChIA-PET Pipeline
=================
Steps:
  1. Linker filtering   parasail SIMD  →  filtered FASTQ (same-linker PETs)
  2. Mapping            BWA MEM        →  BAM + BEDPE (deduplicated)
  3. Peak calling       MACS3          →  broadPeak / narrowPeak
  4. Background model
     4a. classify_pets  →  P2P / P2D / D2D PET files
     4b. extract_templates  →  templates.csv
     4c. NB sampling    →  templates_with_nb.csv
     4d. p-values       →  templates_with_pvalues.csv
     4e. FDR correction →  significant_loops.csv

Output layout:
  <output-dir>/
  ├── filtered/    per-linker-category FASTQ + merged filtered FASTQ
  ├── mapped/      BAM, BEDPE, dedup BEDPE + flagstat
  ├── peaks/       MACS3 broadPeak + summits
  ├── loops/
  │   ├── classified/   P2P / P2D / D2D PET files
  │   ├── templates/    templates.csv, NB params, p-values
  │   └── results/      significant_loops.csv
  └── qc/              pipeline_summary.txt
""",
    )
    inp = chia.add_argument_group('inputs')
    inp.add_argument('--r1',        metavar='FASTQ',
                     help='R1 FASTQ file (required unless --start-from > 1)')
    inp.add_argument('--r2',        metavar='FASTQ',
                     help='R2 FASTQ file (required unless --start-from > 1)')
    inp.add_argument('--sample-id', default='sample', metavar='STR',
                     help='Sample identifier used in output file names (default: sample)')
    inp.add_argument('--genome',    required=True, metavar='PATH',
                     help='BWA-indexed genome FASTA')
    inp.add_argument('--output-dir', required=True, metavar='DIR',
                     help='Output directory (created if absent)')

    lnk = chia.add_argument_group('linker filtering')
    lnk.add_argument('--linkers', required=True, metavar='SEQ[,SEQ]',
                     help='Comma-separated linker sequence(s) (e.g. ACGCGATATCGCG)')
    lnk.add_argument('--min-score',  type=int, default=20, metavar='INT',
                     help='Minimum parasail alignment score (default: 20)')
    lnk.add_argument('--min-tag',    type=int, default=15, metavar='INT',
                     help='Minimum genomic tag length after linker removal (default: 15)')
    lnk.add_argument('--max-tag',    type=int, default=40, metavar='INT',
                     help='Maximum genomic tag length after linker removal (default: 40)')

    mp = chia.add_argument_group('mapping')
    mp.add_argument('--mapq',     type=int, default=30, metavar='INT',
                    help='Minimum mapping quality (default: 30)')
    mp.add_argument('--threads',  type=int, default=4,  metavar='N',
                    help='CPU threads for BWA / samtools (default: 4)')

    pk = chia.add_argument_group('peak calling')
    pk.add_argument('--genome-size', default='hs', metavar='STR',
                    help='MACS3 genome size: hs, mm, or integer (default: hs)')
    pk.add_argument('--qvalue',      type=float, default=0.05, metavar='FLOAT',
                    help='MACS3 q-value cutoff (default: 0.05)')

    lp = chia.add_argument_group('loop calling')
    lp.add_argument('--alpha',             type=float, default=0.05, metavar='FLOAT',
                    help='FDR significance threshold (default: 0.05)')
    lp.add_argument('--standard-chroms',   action='store_true',
                    help='Restrict loop calling to chr1-22 + chrX/Y')
    lp.add_argument('--cytoband',          metavar='FILE',
                    help='UCSC cytoband file for centromere exclusion (optional)')

    out = chia.add_argument_group('output')
    out.add_argument('--keep-intermediates', action='store_true',
                     help='Keep intermediate BAM files (default: delete)')

    resume = chia.add_argument_group('resume')
    resume.add_argument('--start-from', type=int, default=1, choices=range(1, 5),
                        metavar='STEP',
                        help='Resume from step N (1-4). 1=linker filtering, '
                             '2=mapping, 3=peak calling, 4=background model / loop calling. '
                             'Default: 1 (full pipeline). When resuming, outputs from '
                             'prior steps must exist at canonical paths under --output-dir.')

    log = chia.add_argument_group('logging')
    log.add_argument('-v', '--verbose', action='store_true',
                     help='Enable DEBUG-level logging')
    log.add_argument('--log-file', metavar='FILE',
                     help='Write log to FILE in addition to stdout')

    chia.set_defaults(func=cmd_chia_pet)

    # ------------------------------------------------------------------
    # hichip
    # ------------------------------------------------------------------
    hichip = subparsers.add_parser(
        'hichip',
        help='HiChIP pipeline  (align → dedup → MboI purify → background model)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
HiChIP Pipeline
===============
Full HiChIP analysis pipeline:
  1. FASTQ splitting into parallel chunks
  2. BWA MEM -5SP -T0 alignment (per chunk, merged)
  3. BAM → BEDPE + 5' coordinate deduplication
  4. MboI restriction fragment purification
  5. Background model (randomised PETs, distance decay)
""",
    )
    hichip.add_argument('--r1', metavar='FASTQ',
                        help='R1 FASTQ file (required unless --start-from > 1)')
    hichip.add_argument('--r2', metavar='FASTQ',
                        help='R2 FASTQ file (required unless --start-from > 1)')
    hichip.add_argument('--genome', required=True, metavar='FASTA',
                        help='BWA-indexed genome FASTA')
    hichip.add_argument('--fragments', required=True, metavar='BED',
                        help='Restriction fragment BED (e.g. MboI from chr3d digest)')
    hichip.add_argument('--output-dir', required=True, metavar='DIR',
                        help='Output directory (created if absent)')
    hichip.add_argument('--sample-id', default='sample', metavar='STR',
                        help='Sample identifier for output file names (default: sample)')
    hichip.add_argument('--threads', type=int, default=24, metavar='INT',
                        help='Total CPU threads (default: 24)')
    hichip.add_argument('--n-chunks', type=int, default=6, metavar='INT',
                        help='Parallel BWA jobs — threads split evenly (default: 6)')
    hichip.add_argument('--min-insert', type=int, default=100, metavar='INT',
                        help='Min insert size for MboI purification bp (default: 100)')
    hichip.add_argument('--keep-intermediates', action='store_true',
                        help='Keep per-chunk FASTQ/BAM files after merge')
    hichip.add_argument('--start-from', type=int, default=1, choices=range(1, 7),
                        metavar='STEP',
                        help='Resume from step N (1-6). 1=split FASTQ, 2=align chunks, '
                             '3=merge BAMs, 4=BAM→BEDPE dedup, 5=MboI purification, '
                             '6=background model. Default: 1 (full pipeline). When '
                             'resuming, outputs from prior steps must exist at '
                             'canonical paths under --output-dir.')
    hichip.add_argument('-v', '--verbose', action='store_true',
                        help='Enable DEBUG-level logging')
    hichip.add_argument('--log-file', metavar='FILE',
                        help='Write log to FILE in addition to stdout')
    hichip.set_defaults(func=cmd_hichip)

    # ------------------------------------------------------------------
    # digest
    # ------------------------------------------------------------------
    dig = subparsers.add_parser(
        'digest',
        help='Generate restriction fragment BED from a genome FASTA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
Generate Restriction Fragment BED
===================================
In silico digest a genome FASTA with a restriction enzyme and output a
BED file of fragments.  This BED file can be passed to bulk-hic / sn-hic
via --fragment-bed to enable fragment-aware pair parsing with pairtools.

Supported enzyme names: HindIII, DpnII, MboI, BglII, Sau3AI, Hinf1,
                         NlaIII, AluI, EcoRI, BamHI, PstI, SalI, XbaI
Or pass the raw recognition site with cut position, e.g. A^AGCTT.

For Arima Hi-C (dual enzyme) use:
  chr3d digest --enzyme MboI --enzyme GATC^  -o arima_frags.bed genome.fa
""",
    )
    dig.add_argument('genome', metavar='FASTA',
                     help='Genome FASTA file (plain or gzipped)')
    dig.add_argument('-e', '--enzyme', dest='enzymes', required=True,
                     action='append', metavar='NAME_OR_SITE',
                     help='Enzyme name or recognition site (e.g. HindIII or A^AGCTT). '
                          'Repeat flag for multiple enzymes (Arima kit)')
    dig.add_argument('-o', '--output', required=True, metavar='BED',
                     help='Output BED file path')
    dig.add_argument('--min-size', type=int, default=20, metavar='INT',
                     help='Minimum fragment size to keep in bp (default: 20)')
    dig.add_argument('--max-size', type=int, default=10_000_000, metavar='INT',
                     help='Maximum fragment size to keep in bp (default: 10000000)')
    dig.add_argument('-v', '--verbose', action='store_true',
                     help='Enable DEBUG-level logging')
    dig.add_argument('--log-file', metavar='FILE',
                     help='Write log to FILE in addition to stdout')
    dig.set_defaults(func=cmd_digest)

    return parser


def cmd_digest(args):
    """Run standalone restriction enzyme genome digestion."""
    from .utils.restriction_sites import RestrictionSiteGenerator

    enzyme = args.enzymes if len(args.enzymes) > 1 else args.enzymes[0]

    logger.info("=" * 70)
    logger.info("CHR3D  —  RESTRICTION ENZYME DIGEST")
    logger.info("=" * 70)
    logger.info(f"  Genome   : {args.genome}")
    logger.info(f"  Enzyme(s): {enzyme}")
    logger.info(f"  Output   : {args.output}")
    logger.info(f"  Min size : {args.min_size} bp")
    logger.info(f"  Max size : {args.max_size} bp")
    logger.info("=" * 70)

    try:
        gen = RestrictionSiteGenerator(
            enzyme=enzyme,
            min_frag_size=args.min_size,
            max_frag_size=args.max_size,
        )
        stats = gen.generate_sites(args.genome, args.output)

        logger.info("=" * 70)
        logger.info("DIGEST COMPLETE")
        logger.info(f"  Chromosomes : {stats['chromosomes']}")
        logger.info(f"  RE sites    : {stats['total_sites']:,}")
        logger.info(f"  Fragments   : {stats['total_fragments'] - stats['filtered_fragments']:,}")
        logger.info(f"  Filtered    : {stats['filtered_fragments']:,} (outside size range)")
        logger.info(f"  Output BED  : {args.output}")
        logger.info("=" * 70)
        return 0

    except Exception as e:
        logger.error(f"Digest failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    parser = build_parser()
    args   = parser.parse_args()

    setup_logging(
        verbose=getattr(args, 'verbose', False),
        log_file=getattr(args, 'log_file', None),
    )

    if args.command is None:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())

