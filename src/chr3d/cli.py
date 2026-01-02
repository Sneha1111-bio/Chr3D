#!/usr/bin/env python3
"""
Chr3D Command Line Interface

Provides command-line access to all pipeline steps for ChIA-PET and HiChIP analysis.

Usage:
    chr3d <command> [options]

Commands:
    run             Run the complete pipeline
    filter-linker   Step 1: Filter linker sequences
    map             Step 2: Map reads to genome
    purify          Step 3: Purify PETs (deduplicate/merge)
    categorize      Step 4: Categorize PETs (iPET/sPET/oPET)
    call-peaks      Step 5: Call peaks from sPET
    call-loops      Step 6: Call significant loops
    generate-sites  Generate restriction site file
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('chr3d')


def setup_logging(verbose: bool = False, log_file: str = None):
    """Configure logging based on verbosity and optional log file."""
    level = logging.DEBUG if verbose else logging.INFO
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers,
        force=True
    )


def cmd_filter_linker(args):
    """Step 1: Filter linker sequences from FASTQ files."""
    from .linker_filtering_v2 import LinkerFilterV2
    
    logger.info("=" * 70)
    logger.info("STEP 1: LINKER FILTERING")
    logger.info("=" * 70)
    
    # Parse linker sequences
    linkers = [args.linker_a]
    if args.linker_b:
        linkers.append(args.linker_b)
    
    logger.info(f"Input R1: {args.fastq_r1}")
    logger.info(f"Input R2: {args.fastq_r2}")
    logger.info(f"Linkers: {linkers}")
    logger.info(f"Output prefix: {args.output_prefix}")
    
    # Create output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(args.fastq_r1).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize filter
    linker_filter = LinkerFilterV2(
        linker_sequences=linkers,
        min_alignment_score=args.min_score,
        min_tag_length=args.min_tag_length,
        max_tag_length=args.max_tag_length,
        n_threads=args.threads
    )
    
    # Run filtering
    stats = linker_filter.filter_fastq(
        fastq_r1=args.fastq_r1,
        fastq_r2=args.fastq_r2,
        output_prefix=args.output_prefix,
        output_dir=str(output_dir),
        compress_output=args.compress
    )
    
    logger.info(f"Linker filtering complete: {stats['valid_pets']:,} valid PETs")
    return 0


def cmd_map(args):
    """Step 2: Map reads to reference genome."""
    from .mapping_v2 import PETMapper
    
    logger.info("=" * 70)
    logger.info("STEP 2: GENOMIC MAPPING")
    logger.info("=" * 70)
    
    logger.info(f"Input R1: {args.fastq_r1}")
    logger.info(f"Input R2: {args.fastq_r2}")
    logger.info(f"Genome index: {args.genome_index}")
    logger.info(f"Output prefix: {args.output_prefix}")
    logger.info(f"BWA mode: {'MEM' if args.use_bwa_mem else 'ALN'}")
    
    # Create output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(args.fastq_r1).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize mapper
    mapper = PETMapper(
        genome_index=args.genome_index,
        mapping_quality_cutoff=args.mapping_quality,
        n_threads=args.threads,
        use_bwa_mem=args.use_bwa_mem,
        self_ligation_cutoff=args.self_ligation_cutoff
    )
    
    # Run mapping
    stats = mapper.map_linker_filtered_fastq(
        fastq_r1=args.fastq_r1,
        fastq_r2=args.fastq_r2,
        output_prefix=args.output_prefix,
        output_dir=str(output_dir),
        keep_sam=args.keep_sam,
        remove_duplicates=not args.no_dedup
    )
    
    logger.info(f"Mapping complete: {stats.get('valid_pairs', 0):,} valid pairs")
    return 0


def cmd_purify(args):
    """Step 3: Purify PETs (deduplicate and merge)."""
    logger.info("=" * 70)
    logger.info("STEP 3: PET PURIFYING")
    logger.info("=" * 70)
    
    logger.info(f"Input BEDPE: {args.bedpe}")
    logger.info(f"Output prefix: {args.output_prefix}")
    logger.info(f"Mode: {args.mode}")
    
    # Create output directory
    output_dir = Path(args.output_prefix).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.mode == 'chiapet':
        from .chiapet_purifying import ChIAPETPurifier
        
        purifier = ChIAPETPurifier(merge_distance=args.merge_distance)
        stats = purifier.purify(args.bedpe, args.output_prefix)
        
    else:  # hichip
        from .hichip_purifying import HiChIPPurifier
        
        if not args.restriction_sites:
            logger.error("HiChIP mode requires --restriction-sites")
            return 1
        
        purifier = HiChIPPurifier(
            restriction_file=args.restriction_sites,
            min_insert_size=args.min_insert_size
        )
        
        output_file = f"{args.output_prefix}.valid.bedpe"
        sameres_file = f"{args.output_prefix}.sameres.bedpe"
        stats = purifier.remove_same_fragment_pets(args.bedpe, output_file, sameres_file)
    
    logger.info("Purifying complete")
    return 0


def cmd_categorize(args):
    """Step 4: Categorize PETs into iPET, sPET, oPET."""
    from .pet_categorization import PETCategorizer
    
    logger.info("=" * 70)
    logger.info("STEP 4: PET CATEGORIZATION")
    logger.info("=" * 70)
    
    logger.info(f"Input BEDPE: {args.bedpe}")
    logger.info(f"Output prefix: {args.output_prefix}")
    logger.info(f"Self-ligation cutoff: {args.cutoff}bp")
    logger.info(f"Mode: {args.mode}")
    
    # Create output directory
    output_dir = Path(args.output_prefix).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize categorizer
    categorizer = PETCategorizer(
        self_ligation_cutoff=args.cutoff,
        mode=args.mode
    )
    
    # Run categorization
    stats = categorizer.categorize_bedpe(args.bedpe, args.output_prefix)
    
    logger.info(f"Categorization complete:")
    logger.info(f"  iPET: {stats['ipet']['count']:,} ({stats['ipet']['percentage']:.1f}%)")
    logger.info(f"  sPET: {stats['spet']['count']:,} ({stats['spet']['percentage']:.1f}%)")
    logger.info(f"  oPET: {stats['opet']['count']:,} ({stats['opet']['percentage']:.1f}%)")
    return 0


def cmd_call_peaks(args):
    """Step 5: Call peaks from sPET data."""
    from .peak_calling import PeakCaller
    
    logger.info("=" * 70)
    logger.info("STEP 5: PEAK CALLING")
    logger.info("=" * 70)
    
    logger.info(f"Input: {args.input}")
    logger.info(f"Output prefix: {args.output_prefix}")
    logger.info(f"Genome size: {args.genome_size}")
    logger.info(f"Q-value cutoff: {args.qvalue}")
    
    # Create output directory
    output_dir = Path(args.output_prefix).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize peak caller
    peak_caller = PeakCaller(
        genome_size=args.genome_size,
        qvalue_cutoff=args.qvalue,
        keep_dup=args.keep_dup,
        build_model=not args.no_model,
        conda_env=args.conda_env if not args.no_conda else None
    )
    
    # Run peak calling
    stats = peak_caller.call_peaks(args.input, args.output_prefix, input_format=args.format)
    
    logger.info(f"Peak calling complete: {stats.get('num_peaks', 0):,} peaks")
    return 0


def cmd_call_loops(args):
    """Step 6: Call significant chromatin loops."""
    from .loop_calling import PreClusterer, AnchorClusterer, StatisticalSignificance
    
    logger.info("=" * 70)
    logger.info("STEP 6: LOOP CALLING")
    logger.info("=" * 70)
    
    logger.info(f"iPET file: {args.ipet_file}")
    logger.info(f"Output prefix: {args.output_prefix}")
    logger.info(f"Extension length: {args.extension}bp")
    logger.info(f"iPET threshold: {args.ipet_threshold}")
    logger.info(f"FDR cutoff: {args.fdr_cutoff}")
    
    # Create output directory
    output_dir = Path(args.output_prefix).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 6.1: Pre-clustering
    logger.info("\n--- Step 6.1: Pre-clustering ---")
    pre_clusterer = PreClusterer(extension_length=args.extension)
    precluster_stats = pre_clusterer.pre_cluster(
        args.ipet_file,
        f"{args.output_prefix}.preclustered"
    )
    
    # Step 6.2: Anchor clustering
    logger.info("\n--- Step 6.2: Anchor clustering ---")
    anchor_clusterer = AnchorClusterer()
    cluster_stats = anchor_clusterer.cluster_anchors(
        precluster_stats['output_file'],
        f"{args.output_prefix}.clusters.txt"
    )
    
    # Step 6.3: Statistical significance
    logger.info("\n--- Step 6.3: Statistical significance ---")
    stat_sig = StatisticalSignificance(
        ipet_count_threshold=args.ipet_threshold,
        pvalue_cutoff=args.fdr_cutoff,
        extension_length=args.extension
    )
    sig_stats = stat_sig.calculate_significance(
        f"{args.output_prefix}.clusters.txt",
        args.ipet_file,
        f"{args.output_prefix}.loops"
    )
    
    logger.info(f"\nLoop calling complete:")
    logger.info(f"  Pre-clusters: {precluster_stats['num_clusters']:,}")
    logger.info(f"  Anchor clusters: {cluster_stats['num_anchor_clusters']:,}")
    logger.info(f"  Significant loops: {sig_stats['num_significant_loops']:,}")
    logger.info(f"  FDR < 0.05: {sig_stats['num_fdr_005']:,}")
    logger.info(f"  FDR < 0.01: {sig_stats['num_fdr_001']:,}")
    return 0


def cmd_generate_sites(args):
    """Generate restriction site file from genome FASTA."""
    from .restriction_sites import RestrictionSiteGenerator
    
    logger.info("=" * 70)
    logger.info("RESTRICTION SITE GENERATION")
    logger.info("=" * 70)
    
    logger.info(f"Genome: {args.genome}")
    logger.info(f"Enzyme: {args.enzyme}")
    logger.info(f"Output: {args.output}")
    
    # Create output directory
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator
    generator = RestrictionSiteGenerator(
        enzyme=args.enzyme,
        min_frag_size=args.min_size,
        max_frag_size=args.max_size
    )
    
    # Generate sites
    stats = generator.generate_sites(args.genome, args.output)
    
    logger.info(f"Generated {stats['total_fragments']:,} restriction sites")
    return 0


def cmd_run(args):
    """Run the complete pipeline."""
    logger.info("=" * 70)
    logger.info("CHR3D COMPLETE PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Mode: {args.mode.upper()}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Keep intermediates: {args.keep_intermediates}")
    
    # Validate mode-specific requirements
    if args.mode in ['chiapet', 'hichip'] and not args.linker_a:
        logger.error(f"--linker-a is required for {args.mode} mode")
        return 1
    if args.mode == 'hichip' and not args.restriction_sites:
        logger.error("--restriction-sites is required for hichip mode")
        return 1
    if args.mode == 'hic' and not args.chrom_sizes:
        logger.error("--chrom-sizes is required for hic mode")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Route to appropriate pipeline
    if args.mode == 'hic':
        return _run_hic_pipeline(args, output_dir)
    else:
        return _run_chiapet_hichip_pipeline(args, output_dir)


def _run_hic_pipeline(args, output_dir: Path):
    """Run Hi-C analysis pipeline."""
    from .bulk_hic import HiCPipeline
    
    logger.info("\n" + "=" * 70)
    logger.info("HI-C PIPELINE")
    logger.info("=" * 70)
    
    try:
        # Parse resolutions
        resolutions = [int(r) for r in args.resolution.split(',')]
        
        # Initialize Hi-C pipeline
        hic_pipeline = HiCPipeline(
            genome_index=args.genome_index,
            chrom_sizes=args.chrom_sizes,
            threads=args.threads,
            assembly=args.assembly,
            min_mapq=args.mapping_quality,
            min_distance=args.min_distance,
            resolutions=resolutions
        )
        
        # Note: HiCPipeline uses 'cleanup' parameter (opposite of keep_intermediates)
        stats = hic_pipeline.run(
            fastq1=args.fastq_r1,
            fastq2=args.fastq_r2,
            output_dir=output_dir,
            sample_id=args.sample_id,
            cleanup=not args.keep_intermediates
        )
        
        logger.info("\n" + "=" * 70)
        logger.info("HI-C PIPELINE COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"\nFinal outputs:")
        logger.info(f"  Filtered pairs: {output_dir / 'sample.filtered.pairs.gz'}")
        logger.info(f"  Contact matrix: {output_dir / 'sample.mcool'}")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"Hi-C pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _run_chiapet_hichip_pipeline(args, output_dir: Path):
    """Run ChIA-PET or HiChIP analysis pipeline."""
    logger.info("\n" + "=" * 70)
    logger.info(f"{args.mode.upper()} PIPELINE")
    logger.info("=" * 70)
    
    # Set up step-specific output directories
    step_dirs = {
        'step1': output_dir / 'step1_linker_filtering',
        'step2': output_dir / 'step2_mapping',
        'step3': output_dir / 'step3_purifying',
        'step4': output_dir / 'step4_categorization',
        'step5': output_dir / 'step5_peaks',
        'step6': output_dir / 'step6_loops'
    }
    for d in step_dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Linker Filtering (if linkers provided)
        if args.linker_a:
            from .linker_filtering_v2 import LinkerFilterV2
            
            logger.info("\n" + "=" * 70)
            logger.info("STEP 1: LINKER FILTERING")
            logger.info("=" * 70)
            
            linkers = [args.linker_a]
            if args.linker_b:
                linkers.append(args.linker_b)
            
            linker_filter = LinkerFilterV2(
                linker_sequences=linkers,
                n_threads=args.threads
            )
            
            linker_stats = linker_filter.filter_fastq(
                fastq_r1=args.fastq_r1,
                fastq_r2=args.fastq_r2,
                output_prefix='filtered',
                output_dir=str(step_dirs['step1'])
            )
            
            # Use filtered files for next step
            fastq_r1 = str(step_dirs['step1'] / 'filtered.1_1.R1.fastq')
            fastq_r2 = str(step_dirs['step1'] / 'filtered.1_1.R2.fastq')
        else:
            fastq_r1 = args.fastq_r1
            fastq_r2 = args.fastq_r2
        
        # Step 2: Mapping
        from .mapping_v2 import PETMapper
        
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: GENOMIC MAPPING")
        logger.info("=" * 70)
        
        mapper = PETMapper(
            genome_index=args.genome_index,
            mapping_quality_cutoff=args.mapping_quality,
            n_threads=args.threads,
            use_bwa_mem=args.use_bwa_mem,
            self_ligation_cutoff=args.self_ligation_cutoff
        )
        
        map_stats = mapper.map_linker_filtered_fastq(
            fastq_r1=fastq_r1,
            fastq_r2=fastq_r2,
            output_prefix='mapped',
            output_dir=str(step_dirs['step2'])
        )
        
        bedpe_file = str(step_dirs['step2'] / 'mapped.dedup.bedpe')
        
        # Step 3: Purifying
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: PET PURIFYING")
        logger.info("=" * 70)
        
        if args.mode == 'chiapet':
            from .chiapet_purifying import ChIAPETPurifier
            
            purifier = ChIAPETPurifier(merge_distance=2)
            purify_stats = purifier.purify(bedpe_file, str(step_dirs['step3'] / 'purified'))
            purified_bedpe = str(step_dirs['step3'] / 'purified.merged.bedpe')
        else:
            from .hichip_purifying import HiChIPPurifier
            
            purifier = HiChIPPurifier(restriction_file=args.restriction_sites)
            purify_stats = purifier.remove_same_fragment_pets(
                bedpe_file,
                str(step_dirs['step3'] / 'purified.valid.bedpe'),
                str(step_dirs['step3'] / 'purified.sameres.bedpe')
            )
            purified_bedpe = str(step_dirs['step3'] / 'purified.valid.bedpe')
        
        # Step 4: Categorization
        from .pet_categorization import PETCategorizer
        
        logger.info("\n" + "=" * 70)
        logger.info("STEP 4: PET CATEGORIZATION")
        logger.info("=" * 70)
        
        cutoff = args.self_ligation_cutoff if args.mode == 'chiapet' else 1000
        categorizer = PETCategorizer(self_ligation_cutoff=cutoff, mode=args.mode)
        cat_stats = categorizer.categorize_bedpe(
            purified_bedpe,
            str(step_dirs['step4'] / 'categorized')
        )
        
        ipet_file = str(step_dirs['step4'] / 'categorized.ipet')
        spet_file = str(step_dirs['step4'] / 'categorized.spet')
        
        # Step 5: Peak Calling
        from .peak_calling import PeakCaller
        
        logger.info("\n" + "=" * 70)
        logger.info("STEP 5: PEAK CALLING")
        logger.info("=" * 70)
        
        peak_caller = PeakCaller(
            genome_size=args.genome_size,
            qvalue_cutoff=0.05,
            keep_dup='all'
        )
        peak_stats = peak_caller.call_peaks(
            spet_file,
            str(step_dirs['step5'] / 'peaks')
        )
        
        # Step 6: Loop Calling
        from .loop_calling import PreClusterer, AnchorClusterer, StatisticalSignificance
        
        logger.info("\n" + "=" * 70)
        logger.info("STEP 6: LOOP CALLING")
        logger.info("=" * 70)
        
        # 6.1 Pre-clustering
        pre_clusterer = PreClusterer(extension_length=args.extension_length)
        precluster_stats = pre_clusterer.pre_cluster(
            ipet_file,
            str(step_dirs['step6'] / 'preclustered')
        )
        
        # 6.2 Anchor clustering
        anchor_clusterer = AnchorClusterer()
        cluster_stats = anchor_clusterer.cluster_anchors(
            precluster_stats['output_file'],
            str(step_dirs['step6'] / 'clusters.txt')
        )
        
        # 6.3 Statistical significance
        stat_sig = StatisticalSignificance(
            ipet_count_threshold=args.ipet_threshold,
            pvalue_cutoff=args.fdr_cutoff,
            extension_length=args.extension_length
        )
        sig_stats = stat_sig.calculate_significance(
            str(step_dirs['step6'] / 'clusters.txt'),
            ipet_file,
            str(step_dirs['step6'] / 'loops')
        )
        
        # Cleanup intermediate files if requested
        if not args.keep_intermediates:
            logger.info("\n" + "=" * 70)
            logger.info("CLEANING UP INTERMEDIATE FILES")
            logger.info("=" * 70)
            
            import shutil
            cleanup_patterns = []
            
            # Step 1: Linker filtered files (keep only final outputs)
            if step_dirs['step1'].exists():
                for f in step_dirs['step1'].glob('*.fastq'):
                    cleanup_patterns.append(f)
                logger.info(f"  Removing linker-filtered FASTQ files...")
            
            # Step 2: SAM files, unsorted BAM files
            if step_dirs['step2'].exists():
                for pattern in ['*.sam', '*_unsorted.bam', '*.sai']:
                    for f in step_dirs['step2'].glob(pattern):
                        cleanup_patterns.append(f)
                logger.info(f"  Removing SAM/BAM intermediate files...")
            
            # Step 3: Intermediate purification files
            if step_dirs['step3'].exists():
                for f in step_dirs['step3'].glob('*.sameres.bedpe'):
                    cleanup_patterns.append(f)
                logger.info(f"  Removing purification intermediates...")
            
            # Step 4: Keep categorized files (iPET, sPET, oPET)
            # Step 5: Keep peak files
            # Step 6: Keep only final filtered loops, remove intermediates
            if step_dirs['step6'].exists():
                for pattern in ['*.pre_cluster', '*.pre_cluster.sorted', 'clusters.txt']:
                    for f in step_dirs['step6'].glob(pattern):
                        cleanup_patterns.append(f)
                logger.info(f"  Removing loop calling intermediates...")
            
            # Remove files
            for f in cleanup_patterns:
                try:
                    if f.is_file():
                        f.unlink()
                except Exception as e:
                    logger.warning(f"  Could not remove {f}: {e}")
            
            logger.info(f"  Cleaned up {len(cleanup_patterns)} intermediate files")
            logger.info("=" * 70)
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info(f"{args.mode.upper()} PIPELINE COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"\nFinal outputs:")
        logger.info(f"  iPET file: {ipet_file}")
        logger.info(f"  sPET file: {spet_file}")
        logger.info(f"  Peaks: {step_dirs['step5'] / 'peaks_peaks.narrowPeak'}")
        logger.info(f"  Loops: {step_dirs['step6'] / 'loops.cluster.FDRfiltered.txt'}")
        logger.info(f"\nSummary:")
        logger.info(f"  Total PETs: {cat_stats['total']:,}")
        logger.info(f"  iPETs: {cat_stats['ipet']['count']:,} ({cat_stats['ipet']['percentage']:.1f}%)")
        logger.info(f"  sPETs: {cat_stats['spet']['count']:,} ({cat_stats['spet']['percentage']:.1f}%)")
        logger.info(f"  Peaks: {peak_stats.get('num_peaks', 0):,}")
        logger.info(f"  Significant loops: {sig_stats['num_significant_loops']:,}")
        
        if args.keep_intermediates:
            logger.info(f"\nIntermediate files kept in:")
            for step_name, step_dir in step_dirs.items():
                logger.info(f"  {step_name}: {step_dir}")
        
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"{args.mode.upper()} pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog='chr3d',
        description='Chr3D: Complete Pipeline for ChIA-PET, HiChIP, and Hi-C Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # ChIA-PET Analysis (complete pipeline)
  chr3d run --mode chiapet \\
      --fastq-r1 sample_R1.fastq.gz \\
      --fastq-r2 sample_R2.fastq.gz \\
      --genome-index /path/to/hg38.fa \\
      --linker-a GTTGGATAAG \\
      --linker-b GTTGGAATGT \\
      --output-dir results/ \\
      --threads 24 \\
      --keep-intermediates

  # HiChIP Analysis (complete pipeline)
  chr3d run --mode hichip \\
      --fastq-r1 sample_R1.fastq.gz \\
      --fastq-r2 sample_R2.fastq.gz \\
      --genome-index /path/to/hg38.fa \\
      --linker-a GTTGGATAAG \\
      --restriction-sites /path/to/MboI_sites.bed \\
      --output-dir results/ \\
      --threads 24 \\
      --keep-intermediates

  # Hi-C Analysis (complete pipeline)
  chr3d run --mode hic \\
      --fastq-r1 sample_R1.fastq.gz \\
      --fastq-r2 sample_R2.fastq.gz \\
      --genome-index /path/to/hg38.fa \\
      --chrom-sizes /path/to/hg38.chrom.sizes \\
      --output-dir results/ \\
      --threads 24 \\
      --resolution 1000,5000,10000 \\
      --keep-intermediates

Note: Use --keep-intermediates to retain all intermediate files (SAM, BAM, etc.)
      By default, intermediate files are removed to save disk space.

For more information: https://github.com/rudrajoshi2481/Chr3D
        """
    )
    
    parser.add_argument('--version', action='version', version='%(prog)s 3.2.0')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--log-file', help='Log file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # =========================================================================
    # run - Complete pipeline (MAIN COMMAND)
    # =========================================================================
    run_parser = subparsers.add_parser('run', help='Run complete pipeline')
    run_parser.add_argument('--mode', choices=['chiapet', 'hichip', 'hic'], required=True,
                           help='Analysis mode: chiapet, hichip, or hic')
    # Required inputs
    run_parser.add_argument('--fastq-r1', required=True, help='Input R1 FASTQ file')
    run_parser.add_argument('--fastq-r2', required=True, help='Input R2 FASTQ file')
    run_parser.add_argument('--genome-index', required=True, help='BWA-indexed genome FASTA')
    run_parser.add_argument('--output-dir', required=True, help='Output directory')
    
    # Mode-specific required inputs
    run_parser.add_argument('--linker-a', help='Linker A sequence (required for chiapet/hichip)')
    run_parser.add_argument('--linker-b', help='Linker B sequence (optional for chiapet/hichip)')
    run_parser.add_argument('--restriction-sites', help='Restriction sites BED file (required for hichip)')
    run_parser.add_argument('--chrom-sizes', help='Chromosome sizes file (required for hic)')
    
    # Performance options
    run_parser.add_argument('--threads', type=int, default=24, help='Number of threads (default: 24)')
    run_parser.add_argument('--use-bwa-mem', action='store_true', help='Use BWA-MEM instead of BWA-ALN')
    
    # ChIA-PET/HiChIP parameters
    run_parser.add_argument('--genome-size', default='hs', help='Genome size for MACS3 (default: hs)')
    run_parser.add_argument('--mapping-quality', type=int, default=30, help='Min mapping quality (default: 30)')
    run_parser.add_argument('--self-ligation-cutoff', type=int, default=8000,
                           help='Self-ligation cutoff in bp (default: 8000)')
    run_parser.add_argument('--extension-length', type=int, default=500,
                           help='Tag extension length in bp (default: 500)')
    run_parser.add_argument('--ipet-threshold', type=int, default=2,
                           help='Min iPET count for loops (default: 2)')
    run_parser.add_argument('--fdr-cutoff', type=float, default=0.05, help='FDR cutoff (default: 0.05)')
    
    # Hi-C parameters
    run_parser.add_argument('--resolution', default='1000,5000,10000',
                           help='Resolutions for Hi-C matrices (comma-separated, default: 1000,5000,10000)')
    run_parser.add_argument('--assembly', default='hg38', help='Genome assembly name (default: hg38)')
    run_parser.add_argument('--min-distance', type=int, default=1000,
                           help='Minimum distance for Hi-C pairs (default: 1000)')
    run_parser.add_argument('--sample-id', default='sample', help='Sample identifier (default: sample)')
    
    # Output control
    run_parser.add_argument('--keep-intermediates', action='store_true',
                           help='Keep intermediate files (SAM, unsorted BAM, etc.)')
    run_parser.add_argument('--keep-sam', action='store_true', help='Keep SAM files')
    run_parser.add_argument('--no-dedup', action='store_true', help='Skip PCR duplicate removal')
    
    run_parser.set_defaults(func=cmd_run)
    
    # =========================================================================
    # generate-sites - Utility command for generating restriction sites
    # =========================================================================
    sites_parser = subparsers.add_parser('generate-sites', 
                                         help='Generate restriction fragment sites from genome')
    sites_parser.add_argument('--genome', required=True, help='Genome FASTA file')
    sites_parser.add_argument('--enzyme', required=True, 
                             help='Enzyme name (e.g., MboI, HindIII) or recognition site (e.g., GATC)')
    sites_parser.add_argument('--output', required=True, help='Output BED file')
    sites_parser.add_argument('--min-size', type=int, default=20, 
                             help='Min fragment size (default: 20)')
    sites_parser.add_argument('--max-size', type=int, default=1000000, 
                             help='Max fragment size (default: 1000000)')
    sites_parser.set_defaults(func=cmd_generate_sites)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.log_file)
    
    # Run command
    if args.command is None:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
