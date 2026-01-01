#!/usr/bin/env python3
"""
Rowan-PET Command Line Interface

Provides command-line access to all pipeline steps for ChIA-PET and HiChIP analysis.

Usage:
    rowan-pet <command> [options]

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
logger = logging.getLogger('rowan-pet')


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
    logger.info("ROWAN-PET COMPLETE PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
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
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE COMPLETE!")
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
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog='rowan-pet',
        description='Rowan-PET: ChIA-PET and HiChIP Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete ChIA-PET pipeline
  rowan-pet run --mode chiapet --fastq-r1 R1.fq.gz --fastq-r2 R2.fq.gz \\
      --genome-index hg38.fa --linker-a GTTGGATAAG --output-dir results/

  # Run individual steps
  rowan-pet filter-linker --fastq-r1 R1.fq.gz --fastq-r2 R2.fq.gz \\
      --linker-a GTTGGATAAG --output-prefix filtered

  rowan-pet call-loops --ipet-file categorized.ipet --output-prefix loops

For more information, see: https://github.com/rowan-pet/rowan-pet
        """
    )
    
    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--log-file', help='Log file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # =========================================================================
    # run - Complete pipeline
    # =========================================================================
    run_parser = subparsers.add_parser('run', help='Run complete pipeline')
    run_parser.add_argument('--mode', choices=['chiapet', 'hichip'], default='chiapet',
                           help='Analysis mode (default: chiapet)')
    run_parser.add_argument('--fastq-r1', required=True, help='Input R1 FASTQ file')
    run_parser.add_argument('--fastq-r2', required=True, help='Input R2 FASTQ file')
    run_parser.add_argument('--genome-index', required=True, help='BWA genome index')
    run_parser.add_argument('--linker-a', help='Linker A sequence')
    run_parser.add_argument('--linker-b', help='Linker B sequence (optional)')
    run_parser.add_argument('--restriction-sites', help='Restriction sites BED (HiChIP)')
    run_parser.add_argument('--output-dir', required=True, help='Output directory')
    run_parser.add_argument('--threads', type=int, default=4, help='Number of threads')
    run_parser.add_argument('--genome-size', default='hs', help='Genome size for MACS3')
    run_parser.add_argument('--mapping-quality', type=int, default=30, help='Min mapping quality')
    run_parser.add_argument('--self-ligation-cutoff', type=int, default=8000,
                           help='Self-ligation cutoff (bp)')
    run_parser.add_argument('--extension-length', type=int, default=500,
                           help='Tag extension length (bp)')
    run_parser.add_argument('--ipet-threshold', type=int, default=2,
                           help='Min iPET count for loops')
    run_parser.add_argument('--fdr-cutoff', type=float, default=0.05, help='FDR cutoff')
    run_parser.add_argument('--use-bwa-mem', action='store_true', help='Use BWA-MEM')
    run_parser.set_defaults(func=cmd_run)
    
    # =========================================================================
    # filter-linker - Step 1
    # =========================================================================
    filter_parser = subparsers.add_parser('filter-linker', help='Step 1: Filter linker sequences')
    filter_parser.add_argument('--fastq-r1', required=True, help='Input R1 FASTQ file')
    filter_parser.add_argument('--fastq-r2', required=True, help='Input R2 FASTQ file')
    filter_parser.add_argument('--linker-a', required=True, help='Linker A sequence')
    filter_parser.add_argument('--linker-b', help='Linker B sequence (optional)')
    filter_parser.add_argument('--output-prefix', required=True, help='Output prefix')
    filter_parser.add_argument('--output-dir', help='Output directory')
    filter_parser.add_argument('--min-score', type=int, default=14, help='Min alignment score')
    filter_parser.add_argument('--min-tag-length', type=int, default=18, help='Min tag length')
    filter_parser.add_argument('--max-tag-length', type=int, default=1000, help='Max tag length')
    filter_parser.add_argument('--threads', type=int, default=4, help='Number of threads')
    filter_parser.add_argument('--compress', action='store_true', help='Compress output')
    filter_parser.set_defaults(func=cmd_filter_linker)
    
    # =========================================================================
    # map - Step 2
    # =========================================================================
    map_parser = subparsers.add_parser('map', help='Step 2: Map reads to genome')
    map_parser.add_argument('--fastq-r1', required=True, help='Input R1 FASTQ file')
    map_parser.add_argument('--fastq-r2', required=True, help='Input R2 FASTQ file')
    map_parser.add_argument('--genome-index', required=True, help='BWA genome index')
    map_parser.add_argument('--output-prefix', required=True, help='Output prefix')
    map_parser.add_argument('--output-dir', help='Output directory')
    map_parser.add_argument('--mapping-quality', type=int, default=30, help='Min mapping quality')
    map_parser.add_argument('--threads', type=int, default=4, help='Number of threads')
    map_parser.add_argument('--use-bwa-mem', action='store_true', help='Use BWA-MEM')
    map_parser.add_argument('--self-ligation-cutoff', type=int, default=8000,
                           help='Self-ligation cutoff')
    map_parser.add_argument('--keep-sam', action='store_true', help='Keep SAM files')
    map_parser.add_argument('--no-dedup', action='store_true', help='Skip deduplication')
    map_parser.set_defaults(func=cmd_map)
    
    # =========================================================================
    # purify - Step 3
    # =========================================================================
    purify_parser = subparsers.add_parser('purify', help='Step 3: Purify PETs')
    purify_parser.add_argument('--bedpe', required=True, help='Input BEDPE file')
    purify_parser.add_argument('--output-prefix', required=True, help='Output prefix')
    purify_parser.add_argument('--mode', choices=['chiapet', 'hichip'], default='chiapet',
                              help='Analysis mode')
    purify_parser.add_argument('--merge-distance', type=int, default=2,
                              help='Merge distance (ChIA-PET)')
    purify_parser.add_argument('--restriction-sites', help='Restriction sites BED (HiChIP)')
    purify_parser.add_argument('--min-insert-size', type=int, default=1,
                              help='Min insert size (HiChIP)')
    purify_parser.set_defaults(func=cmd_purify)
    
    # =========================================================================
    # categorize - Step 4
    # =========================================================================
    cat_parser = subparsers.add_parser('categorize', help='Step 4: Categorize PETs')
    cat_parser.add_argument('--bedpe', required=True, help='Input BEDPE file')
    cat_parser.add_argument('--output-prefix', required=True, help='Output prefix')
    cat_parser.add_argument('--cutoff', type=int, default=8000, help='Self-ligation cutoff (bp)')
    cat_parser.add_argument('--mode', choices=['chiapet', 'hichip'], default='chiapet',
                           help='Analysis mode')
    cat_parser.set_defaults(func=cmd_categorize)
    
    # =========================================================================
    # call-peaks - Step 5
    # =========================================================================
    peak_parser = subparsers.add_parser('call-peaks', help='Step 5: Call peaks')
    peak_parser.add_argument('--input', required=True, help='Input file (sPET or BAM)')
    peak_parser.add_argument('--output-prefix', required=True, help='Output prefix')
    peak_parser.add_argument('--genome-size', '-g', default='hs', help='Genome size')
    peak_parser.add_argument('--qvalue', '-q', type=float, default=0.05, help='Q-value cutoff')
    peak_parser.add_argument('--keep-dup', default='all', help='Duplicate handling')
    peak_parser.add_argument('--no-model', action='store_true', help='Skip model building')
    peak_parser.add_argument('--format', choices=['auto', 'BAM', 'BED', 'BEDPE'], default='auto',
                            help='Input format')
    peak_parser.add_argument('--conda-env', default='rowan-hic', help='Conda environment')
    peak_parser.add_argument('--no-conda', action='store_true', help='Skip conda')
    peak_parser.set_defaults(func=cmd_call_peaks)
    
    # =========================================================================
    # call-loops - Step 6
    # =========================================================================
    loop_parser = subparsers.add_parser('call-loops', help='Step 6: Call loops')
    loop_parser.add_argument('--ipet-file', required=True, help='Input iPET file')
    loop_parser.add_argument('--output-prefix', required=True, help='Output prefix')
    loop_parser.add_argument('--extension', type=int, default=500, help='Extension length (bp)')
    loop_parser.add_argument('--ipet-threshold', type=int, default=2, help='Min iPET count')
    loop_parser.add_argument('--fdr-cutoff', type=float, default=0.05, help='FDR cutoff')
    loop_parser.set_defaults(func=cmd_call_loops)
    
    # =========================================================================
    # generate-sites - Utility
    # =========================================================================
    sites_parser = subparsers.add_parser('generate-sites', help='Generate restriction sites')
    sites_parser.add_argument('--genome', required=True, help='Genome FASTA file')
    sites_parser.add_argument('--enzyme', required=True, help='Enzyme name or site')
    sites_parser.add_argument('--output', required=True, help='Output BED file')
    sites_parser.add_argument('--min-size', type=int, default=20, help='Min fragment size')
    sites_parser.add_argument('--max-size', type=int, default=1000000, help='Max fragment size')
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
