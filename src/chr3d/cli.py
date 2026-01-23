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
    from .linker_filtering_v3 import LinkerFilterV3
    
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
    linker_filter = LinkerFilterV3(
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
    if args.mode == 'chiapet' and not args.linker_a:
        logger.error("--linker-a is required for chiapet mode")
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
        
        # Get final outputs from stats
        final_outputs = stats.get('final_outputs', {})
        
        logger.info("\n" + "=" * 70)
        logger.info("HI-C PIPELINE COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"\nFinal outputs (always kept):")
        logger.info(f"  Sorted BAM: {final_outputs.get('sorted_bam', 'N/A')}")
        logger.info(f"  Sorted pairs: {final_outputs.get('sorted_pairs', 'N/A')}")
        logger.info(f"  Filtered pairs: {final_outputs.get('filtered_pairs', 'N/A')}")
        logger.info(f"  Contact matrix (.cool): {final_outputs.get('cool_matrix', 'N/A')}")
        logger.info(f"  Multi-res matrix (.mcool): {final_outputs.get('mcool_matrix', 'N/A')}")
        
        # SAM is always deleted (BAM is kept and can convert back to SAM)
        deleted = stats.get('deleted_files', [])
        if deleted:
            logger.info(f"\nDeleted {len(deleted)} file(s) (SAM always removed, BAM kept)")
        
        if args.keep_intermediates:
            logger.info(f"\nIntermediate files kept (--keep-intermediates):")
            logger.info(f"  Dedup pairs: {output_dir}/pairs/{args.sample_id}.dedup.pairs.gz")
            logger.info(f"\nNote: SAM deleted but BAM kept. Convert back: samtools view -h sorted.bam > output.sam")
        
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"Hi-C pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _write_step_qc(qc_dir: Path, step_name: str, step_num: str, stats: dict, sample_id: str):
    """Write QC stats for a single step."""
    qc_file = qc_dir / f'{sample_id}_{step_num}_{step_name}_qc.txt'
    with open(qc_file, 'w') as f:
        f.write(f"{'=' * 50}\n")
        f.write(f"Step {step_num}: {step_name.upper()} QC\n")
        f.write(f"{'=' * 50}\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for key, value in stats.items():
            if isinstance(value, dict):
                f.write(f"{key}:\n")
                for k, v in value.items():
                    f.write(f"  {k}: {v}\n")
            else:
                f.write(f"{key}: {value}\n")
        f.write(f"{'=' * 50}\n")
    return qc_file


def _run_chiapet_hichip_pipeline(args, output_dir: Path):
    """Run ChIA-PET or HiChIP analysis pipeline."""
    logger.info("\n" + "=" * 70)
    logger.info(f"{args.mode.upper()} PIPELINE")
    logger.info("=" * 70)
    
    # Set up step-specific output directories with proper numbering
    # HiChIP: step01=mapping (no linker filtering)
    # ChIA-PET: step01=linker_filtering, step02=mapping, etc.
    if args.mode == 'hichip':
        step_dirs = {
            'mapping': output_dir / 'step01_mapping',
            'purifying': output_dir / 'step02_purifying',
            'categorization': output_dir / 'step03_categorization',
            'peaks': output_dir / 'step04_peaks',
            'loops': output_dir / 'step05_loops',
            'qc': output_dir / 'qc'
        }
    else:  # chiapet
        step_dirs = {
            'linker_filtering': output_dir / 'step01_linker_filtering',
            'mapping': output_dir / 'step02_mapping',
            'purifying': output_dir / 'step03_purifying',
            'categorization': output_dir / 'step04_categorization',
            'peaks': output_dir / 'step05_peaks',
            'loops': output_dir / 'step06_loops',
            'qc': output_dir / 'qc'
        }
    
    for d in step_dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1 for ChIA-PET: Linker Filtering (HiChIP skips this)
        if args.mode == 'chiapet' and args.linker_a:
            from .linker_filtering_v3 import LinkerFilterV3
            
            logger.info("\n" + "=" * 70)
            logger.info("STEP 01: LINKER FILTERING (ChIA-PET)")
            logger.info("=" * 70)
            
            linkers = [args.linker_a]
            if args.linker_b:
                linkers.append(args.linker_b)
            
            linker_filter = LinkerFilterV3(
                linker_sequences=linkers,
                min_alignment_score=args.min_score,
                min_tag_length=args.min_tag_length,
                max_tag_length=args.max_tag_length,
                n_threads=args.threads
            )
            
            linker_stats = linker_filter.filter_fastq_parallel(
                fastq_r1=args.fastq_r1,
                fastq_r2=args.fastq_r2,
                output_prefix='filtered',
                output_dir=str(step_dirs['linker_filtering'])
            )
            
            # Write QC for linker filtering
            _write_step_qc(step_dirs['qc'], 'linker_filtering', '01', linker_stats, args.sample_id)
            logger.info(f"  QC written to: {step_dirs['qc']}")
            
            # Use filtered files for next step
            fastq_r1 = str(step_dirs['linker_filtering'] / 'filtered.1_1.R1.fastq')
            fastq_r2 = str(step_dirs['linker_filtering'] / 'filtered.1_1.R2.fastq')
        else:
            # HiChIP uses original FASTQs directly (no linker filtering needed)
            fastq_r1 = args.fastq_r1
            fastq_r2 = args.fastq_r2
        
        # Mapping step
        from .mapping_v2 import PETMapper
        
        step_num = '01' if args.mode == 'hichip' else '02'
        logger.info("\n" + "=" * 70)
        logger.info(f"STEP {step_num}: GENOMIC MAPPING")
        logger.info("=" * 70)
        
        # Use BWA-MEM by default, unless --use-bwa-aln is specified
        use_bwa_mem = not getattr(args, 'use_bwa_aln', False)
        
        mapper = PETMapper(
            genome_index=args.genome_index,
            mapping_quality_cutoff=args.mapping_quality,
            n_threads=args.threads,
            use_bwa_mem=use_bwa_mem,
            self_ligation_cutoff=args.self_ligation_cutoff
        )
        
        map_stats = mapper.map_linker_filtered_fastq(
            fastq_r1=fastq_r1,
            fastq_r2=fastq_r2,
            output_prefix='mapped',
            output_dir=str(step_dirs['mapping'])
        )
        
        # Write QC for mapping
        _write_step_qc(step_dirs['qc'], 'mapping', step_num, map_stats, args.sample_id)
        logger.info(f"  QC written to: {step_dirs['qc']}")
        
        bedpe_file = str(step_dirs['mapping'] / 'mapped.dedup.bedpe')
        
        # Purifying step
        step_num = '02' if args.mode == 'hichip' else '03'
        logger.info("\n" + "=" * 70)
        logger.info(f"STEP {step_num}: PET PURIFYING")
        logger.info("=" * 70)
        
        if args.mode == 'chiapet':
            from .chiapet_purifying import ChIAPETPurifier
            
            purifier = ChIAPETPurifier(merge_distance=2)
            purify_stats = purifier.purify(bedpe_file, str(step_dirs['purifying'] / 'purified'))
            purified_bedpe = str(step_dirs['purifying'] / 'purified.merged.bedpe')
        else:
            from .hichip_purifying import HiChIPPurifier
            
            purifier = HiChIPPurifier(restriction_file=args.restriction_sites)
            purify_stats = purifier.remove_same_fragment_pets(
                bedpe_file,
                str(step_dirs['purifying'] / 'purified.valid.bedpe'),
                str(step_dirs['purifying'] / 'purified.sameres.bedpe')
            )
            purified_bedpe = str(step_dirs['purifying'] / 'purified.valid.bedpe')
        
        # Write QC for purifying
        _write_step_qc(step_dirs['qc'], 'purifying', step_num, purify_stats, args.sample_id)
        logger.info(f"  QC written to: {step_dirs['qc']}")
        
        # Categorization step
        from .pet_categorization import PETCategorizer
        
        step_num = '03' if args.mode == 'hichip' else '04'
        logger.info("\n" + "=" * 70)
        logger.info(f"STEP {step_num}: PET CATEGORIZATION")
        logger.info("=" * 70)
        
        cutoff = args.self_ligation_cutoff if args.mode == 'chiapet' else 1000
        categorizer = PETCategorizer(self_ligation_cutoff=cutoff, mode=args.mode)
        cat_stats = categorizer.categorize_bedpe(
            purified_bedpe,
            str(step_dirs['categorization'] / 'categorized')
        )
        
        # Write QC for categorization
        _write_step_qc(step_dirs['qc'], 'categorization', step_num, cat_stats, args.sample_id)
        logger.info(f"  QC written to: {step_dirs['qc']}")
        
        ipet_file = str(step_dirs['categorization'] / 'categorized.ipet')
        spet_file = str(step_dirs['categorization'] / 'categorized.spet')
        
        # Peak Calling step
        from .peak_calling import PeakCaller
        
        step_num = '04' if args.mode == 'hichip' else '05'
        logger.info("\n" + "=" * 70)
        logger.info(f"STEP {step_num}: PEAK CALLING")
        logger.info("=" * 70)
        
        peak_caller = PeakCaller(
            genome_size=args.genome_size,
            qvalue_cutoff=0.05,
            keep_dup='all'
        )
        peak_stats = peak_caller.call_peaks(
            spet_file,
            str(step_dirs['peaks'] / 'peaks')
        )
        
        # Write QC for peak calling
        _write_step_qc(step_dirs['qc'], 'peaks', step_num, peak_stats, args.sample_id)
        logger.info(f"  QC written to: {step_dirs['qc']}")
        
        # Loop Calling step
        from .loop_calling import PreClusterer, AnchorClusterer, StatisticalSignificance
        
        step_num = '05' if args.mode == 'hichip' else '06'
        logger.info("\n" + "=" * 70)
        logger.info(f"STEP {step_num}: LOOP CALLING")
        logger.info("=" * 70)
        
        # 6.1 Pre-clustering
        pre_clusterer = PreClusterer(extension_length=args.extension_length)
        precluster_stats = pre_clusterer.pre_cluster(
            ipet_file,
            str(step_dirs['loops'] / 'preclustered')
        )
        
        # 6.2 Anchor clustering
        anchor_clusterer = AnchorClusterer()
        cluster_stats = anchor_clusterer.cluster_anchors(
            precluster_stats['output_file'],
            str(step_dirs['loops'] / 'clusters.txt')
        )
        
        # 6.3 Statistical significance
        stat_sig = StatisticalSignificance(
            ipet_count_threshold=args.ipet_threshold,
            pvalue_cutoff=args.fdr_cutoff,
            extension_length=args.extension_length
        )
        sig_stats = stat_sig.calculate_significance(
            str(step_dirs['loops'] / 'clusters.txt'),
            ipet_file,
            str(step_dirs['loops'] / 'loops')
        )
        
        # Write QC for loop calling
        loop_qc = {
            'precluster': precluster_stats,
            'anchor_cluster': cluster_stats,
            'significance': sig_stats
        }
        _write_step_qc(step_dirs['qc'], 'loops', step_num, loop_qc, args.sample_id)
        logger.info(f"  QC written to: {step_dirs['qc']}")
        
        # Cleanup intermediate files if requested
        if not args.keep_intermediates:
            logger.info("\n" + "=" * 70)
            logger.info("CLEANING UP INTERMEDIATE FILES")
            logger.info("=" * 70)
            
            import shutil
            cleanup_patterns = []
            
            # Linker filtered files (ChIA-PET only)
            if 'linker_filtering' in step_dirs and step_dirs['linker_filtering'].exists():
                for f in step_dirs['linker_filtering'].glob('*.fastq'):
                    cleanup_patterns.append(f)
                logger.info(f"  Removing linker-filtered FASTQ files...")
            
            # SAM files, unsorted BAM files
            if step_dirs['mapping'].exists():
                for pattern in ['*.sam', '*_unsorted.bam', '*.sai']:
                    for f in step_dirs['mapping'].glob(pattern):
                        cleanup_patterns.append(f)
                logger.info(f"  Removing SAM/BAM intermediate files...")
            
            # Intermediate purification files
            if step_dirs['purifying'].exists():
                for f in step_dirs['purifying'].glob('*.sameres.bedpe'):
                    cleanup_patterns.append(f)
                logger.info(f"  Removing purification intermediates...")
            
            # Loop calling intermediates
            if step_dirs['loops'].exists():
                for pattern in ['*.pre_cluster', '*.pre_cluster.sorted', 'clusters.txt']:
                    for f in step_dirs['loops'].glob(pattern):
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
        
        # Generate QC summary
        logger.info("\n" + "=" * 70)
        logger.info("GENERATING QC STATISTICS")
        logger.info("=" * 70)
        
        qc_summary = {
            'sample_id': args.sample_id,
            'mode': args.mode,
            'mapping': {
                'total_pets': map_stats.get('total_pets', 'N/A'),
                'mapped_pets': map_stats.get('mapped_pets', 'N/A'),
                'unique_pets': map_stats.get('unique_pets', 'N/A'),
                'duplicate_rate': map_stats.get('duplicate_rate', 'N/A'),
            },
            'purification': {
                'total_pets': purify_stats.get('total_pets', 'N/A'),
                'valid_pets': purify_stats.get('valid_pets', 'N/A'),
                'same_fragment_pets': purify_stats.get('same_fragment_pets', 'N/A'),
                'valid_ratio': purify_stats.get('valid_ratio', 'N/A'),
            },
            'categorization': {
                'total': cat_stats.get('total', 0),
                'ipet_count': cat_stats['ipet']['count'],
                'ipet_percentage': cat_stats['ipet']['percentage'],
                'spet_count': cat_stats['spet']['count'],
                'spet_percentage': cat_stats['spet']['percentage'],
                'opet_count': cat_stats['opet']['count'],
                'opet_percentage': cat_stats['opet']['percentage'],
                'cis_percentage': cat_stats.get('cis', {}).get('percentage', 'N/A'),
                'trans_percentage': cat_stats.get('trans', {}).get('percentage', 'N/A'),
            },
            'peaks': {
                'num_peaks': peak_stats.get('num_peaks', 0),
            },
            'loops': {
                'total_clusters': sig_stats.get('num_clusters', 'N/A'),
                'significant_loops': sig_stats.get('num_significant_loops', 0),
            }
        }
        
        # Write QC summary to file
        qc_file = step_dirs['qc'] / f'{args.sample_id}_qc_summary.txt'
        with open(qc_file, 'w') as f:
            f.write(f"{'=' * 70}\n")
            f.write(f"{args.mode.upper()} QC SUMMARY\n")
            f.write(f"{'=' * 70}\n")
            f.write(f"Sample ID: {args.sample_id}\n")
            f.write(f"Mode: {args.mode}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"MAPPING STATISTICS\n")
            f.write(f"-" * 40 + "\n")
            f.write(f"Total PETs: {qc_summary['mapping']['total_pets']}\n")
            f.write(f"Mapped PETs: {qc_summary['mapping']['mapped_pets']}\n")
            f.write(f"Unique PETs: {qc_summary['mapping']['unique_pets']}\n")
            dup_rate = qc_summary['mapping']['duplicate_rate']
            if isinstance(dup_rate, (int, float)):
                f.write(f"Duplicate Rate: {dup_rate*100:.1f}%\n")
            else:
                f.write(f"Duplicate Rate: {dup_rate}\n")
            f.write("\n")
            
            f.write(f"PURIFICATION STATISTICS\n")
            f.write(f"-" * 40 + "\n")
            f.write(f"Total PETs: {qc_summary['purification']['total_pets']}\n")
            f.write(f"Valid PETs: {qc_summary['purification']['valid_pets']}\n")
            f.write(f"Same-fragment PETs: {qc_summary['purification']['same_fragment_pets']}\n")
            valid_ratio = qc_summary['purification']['valid_ratio']
            if isinstance(valid_ratio, (int, float)):
                f.write(f"Valid Ratio: {valid_ratio*100:.1f}%\n")
            else:
                f.write(f"Valid Ratio: {valid_ratio}\n")
            f.write("\n")
            
            f.write(f"CATEGORIZATION STATISTICS\n")
            f.write(f"-" * 40 + "\n")
            f.write(f"Total PETs: {qc_summary['categorization']['total']:,}\n")
            f.write(f"iPETs: {qc_summary['categorization']['ipet_count']:,} ({qc_summary['categorization']['ipet_percentage']:.1f}%)\n")
            f.write(f"sPETs: {qc_summary['categorization']['spet_count']:,} ({qc_summary['categorization']['spet_percentage']:.1f}%)\n")
            f.write(f"oPETs: {qc_summary['categorization']['opet_count']:,} ({qc_summary['categorization']['opet_percentage']:.1f}%)\n")
            f.write(f"Cis Ratio: {qc_summary['categorization']['cis_percentage']}%\n")
            f.write(f"Trans Ratio: {qc_summary['categorization']['trans_percentage']}%\n")
            f.write("\n")
            
            f.write(f"PEAK CALLING STATISTICS\n")
            f.write(f"-" * 40 + "\n")
            f.write(f"Peaks Called: {qc_summary['peaks']['num_peaks']:,}\n")
            f.write("\n")
            
            f.write(f"LOOP CALLING STATISTICS\n")
            f.write(f"-" * 40 + "\n")
            f.write(f"Total Clusters: {qc_summary['loops']['total_clusters']}\n")
            f.write(f"Significant Loops (FDR < {args.fdr_cutoff}): {qc_summary['loops']['significant_loops']:,}\n")
            f.write("\n")
            
            f.write(f"{'=' * 70}\n")
        
        logger.info(f"QC summary written to: {qc_file}")
        
        # Generate comprehensive ChIA-PET quality report
        if args.mode == 'chiapet':
            from .chiapet_qc_report import generate_chiapet_report
            
            logger.info("\n" + "=" * 70)
            logger.info("GENERATING COMPREHENSIVE QUALITY REPORT")
            logger.info("=" * 70)
            
            report_file = step_dirs['qc'] / f'{args.sample_id}_comprehensive_qc_report.txt'
            try:
                report = generate_chiapet_report(
                    qc_dir=str(step_dirs['qc']),
                    sample_id=args.sample_id,
                    output_file=str(report_file),
                    output_dir=str(output_dir),
                    genome=args.assembly if hasattr(args, 'assembly') else 'hg38',
                    self_ligation_cutoff=args.self_ligation_cutoff,
                    extension_length=args.extension_length,
                    threads=args.threads
                )
                logger.info(f"Comprehensive QC report written to: {report_file}")
            except Exception as e:
                logger.warning(f"Could not generate comprehensive report: {e}")
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info(f"{args.mode.upper()} PIPELINE COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"\nFinal outputs:")
        logger.info(f"  iPET file: {ipet_file}")
        logger.info(f"  sPET file: {spet_file}")
        logger.info(f"  Peaks: {step_dirs['peaks'] / 'peaks_peaks.narrowPeak'}")
        logger.info(f"  Loops: {step_dirs['loops'] / 'loops.cluster.FDRfiltered.txt'}")
        logger.info(f"  QC Summary: {qc_file}")
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
    run_parser.add_argument('--use-bwa-mem', action='store_true', default=True, help='Use BWA-MEM (default: True)')
    run_parser.add_argument('--use-bwa-aln', action='store_true', help='Use BWA-ALN instead of BWA-MEM')
    
    # Linker filtering parameters
    run_parser.add_argument('--min-tag-length', type=int, default=18,
                           help='Minimum tag length after linker removal (default: 18)')
    run_parser.add_argument('--max-tag-length', type=int, default=1000,
                           help='Maximum tag length (default: 1000)')
    run_parser.add_argument('--min-score', type=int, default=14,
                           help='Minimum linker alignment score (default: 14)')
    
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
