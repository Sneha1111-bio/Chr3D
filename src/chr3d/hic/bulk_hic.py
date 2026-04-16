"""
Hi-C Analysis Module

This module implements modular Hi-C data processing with standalone classes for each step.
Each class can be used independently or combined into a full pipeline.

Classes:
    - HiCAligner: BWA MEM alignment for Hi-C data
    - HiCSamProcessor: SAM to BAM conversion and sorting
    - HiCPairsProcessor: pairtools parse, sort, dedup, filter
    - HiCMatrixGenerator: cooler contact matrix generation
    - HiCPipeline: Complete pipeline orchestrator
    - HiCQCAnalyzer: Quality control analysis
    - FastqSplitter: Split large FASTQ files for parallel processing

Dependencies:
- BWA (>= 0.7.17)
- SAMtools (>= 1.10)
- pairtools (>= 1.0.0)
- cooler (>= 0.9.0)

Reference: 4DN Hi-C Processing Pipeline
"""

import os
import subprocess
import logging
import glob
import gzip
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime

# Use centralized logging
from ..utils.logging import get_logger
from ..utils.system_info import save_system_info

# Get module logger
logger = get_logger(__name__)


def _run_command(cmd: str, description: str = "") -> subprocess.CompletedProcess:
    """Execute a shell command with logging."""
    if description:
        logger.info(f"  {description}")
    logger.debug(f"  Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                               capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {cmd}")
        logger.error(f"STDERR: {e.stderr}")
        raise


def _check_tool(tool: str) -> bool:
    """Check if a tool is available in PATH."""
    try:
        subprocess.run(['which', tool], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def _format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes ({seconds:.0f}s)"
    else:
        hours = seconds / 3600
        minutes = (seconds % 3600) / 60
        return f"{hours:.1f} hours ({int(hours)}h {int(minutes)}m)"


class FastqSplitter:
    """
    Split large FASTQ files into smaller chunks for parallel processing.
    
    Useful for processing very large Hi-C datasets by splitting into
    manageable chunks that can be processed in parallel.
    
    Example:
        >>> import chr3d as c3d
        >>> 
        >>> splitter = c3d.FastqSplitter(n_chunks=10)
        >>> chunks = splitter.split(
        ...     fastq1="sample_R1.fastq.gz",
        ...     fastq2="sample_R2.fastq.gz",
        ...     output_dir="split_fastq/"
        ... )
        >>> print(f"Created {len(chunks)} chunk pairs")
    """
    
    def __init__(self, n_chunks: int = 10, reads_per_chunk: Optional[int] = None):
        """
        Initialize FASTQ splitter.
        
        Args:
            n_chunks: Number of chunks to split into (default: 10)
            reads_per_chunk: Reads per chunk (overrides n_chunks if set)
        """
        self.n_chunks = n_chunks
        self.reads_per_chunk = reads_per_chunk
        
        logger.info("FastqSplitter initialized")
        logger.info(f"  Chunks: {n_chunks}")
        if reads_per_chunk:
            logger.info(f"  Reads per chunk: {reads_per_chunk}")
    
    def _count_reads(self, fastq_file: str) -> int:
        """Count reads in a FASTQ file."""
        logger.info(f"  Counting reads in {fastq_file}...")
        
        open_func = gzip.open if fastq_file.endswith('.gz') else open
        count = 0
        with open_func(fastq_file, 'rt') as f:
            for _ in f:
                count += 1
        return count // 4  # 4 lines per read
    
    def split(self,
              fastq1: str,
              fastq2: str,
              output_dir: str,
              prefix: str = "chunk") -> List[Tuple[str, str]]:
        """
        Split paired FASTQ files into chunks.
        
        Args:
            fastq1: Path to R1 FASTQ file
            fastq2: Path to R2 FASTQ file
            output_dir: Output directory for chunks
            prefix: Prefix for chunk files (default: 'chunk')
            
        Returns:
            List of tuples (chunk_r1, chunk_r2) paths
        """
        logger.info("=" * 70)
        logger.info("FASTQ SPLITTING")
        logger.info("=" * 70)
        logger.info(f"FASTQ R1: {fastq1}")
        logger.info(f"FASTQ R2: {fastq2}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Count total reads
        total_reads = self._count_reads(fastq1)
        logger.info(f"  Total reads: {total_reads:,}")
        
        # Calculate reads per chunk
        if self.reads_per_chunk:
            reads_per_chunk = self.reads_per_chunk
            n_chunks = (total_reads + reads_per_chunk - 1) // reads_per_chunk
        else:
            n_chunks = self.n_chunks
            reads_per_chunk = (total_reads + n_chunks - 1) // n_chunks
        
        logger.info(f"  Splitting into {n_chunks} chunks ({reads_per_chunk:,} reads each)")
        
        # Split files
        chunks = []
        open_func1 = gzip.open if fastq1.endswith('.gz') else open
        open_func2 = gzip.open if fastq2.endswith('.gz') else open
        
        with open_func1(fastq1, 'rt') as f1, open_func2(fastq2, 'rt') as f2:
            chunk_idx = 0
            read_count = 0
            
            chunk_r1_path = os.path.join(output_dir, f"{prefix}_{chunk_idx:03d}_R1.fastq")
            chunk_r2_path = os.path.join(output_dir, f"{prefix}_{chunk_idx:03d}_R2.fastq")
            chunk_r1 = open(chunk_r1_path, 'w')
            chunk_r2 = open(chunk_r2_path, 'w')
            
            while True:
                # Read one record from each file (4 lines)
                r1_lines = [f1.readline() for _ in range(4)]
                r2_lines = [f2.readline() for _ in range(4)]
                
                if not r1_lines[0]:  # EOF
                    break
                
                # Write to current chunk
                chunk_r1.writelines(r1_lines)
                chunk_r2.writelines(r2_lines)
                read_count += 1
                
                # Check if chunk is full
                if read_count >= reads_per_chunk:
                    chunk_r1.close()
                    chunk_r2.close()
                    chunks.append((chunk_r1_path, chunk_r2_path))
                    
                    chunk_idx += 1
                    read_count = 0
                    
                    chunk_r1_path = os.path.join(output_dir, f"{prefix}_{chunk_idx:03d}_R1.fastq")
                    chunk_r2_path = os.path.join(output_dir, f"{prefix}_{chunk_idx:03d}_R2.fastq")
                    chunk_r1 = open(chunk_r1_path, 'w')
                    chunk_r2 = open(chunk_r2_path, 'w')
            
            # Close last chunk if it has reads
            if read_count > 0:
                chunk_r1.close()
                chunk_r2.close()
                chunks.append((chunk_r1_path, chunk_r2_path))
            else:
                chunk_r1.close()
                chunk_r2.close()
                os.remove(chunk_r1_path)
                os.remove(chunk_r2_path)
        
        logger.info(f"  Created {len(chunks)} chunk pairs")
        
        return chunks


class HiCAligner:
    """
    Hi-C alignment using BWA MEM with Hi-C specific parameters.
    
    Uses BWA MEM with -SP5M flags optimized for Hi-C chimeric reads.
    
    Example:
        >>> import chr3d as c3d
        >>> 
        >>> aligner = c3d.HiCAligner(
        ...     genome_index="/path/to/hg38.fa",
        ...     threads=24
        ... )
        >>> stats = aligner.align(
        ...     fastq1="sample_R1.fastq.gz",
        ...     fastq2="sample_R2.fastq.gz",
        ...     output_sam="aligned.sam"
        ... )
    """
    
    def __init__(self,
                 genome_index: str,
                 threads: int = 1):
        """
        Initialize Hi-C aligner.
        
        Args:
            genome_index: Path to BWA-indexed genome FASTA
            threads: Number of threads for BWA (default: 1)
        """
        self.genome_index = genome_index
        self.threads = threads
        
        # Validate genome index
        self._validate_index()
        
        # Check BWA is available
        if not _check_tool('bwa'):
            raise RuntimeError("BWA not found. Install with: conda install -c bioconda bwa")
        
        logger.info("HiCAligner initialized")
        logger.info(f"  Genome index: {genome_index}")
        logger.info(f"  Threads: {threads}")
    
    def _validate_index(self):
        """Validate BWA index files exist."""
        if os.path.isdir(self.genome_index):
            amb_files = [f for f in os.listdir(self.genome_index) if f.endswith('.amb')]
            if not amb_files:
                raise ValueError(f"No BWA index files found in: {self.genome_index}")
            base_name = amb_files[0][:-4]
            self.genome_index = os.path.join(self.genome_index, base_name)
        
        bwa_suffixes = ['.amb', '.ann', '.bwt', '.pac', '.sa']
        missing = [f"{self.genome_index}{s}" for s in bwa_suffixes 
                   if not os.path.exists(f"{self.genome_index}{s}")]
        if missing:
            raise ValueError(f"Missing BWA index files: {missing}")
    
    def align(self,
              fastq1: str,
              fastq2: str,
              output_sam: str,
              stats_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Run BWA MEM alignment for Hi-C data.
        
        Args:
            fastq1: Path to R1 FASTQ file
            fastq2: Path to R2 FASTQ file
            output_sam: Path to output SAM file
            stats_file: Optional path to save alignment stats
            
        Returns:
            Dictionary with alignment statistics
        """
        logger.info("=" * 70)
        logger.info("Hi-C ALIGNMENT (BWA MEM)")
        logger.info("=" * 70)
        logger.info(f"FASTQ R1: {fastq1}")
        logger.info(f"FASTQ R2: {fastq2}")
        logger.info(f"Output: {output_sam}")
        
        # Create output directory
        os.makedirs(os.path.dirname(output_sam) or '.', exist_ok=True)
        
        # BWA MEM with Hi-C specific parameters
        # -S: Skip mate rescue
        # -P: Skip pairing
        # -5: Take alignment with smallest coordinate as primary
        # -M: Mark shorter split hits as secondary
        stats_redirect = f"2> {stats_file}" if stats_file else "2>&1"
        cmd = f"bwa mem -SP5M -t {self.threads} {self.genome_index} {fastq1} {fastq2} > {output_sam} {stats_redirect}"
        
        _run_command(cmd, "Running BWA MEM alignment...")
        
        sam_size = os.path.getsize(output_sam) if os.path.exists(output_sam) else 0
        logger.info(f"  Output SAM: {output_sam} ({sam_size / 1e9:.2f} GB)")
        
        return {
            'output_sam': output_sam,
            'stats_file': stats_file,
            'sam_size_bytes': sam_size
        }


class HiCSamProcessor:
    """
    SAM/BAM processing for Hi-C data using samtools.
    
    Converts SAM to BAM and sorts by read name (required for pairtools).
    
    Example:
        >>> import chr3d as c3d
        >>> 
        >>> processor = c3d.HiCSamProcessor(threads=24)
        >>> stats = processor.process(
        ...     input_sam="aligned.sam",
        ...     output_bam="sorted.bam"
        ... )
    """
    
    def __init__(self, threads: int = 1):
        """
        Initialize SAM processor.
        
        Args:
            threads: Number of threads for samtools (default: 1)
        """
        self.threads = threads
        
        if not _check_tool('samtools'):
            raise RuntimeError("samtools not found. Install with: conda install -c bioconda samtools")
        
        logger.info("HiCSamProcessor initialized")
        logger.info(f"  Threads: {threads}")
    
    def process(self,
                input_sam: str,
                output_bam: str,
                stats_file: Optional[str] = None,
                keep_unsorted: bool = False) -> Dict[str, Any]:
        """
        Convert SAM to sorted BAM.
        
        Args:
            input_sam: Path to input SAM file
            output_bam: Path to output sorted BAM file
            stats_file: Optional path to save BAM stats
            keep_unsorted: Keep unsorted BAM file (default: False)
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info("=" * 70)
        logger.info("SAM/BAM PROCESSING")
        logger.info("=" * 70)
        logger.info(f"Input SAM: {input_sam}")
        logger.info(f"Output BAM: {output_bam}")
        
        os.makedirs(os.path.dirname(output_bam) or '.', exist_ok=True)
        
        # Temp unsorted BAM
        unsorted_bam = output_bam.replace('.bam', '.unsorted.bam')
        
        # Convert SAM to BAM
        cmd = f"samtools view -@ {self.threads} -bS {input_sam} > {unsorted_bam}"
        _run_command(cmd, "Converting SAM to BAM...")
        
        # Sort by read name (required for pairtools)
        cmd = f"samtools sort -@ {self.threads} -n -o {output_bam} {unsorted_bam}"
        _run_command(cmd, "Sorting BAM by read name...")
        
        # Generate stats if requested
        if stats_file:
            os.makedirs(os.path.dirname(stats_file) or '.', exist_ok=True)
            cmd = f"samtools stats -@ {self.threads} {output_bam} > {stats_file}"
            _run_command(cmd, "Generating BAM statistics...")
        
        # Cleanup unsorted BAM
        if not keep_unsorted and os.path.exists(unsorted_bam):
            os.remove(unsorted_bam)
        
        bam_size = os.path.getsize(output_bam) if os.path.exists(output_bam) else 0
        logger.info(f"  Output BAM: {output_bam} ({bam_size / 1e9:.2f} GB)")
        
        return {
            'output_bam': output_bam,
            'stats_file': stats_file,
            'bam_size_bytes': bam_size
        }


class HiCPairsProcessor:
    """
    Hi-C pairs processing using pairtools.
    
    Provides methods for each pairtools step:
    - parse: Convert BAM to pairs format
    - sort: Sort pairs by genomic position
    - dedup: Remove PCR duplicates
    - filter: Filter valid pair types
    
    Example:
        >>> import chr3d as c3d
        >>> 
        >>> pairs = c3d.HiCPairsProcessor(
        ...     chrom_sizes="/path/to/hg38.chrom.sizes",
        ...     assembly="hg38",
        ...     threads=24
        ... )
        >>> 
        >>> # Run individual steps
        >>> pairs.parse(input_bam="sorted.bam", output_pairs="parsed.pairs.gz")
        >>> pairs.sort(input_pairs="parsed.pairs.gz", output_pairs="sorted.pairs.gz")
        >>> pairs.dedup(input_pairs="sorted.pairs.gz", output_pairs="dedup.pairs.gz")
        >>> pairs.filter(input_pairs="dedup.pairs.gz", output_pairs="filtered.pairs.gz")
        >>> 
        >>> # Or run all steps at once
        >>> stats = pairs.process_all(input_bam="sorted.bam", output_prefix="sample")
    """
    
    def __init__(self,
                 chrom_sizes: str,
                 assembly: str = 'hg38',
                 threads: int = 1,
                 fragment_bed: Optional[str] = None):
        """
        Initialize pairs processor.
        
        Args:
            chrom_sizes: Path to chromosome sizes file
            assembly: Genome assembly name (default: 'hg38')
            threads: Number of threads (default: 1)
            fragment_bed: Path to restriction fragment BED file for fragment-aware
                          pair parsing (enables walk rescue). If None, uses
                          chrom_sizes for position-based parsing (default: None)
        """
        self.chrom_sizes = chrom_sizes
        self.assembly = assembly
        self.threads = threads
        self.fragment_bed = fragment_bed
        
        if not os.path.exists(chrom_sizes):
            raise ValueError(f"Chromosome sizes file not found: {chrom_sizes}")
        
        if not _check_tool('pairtools'):
            raise RuntimeError("pairtools not found. Install with: conda install -c bioconda pairtools")
        
        logger.info("HiCPairsProcessor initialized")
        logger.info(f"  Chromosome sizes: {chrom_sizes}")
        logger.info(f"  Assembly: {assembly}")
        logger.info(f"  Threads: {threads}")
        logger.info(f"  Fragment BED: {fragment_bed or 'none (position-based)'}") 
    
    def parse(self,
              input_bam: str,
              output_pairs: str,
              stats_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse BAM to pairs format.
        
        Args:
            input_bam: Path to sorted BAM file
            output_pairs: Path to output pairs file (.pairs.gz)
            stats_file: Optional path to save parsing stats
            
        Returns:
            Dictionary with parsing statistics
        """
        logger.info("PAIRTOOLS PARSE")
        logger.info(f"  Input: {input_bam}")
        logger.info(f"  Output: {output_pairs}")
        
        os.makedirs(os.path.dirname(output_pairs) or '.', exist_ok=True)
        
        stats_opt = f"--output-stats {stats_file}" if stats_file else ""
        chroms_src = self.fragment_bed if self.fragment_bed else self.chrom_sizes
        walks_opt  = "--walks-policy all" if self.fragment_bed else ""
        cmd = f"""pairtools parse \
            --assembly {self.assembly} \
            --chroms-path {chroms_src} \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {output_pairs} \
            {stats_opt} \
            {walks_opt} \
            {input_bam}"""
        
        _run_command(cmd)
        
        return {'output_pairs': output_pairs, 'stats_file': stats_file}
    
    def sort(self,
             input_pairs: str,
             output_pairs: str,
             tmp_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Sort pairs by genomic position.
        
        Args:
            input_pairs: Path to input pairs file
            output_pairs: Path to output sorted pairs file
            tmp_dir: Temporary directory for sorting
            
        Returns:
            Dictionary with sorting statistics
        """
        logger.info("PAIRTOOLS SORT")
        logger.info(f"  Input: {input_pairs}")
        logger.info(f"  Output: {output_pairs}")
        
        os.makedirs(os.path.dirname(output_pairs) or '.', exist_ok=True)
        
        tmp_opt = f"--tmpdir {tmp_dir}" if tmp_dir else ""
        cmd = f"""pairtools sort \
            {tmp_opt} \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {output_pairs} \
            {input_pairs}"""
        
        _run_command(cmd)
        
        return {'output_pairs': output_pairs}
    
    def dedup(self,
              input_pairs: str,
              output_pairs: str,
              stats_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove PCR duplicates.
        
        Args:
            input_pairs: Path to sorted pairs file
            output_pairs: Path to output deduplicated pairs file
            stats_file: Optional path to save dedup stats
            
        Returns:
            Dictionary with deduplication statistics
        """
        logger.info("PAIRTOOLS DEDUP")
        logger.info(f"  Input: {input_pairs}")
        logger.info(f"  Output: {output_pairs}")
        
        os.makedirs(os.path.dirname(output_pairs) or '.', exist_ok=True)
        
        stats_opt = f"--output-stats {stats_file}" if stats_file else ""
        cmd = f"""pairtools dedup \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {output_pairs} \
            {stats_opt} \
            --mark-dups \
            {input_pairs}"""
        
        _run_command(cmd)
        
        return {'output_pairs': output_pairs, 'stats_file': stats_file}
    
    def filter(self,
               input_pairs: str,
               output_pairs: str,
               pair_types: List[str] = None) -> Dict[str, Any]:
        """
        Filter pairs by pair type.
        
        Args:
            input_pairs: Path to deduplicated pairs file
            output_pairs: Path to output filtered pairs file
            pair_types: List of pair types to keep (default: ['UU', 'UR', 'RU'])
            
        Returns:
            Dictionary with filtering statistics
        """
        logger.info("PAIRTOOLS SELECT (FILTER)")
        logger.info(f"  Input: {input_pairs}")
        logger.info(f"  Output: {output_pairs}")
        
        os.makedirs(os.path.dirname(output_pairs) or '.', exist_ok=True)
        
        if pair_types is None:
            pair_types = ['UU', 'UR', 'RU']
        
        filter_expr = ' or '.join([f'(pair_type == "{pt}")' for pt in pair_types])
        cmd = f"""pairtools select '{filter_expr}' -o {output_pairs} {input_pairs}"""
        
        _run_command(cmd)
        
        pairs_size = os.path.getsize(output_pairs) if os.path.exists(output_pairs) else 0
        logger.info(f"  Output: {output_pairs} ({pairs_size / 1e6:.2f} MB)")
        
        return {'output_pairs': output_pairs, 'pairs_size_bytes': pairs_size}
    
    def process_all(self,
                    input_bam: str,
                    output_dir: str,
                    prefix: str = "sample",
                    cleanup: bool = True) -> Dict[str, Any]:
        """
        Run all pairtools steps in sequence.
        
        Args:
            input_bam: Path to sorted BAM file
            output_dir: Output directory
            prefix: Output file prefix (default: 'sample')
            cleanup: Remove intermediate files (default: True)
            
        Returns:
            Dictionary with all processing statistics
        """
        logger.info("=" * 70)
        logger.info("Hi-C PAIRS PROCESSING (ALL STEPS)")
        logger.info("=" * 70)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Parse
        parsed = os.path.join(output_dir, f"{prefix}.parsed.pairs.gz")
        parse_stats = os.path.join(output_dir, f"{prefix}.parse.stats")
        self.parse(input_bam, parsed, parse_stats)
        
        # Step 2: Sort
        sorted_pairs = os.path.join(output_dir, f"{prefix}.sorted.pairs.gz")
        self.sort(parsed, sorted_pairs, output_dir)
        
        # Step 3: Dedup
        dedup_pairs = os.path.join(output_dir, f"{prefix}.dedup.pairs.gz")
        dedup_stats = os.path.join(output_dir, f"{prefix}.dedup.stats")
        self.dedup(sorted_pairs, dedup_pairs, dedup_stats)
        
        # Step 4: Filter
        filtered_pairs = os.path.join(output_dir, f"{prefix}.filtered.pairs.gz")
        self.filter(dedup_pairs, filtered_pairs)
        
        # Cleanup intermediate files
        if cleanup:
            for f in [parsed]:
                if os.path.exists(f):
                    os.remove(f)
        
        return {
            'sorted_pairs': sorted_pairs,
            'dedup_pairs': dedup_pairs,
            'filtered_pairs': filtered_pairs,
            'parse_stats': parse_stats,
            'dedup_stats': dedup_stats
        }


class HiCMatrixGenerator:
    """
    Contact matrix generation using cooler.
    
    Creates .cool and multi-resolution .mcool files from pairs.
    
    Example:
        >>> import chr3d as c3d
        >>> 
        >>> matrix = c3d.HiCMatrixGenerator(
        ...     chrom_sizes="/path/to/hg38.chrom.sizes",
        ...     assembly="hg38",
        ...     threads=24
        ... )
        >>> 
        >>> # Create contact matrix
        >>> stats = matrix.create(
        ...     input_pairs="filtered.pairs.gz",
        ...     output_cool="sample.cool"
        ... )
        >>> 
        >>> # Create multi-resolution matrix
        >>> matrix.zoomify(
        ...     input_cool="sample.cool",
        ...     output_mcool="sample.mcool",
        ...     resolutions=[1000, 5000, 10000, 25000, 50000, 100000]
        ... )
    """
    
    def __init__(self,
                 chrom_sizes: str,
                 assembly: str = 'hg38',
                 threads: int = 1):
        """
        Initialize matrix generator.
        
        Args:
            chrom_sizes: Path to chromosome sizes file
            assembly: Genome assembly name (default: 'hg38')
            threads: Number of threads (default: 1)
        """
        self.chrom_sizes = chrom_sizes
        self.assembly = assembly
        self.threads = threads
        
        if not os.path.exists(chrom_sizes):
            raise ValueError(f"Chromosome sizes file not found: {chrom_sizes}")
        
        if not _check_tool('cooler'):
            raise RuntimeError("cooler not found. Install with: conda install -c bioconda cooler")
        
        logger.info("HiCMatrixGenerator initialized")
        logger.info(f"  Chromosome sizes: {chrom_sizes}")
        logger.info(f"  Assembly: {assembly}")
        logger.info(f"  Threads: {threads}")
    
    def create(self,
               input_pairs: str,
               output_cool: str,
               resolution: int = 1000) -> Dict[str, Any]:
        """
        Create contact matrix from pairs.
        
        Args:
            input_pairs: Path to filtered pairs file
            output_cool: Path to output .cool file
            resolution: Matrix resolution in bp (default: 1000)
            
        Returns:
            Dictionary with matrix statistics
        """
        logger.info("COOLER CLOAD (CREATE MATRIX)")
        logger.info(f"  Input: {input_pairs}")
        logger.info(f"  Output: {output_cool}")
        logger.info(f"  Resolution: {resolution}bp")
        
        os.makedirs(os.path.dirname(output_cool) or '.', exist_ok=True)
        
        cmd = f"""cooler cload pairs \
            -c1 2 -p1 3 -c2 4 -p2 5 \
            --assembly {self.assembly} \
            {self.chrom_sizes}:{resolution} \
            {input_pairs} \
            {output_cool}"""
        
        _run_command(cmd)
        
        cool_size = os.path.getsize(output_cool) if os.path.exists(output_cool) else 0
        logger.info(f"  Output: {output_cool} ({cool_size / 1e6:.2f} MB)")
        
        # Get number of contacts from cool file
        num_contacts = 0
        try:
            import cooler
            c = cooler.Cooler(output_cool)
            num_contacts = c.info.get('nnz', 0)
        except Exception:
            pass
        
        return {'output_cool': output_cool, 'cool_size_bytes': cool_size, 'resolution': resolution, 'num_contacts': num_contacts}
    
    def balance(self,
                input_cool: str,
                max_iters: int = 200,
                cis_only: bool = True) -> Dict[str, Any]:
        """
        Balance contact matrix.
        
        Args:
            input_cool: Path to .cool file
            max_iters: Maximum iterations (default: 200)
            cis_only: Only balance cis contacts (default: True)
            
        Returns:
            Dictionary with balancing statistics
        """
        logger.info("COOLER BALANCE")
        logger.info(f"  Input: {input_cool}")
        
        cis_opt = "--cis-only" if cis_only else ""
        cmd = f"""cooler balance --force \
            --max-iters {max_iters} \
            --mad-max 5 \
            --min-nnz 5 \
            --ignore-diags 3 \
            --tol 1e-4 \
            {cis_opt} \
            {input_cool}"""
        
        _run_command(cmd)
        
        return {'balanced': True}
    
    def zoomify(self,
                input_cool: str,
                output_mcool: str,
                resolutions: List[int] = None) -> Dict[str, Any]:
        """
        Create multi-resolution .mcool file.
        
        Args:
            input_cool: Path to .cool file
            output_mcool: Path to output .mcool file
            resolutions: List of resolutions in bp
            
        Returns:
            Dictionary with zoomify statistics
        """
        logger.info("COOLER ZOOMIFY")
        logger.info(f"  Input: {input_cool}")
        logger.info(f"  Output: {output_mcool}")
        
        if resolutions is None:
            resolutions = [1000, 5000, 10000, 25000, 50000, 100000]
        
        logger.info(f"  Resolutions: {resolutions}")
        
        resolutions_str = ','.join(map(str, resolutions))
        cmd = f"cooler zoomify --balance -n {self.threads} --resolutions {resolutions_str} {input_cool} -o {output_mcool}"
        
        _run_command(cmd)
        
        mcool_size = os.path.getsize(output_mcool) if os.path.exists(output_mcool) else 0
        logger.info(f"  Output: {output_mcool} ({mcool_size / 1e6:.2f} MB)")
        
        return {'output_mcool': output_mcool, 'mcool_size_bytes': mcool_size, 'resolutions': resolutions}


class HiCPipeline:
    """
    Complete Hi-C data processing pipeline orchestrator.
    
    This class combines all Hi-C processing steps into a single pipeline.
    For more control, use the individual step classes directly:
    - HiCAligner: BWA MEM alignment
    - HiCSamProcessor: SAM/BAM processing
    - HiCPairsProcessor: pairtools processing
    - HiCMatrixGenerator: cooler matrix generation
    
    Example:
        >>> import chr3d as c3d
        >>> 
        >>> # Initialize pipeline
        >>> hic = c3d.HiCPipeline(
        ...     genome_index="/path/to/hg38.fa",
        ...     chrom_sizes="/path/to/hg38.chrom.sizes",
        ...     threads=24
        ... )
        >>> 
        >>> # Run full pipeline
        >>> stats = hic.run(
        ...     fastq1="sample_R1.fastq.gz",
        ...     fastq2="sample_R2.fastq.gz",
        ...     output_dir="results/",
        ...     sample_id="sample1"
        ... )
    """
    
    # Required external tools
    REQUIRED_TOOLS = ['bwa', 'samtools', 'pairtools', 'cooler']
    
    def __init__(self,
                 genome_index: str,
                 chrom_sizes: str,
                 threads: int = 1,
                 assembly: str = 'hg38',
                 min_mapq: int = 30,
                 min_distance: int = 1000,
                 resolutions: Optional[List[int]] = None,
                 n_splits: int = 0,
                 call_tads: bool = True,
                 tad_windows: Optional[List[int]] = None,
                 call_loops: bool = True,
                 loop_fdr: float = 0.1,
                 call_compartments: bool = True,
                 compartment_phasing_track: Optional[str] = None,
                 fragment_bed: Optional[str] = None):
        """
        Initialize the Hi-C pipeline.
        
        Args:
            genome_index: Path to BWA-indexed genome FASTA
            chrom_sizes: Path to chromosome sizes file
            threads: Number of threads for parallel processing (default: 1)
            assembly: Genome assembly name (default: 'hg38')
            min_mapq: Minimum mapping quality (default: 30)
            min_distance: Minimum pair distance in bp (default: 1000)
            resolutions: List of matrix resolutions in bp 
                        (default: [1000, 5000, 10000, 25000, 50000, 100000])
            n_splits: Split FASTQ into N chunks for parallel alignment; 0 = no splitting (default: 0)
            call_tads: Run TAD/insulation calling after matrix generation (default: True)
            tad_windows: Window sizes in bp for insulation scoring (default: library defaults)
            call_loops: Run loop calling after matrix generation (default: True)
            loop_fdr: FDR threshold for loop significance (default: 0.1)
            call_compartments: Run A/B compartment calling (eigs_cis) after matrix generation (default: True)
            compartment_phasing_track: Path to BED file (chrom,start,end,value) for phasing E1 sign,
                                       e.g. gene density track (default: None — sign unoriented)
            fragment_bed: Path to restriction fragment BED (from chr3d digest). Enables
                          fragment-aware pairtools parse with walk rescue. (default: None)
        """
        self.genome_index = genome_index
        self.chrom_sizes = chrom_sizes
        self.threads = threads
        self.assembly = assembly
        self.min_mapq = min_mapq
        self.min_distance = min_distance
        self.resolutions = resolutions or [1000, 5000, 10000, 25000, 50000, 100000]
        self.n_splits = n_splits
        self.call_tads = call_tads
        self.tad_windows = tad_windows
        self.call_loops = call_loops
        self.loop_fdr = loop_fdr
        self.call_compartments = call_compartments
        self.compartment_phasing_track = compartment_phasing_track
        self.fragment_bed = fragment_bed
        
        # Validate inputs
        self._validate_inputs()
        self._check_dependencies()
        
        logger.info("=" * 70)
        logger.info("Hi-C PIPELINE INITIALIZED")
        logger.info("=" * 70)
        logger.info(f"Genome index: {genome_index}")
        logger.info(f"Chromosome sizes: {chrom_sizes}")
        logger.info(f"Threads: {threads}")
        logger.info(f"Assembly: {assembly}")
        logger.info(f"Min MAPQ: {min_mapq}")
        logger.info(f"Min distance: {min_distance}")
        logger.info(f"Resolutions: {self.resolutions}")
        logger.info(f"Splits: {n_splits}")
        logger.info(f"Call TADs: {call_tads}")
        logger.info(f"Call loops: {call_loops}")
        logger.info(f"Call compartments: {call_compartments}")
    
    def _validate_inputs(self):
        """Validate input files exist."""
        # Check genome index
        if os.path.isdir(self.genome_index):
            # Find index files in directory
            amb_files = [f for f in os.listdir(self.genome_index) if f.endswith('.amb')]
            if not amb_files:
                raise ValueError(f"No BWA index files found in: {self.genome_index}")
            base_name = amb_files[0][:-4]
            self.genome_index = os.path.join(self.genome_index, base_name)
        
        # Check BWA index files exist (try both standard and .64 suffix)
        bwa_suffixes = ['.amb', '.ann', '.bwt', '.pac', '.sa']
        missing = []
        for s in bwa_suffixes:
            standard = f"{self.genome_index}{s}"
            with_64 = f"{self.genome_index}.64{s}"
            if not os.path.exists(standard) and not os.path.exists(with_64):
                missing.append(standard)
        if missing:
            raise ValueError(f"Missing BWA index files: {missing}")
        
        # Check chrom sizes
        if not os.path.exists(self.chrom_sizes):
            raise ValueError(f"Chromosome sizes file not found: {self.chrom_sizes}")
    
    def _check_dependencies(self):
        """Check if required external tools are available."""
        missing = []
        for tool in self.REQUIRED_TOOLS:
            try:
                subprocess.run(['which', tool], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                missing.append(tool)
        
        if missing:
            raise RuntimeError(
                f"Required tools not found: {missing}\n"
                f"Install with: conda install -c bioconda {' '.join(missing)}"
            )
    
    def _run_command(self, cmd: str, description: str = "") -> subprocess.CompletedProcess:
        """Execute a shell command with logging."""
        if description:
            logger.info(f"  {description}")
        logger.debug(f"  Command: {cmd}")
        
        try:
            result = subprocess.run(cmd, shell=True, check=True, 
                                   capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {cmd}")
            logger.error(f"STDERR: {e.stderr}")
            raise
    
    def align(self,
              fastq1: str,
              fastq2: str,
              output_dir: str,
              sample_id: str) -> Dict[str, Any]:
        """
        Step 1: Run BWA MEM alignment for Hi-C data.
        
        Uses BWA MEM with Hi-C specific parameters (-SP5M).
        
        Args:
            fastq1: Path to R1 FASTQ file
            fastq2: Path to R2 FASTQ file
            output_dir: Output directory
            sample_id: Sample identifier
            
        Returns:
            Dictionary with alignment statistics
        """
        logger.info("=" * 70)
        logger.info("STEP 1: BWA MEM ALIGNMENT")
        logger.info("=" * 70)
        logger.info(f"FASTQ R1: {fastq1}")
        logger.info(f"FASTQ R2: {fastq2}")
        
        # Create output directories
        aligned_dir = os.path.join(output_dir, 'aligned')
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(aligned_dir, exist_ok=True)
        os.makedirs(qc_dir, exist_ok=True)
        
        output_sam = os.path.join(aligned_dir, f"{sample_id}.sam")
        stats_file = os.path.join(qc_dir, f"{sample_id}_alignment.stats")
        
        # BWA MEM with Hi-C specific parameters
        # -S: Skip mate rescue
        # -P: Skip pairing; mate rescue performed unless -S also in use
        # -5: For split alignment, take the alignment with the smallest coordinate as primary
        # -M: Mark shorter split hits as secondary
        # Use absolute paths for output files
        output_sam_abs = os.path.abspath(output_sam)
        stats_file_abs = os.path.abspath(stats_file)
        cmd = f"bwa mem -SP5M -t {self.threads} {self.genome_index} {fastq1} {fastq2} > {output_sam_abs} 2> {stats_file_abs}"
        
        self._run_command(cmd, f"Aligning {sample_id}...")
        
        # Get file size as basic stat
        sam_size = os.path.getsize(output_sam) if os.path.exists(output_sam) else 0
        
        logger.info(f"  Output SAM: {output_sam} ({sam_size / 1e9:.2f} GB)")
        
        return {
            'output_sam': output_sam,
            'stats_file': stats_file,
            'sam_size_bytes': sam_size
        }
    
    def process_sam(self,
                    input_sam: str,
                    output_dir: str,
                    sample_id: str) -> Dict[str, Any]:
        """
        Step 2: Process SAM to sorted BAM.
        
        Converts SAM to BAM and sorts by read name for pairtools.
        
        Args:
            input_sam: Path to input SAM file
            output_dir: Output directory
            sample_id: Sample identifier
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info("=" * 70)
        logger.info("STEP 2: SAM/BAM PROCESSING")
        logger.info("=" * 70)
        
        processed_dir = os.path.join(output_dir, 'processed')
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(qc_dir, exist_ok=True)
        
        bam_file = os.path.join(processed_dir, f"{sample_id}.bam")
        sorted_bam = os.path.join(processed_dir, f"{sample_id}_sorted.bam")
        stats_file = os.path.join(qc_dir, f"{sample_id}_bam.stats")
        
        # Convert SAM to BAM
        cmd = f"samtools view -@ {self.threads} -bS {input_sam} > {bam_file}"
        self._run_command(cmd, "Converting SAM to BAM...")
        
        # Sort by read name (required for pairtools)
        cmd = f"samtools sort -@ {self.threads} -n -o {sorted_bam} {bam_file}"
        self._run_command(cmd, "Sorting BAM by read name...")
        
        # Generate stats
        cmd = f"samtools stats -@ {self.threads} {sorted_bam} > {stats_file}"
        self._run_command(cmd, "Generating BAM statistics...")
        
        # Clean up unsorted BAM
        if os.path.exists(bam_file):
            os.remove(bam_file)
        
        bam_size = os.path.getsize(sorted_bam) if os.path.exists(sorted_bam) else 0
        logger.info(f"  Output BAM: {sorted_bam} ({bam_size / 1e9:.2f} GB)")
        
        return {
            'sorted_bam': sorted_bam,
            'stats_file': stats_file,
            'bam_size_bytes': bam_size
        }
    
    def process_pairs(self,
                      input_bam: str,
                      output_dir: str,
                      sample_id: str) -> Dict[str, Any]:
        """
        Step 3: Process Hi-C pairs using pairtools.
        
        Parses BAM to pairs format, sorts, deduplicates, and filters.
        
        Args:
            input_bam: Path to sorted BAM file
            output_dir: Output directory
            sample_id: Sample identifier
            
        Returns:
            Dictionary with pairs processing statistics
        """
        logger.info("=" * 70)
        logger.info("STEP 3: PAIRS PROCESSING")
        logger.info("=" * 70)
        
        pairs_dir = os.path.join(output_dir, 'pairs')
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(pairs_dir, exist_ok=True)
        os.makedirs(qc_dir, exist_ok=True)
        
        temp_pairs = os.path.join(pairs_dir, f"{sample_id}.temp.pairs.gz")
        sorted_pairs = os.path.join(pairs_dir, f"{sample_id}.sorted.pairs.gz")
        dedup_pairs = os.path.join(pairs_dir, f"{sample_id}.dedup.pairs.gz")
        filtered_pairs = os.path.join(pairs_dir, f"{sample_id}.filtered.pairs.gz")
        
        parse_stats = os.path.join(qc_dir, f"{sample_id}_pairs.stats")
        dedup_stats = os.path.join(qc_dir, f"{sample_id}_dedup.stats")
        
        # Parse BAM to pairs
        logger.info("  Parsing BAM to pairs format...")
        _chroms_src = self.fragment_bed if self.fragment_bed else self.chrom_sizes
        _walks_opt  = "--walks-policy all" if self.fragment_bed else ""
        if self.fragment_bed:
            logger.info(f"  Fragment-aware parsing using: {self.fragment_bed}")
        cmd = f"""pairtools parse \
            --assembly {self.assembly} \
            --chroms-path {_chroms_src} \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {temp_pairs} \
            --output-stats {parse_stats} \
            {_walks_opt} \
            {input_bam}"""
        self._run_command(cmd)
        
        # Sort pairs (use pairs_dir as temp directory to keep all temp files in output)
        logger.info("  Sorting pairs...")
        temp_sort_dir = os.path.join(pairs_dir, 'temp_sort')
        os.makedirs(temp_sort_dir, exist_ok=True)
        cmd = f"""pairtools sort \
            --tmpdir {temp_sort_dir} \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {sorted_pairs} \
            {temp_pairs}"""
        self._run_command(cmd)
        
        # Clean up temp sort directory
        if os.path.exists(temp_sort_dir):
            shutil.rmtree(temp_sort_dir)
        
        # Remove duplicates
        logger.info("  Removing duplicates...")
        cmd = f"""pairtools dedup \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {dedup_pairs} \
            --output-stats {dedup_stats} \
            --mark-dups \
            {sorted_pairs}"""
        self._run_command(cmd)
        
        # Filter valid pairs (UU, UR, RU)
        logger.info("  Filtering valid pairs...")
        cmd = f"""pairtools select '(pair_type == "UU") or (pair_type == "UR") or (pair_type == "RU")' \
            -o {filtered_pairs} {dedup_pairs}"""
        self._run_command(cmd)
        
        # Clean up temp file
        if os.path.exists(temp_pairs):
            os.remove(temp_pairs)
        
        pairs_size = os.path.getsize(filtered_pairs) if os.path.exists(filtered_pairs) else 0
        logger.info(f"  Output pairs: {filtered_pairs} ({pairs_size / 1e6:.2f} MB)")
        
        return {
            'sorted_pairs': sorted_pairs,
            'dedup_pairs': dedup_pairs,
            'filtered_pairs': filtered_pairs,
            'parse_stats': parse_stats,
            'dedup_stats': dedup_stats,
            'pairs_size_bytes': pairs_size
        }
    
    def create_contact_matrix(self,
                              input_pairs: str,
                              output_dir: str,
                              sample_id: str) -> Dict[str, Any]:
        """
        Step 4: Create contact matrices using cooler.
        
        Generates .cool and multi-resolution .mcool files.
        
        Args:
            input_pairs: Path to filtered pairs file
            output_dir: Output directory
            sample_id: Sample identifier
            
        Returns:
            Dictionary with matrix statistics
        """
        logger.info("=" * 70)
        logger.info("STEP 4: CONTACT MATRIX GENERATION")
        logger.info("=" * 70)
        
        matrices_dir = os.path.join(output_dir, 'matrices')
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(matrices_dir, exist_ok=True)
        os.makedirs(qc_dir, exist_ok=True)
        
        output_cool = os.path.join(matrices_dir, f"{sample_id}.cool")
        output_mcool = os.path.join(matrices_dir, f"{sample_id}.mcool")
        
        # Create .cool file at 1kb resolution
        logger.info("  Creating contact matrix at 1kb resolution...")
        cmd = f"""cooler cload pairs \
            -c1 2 -p1 3 -c2 4 -p2 5 \
            --assembly {self.assembly} \
            {self.chrom_sizes}:1000 \
            {input_pairs} \
            {output_cool}"""
        self._run_command(cmd)
        
        # Balance the matrix
        logger.info("  Balancing contact matrix...")
        cmd = f"""cooler balance --force \
            --max-iters 200 \
            --mad-max 5 \
            --min-nnz 5 \
            --ignore-diags 3 \
            --tol 1e-4 \
            --cis-only \
            {output_cool}"""
        self._run_command(cmd)
        
        # Create multi-resolution .mcool
        logger.info(f"  Creating multi-resolution matrix ({self.resolutions})...")
        resolutions_str = ','.join(map(str, self.resolutions))
        cmd = f"cooler zoomify --balance -n {self.threads} --resolutions {resolutions_str} {output_cool} -o {output_mcool}"
        self._run_command(cmd)
        
        # Generate matrix stats for each resolution
        for resolution in self.resolutions:
            stats_file = os.path.join(qc_dir, f"{sample_id}_matrix_{resolution}.stats")
            cmd = f"cooler info -o {stats_file} {output_mcool}::/resolutions/{resolution}"
            try:
                self._run_command(cmd)
            except:
                pass  # Stats are optional
        
        cool_size = os.path.getsize(output_cool) if os.path.exists(output_cool) else 0
        mcool_size = os.path.getsize(output_mcool) if os.path.exists(output_mcool) else 0
        
        logger.info(f"  Output .cool: {output_cool} ({cool_size / 1e6:.2f} MB)")
        logger.info(f"  Output .mcool: {output_mcool} ({mcool_size / 1e6:.2f} MB)")
        
        return {
            'cool_file': output_cool,
            'mcool_file': output_mcool,
            'cool_size_bytes': cool_size,
            'mcool_size_bytes': mcool_size,
            'resolutions': self.resolutions
        }
    
    def run(self,
            fastq1: str,
            fastq2: str,
            output_dir: str,
            sample_id: str = 'sample',
            cleanup: bool = False) -> Dict[str, Any]:
        """
        Run the complete Hi-C pipeline.
        
        Executes all steps in order:
        1. Alignment (BWA MEM)
        2. SAM/BAM processing
        3. Pairs processing (pairtools)
        4. Contact matrix generation (cooler)
        
        Args:
            fastq1: Path to R1 FASTQ file
            fastq2: Path to R2 FASTQ file
            output_dir: Output directory
            sample_id: Sample identifier (default: 'sample')
            cleanup: Remove intermediate files (default: False)
            
        Returns:
            Dictionary with all pipeline statistics
            
        Output Directory Structure:
            output_dir/
            ├── aligned/                     # (empty after processing - SAM always deleted)
            ├── processed/
            │   └── {sample_id}_sorted.bam   # Sorted BAM (KEPT)
            ├── pairs/
            │   ├── {sample_id}.sorted.pairs.gz   # Sorted pairs (KEPT)
            │   ├── {sample_id}.dedup.pairs.gz    # Deduplicated pairs (deleted if cleanup=True)
            │   └── {sample_id}.filtered.pairs.gz # Filtered pairs (KEPT)
            ├── matrices/
            │   ├── {sample_id}.cool         # Contact matrix at 1kb (KEPT)
            │   └── {sample_id}.mcool        # Multi-resolution matrix (KEPT)
            └── qc/
                ├── {sample_id}_system_config.txt  # System configuration
                ├── {sample_id}_timing.txt         # Step timing summary
                ├── {sample_id}_alignment.stats
                ├── {sample_id}_bam.stats
                ├── {sample_id}_pairs.stats
                ├── {sample_id}_dedup.stats
                └── {sample_id}_matrix_*.stats
                
        Files ALWAYS deleted (regardless of cleanup flag):
            - aligned/{sample_id}.sam (large, BAM is kept and can convert back)
            - pairs/{sample_id}.temp.pairs.gz (temporary)
            
        Files deleted only when cleanup=True:
            - pairs/{sample_id}.dedup.pairs.gz
            
        Files always kept:
            - processed/{sample_id}_sorted.bam (can convert to SAM: samtools view -h)
            - pairs/{sample_id}.sorted.pairs.gz
            - pairs/{sample_id}.filtered.pairs.gz
            - matrices/{sample_id}.cool
            - matrices/{sample_id}.mcool
            - All QC stats files
        """
        pipeline_start_time = time.time()
        
        logger.info("=" * 70)
        logger.info("BULK Hi-C PIPELINE")
        logger.info("=" * 70)
        logger.info(f"Sample: {sample_id}")
        logger.info(f"FASTQ R1: {fastq1}")
        logger.info(f"FASTQ R2: {fastq2}")
        logger.info(f"Output: {output_dir}")
        logger.info(f"Threads: {self.threads}")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Validate FASTQ files
        if not os.path.exists(fastq1):
            raise ValueError(f"FASTQ R1 not found: {fastq1}")
        if not os.path.exists(fastq2):
            raise ValueError(f"FASTQ R2 not found: {fastq2}")
        
        # Create output directory and QC directory
        os.makedirs(output_dir, exist_ok=True)
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(qc_dir, exist_ok=True)
        
        # Save system configuration
        try:
            system_info_file = os.path.join(qc_dir, f'{sample_id}_system_config.txt')
            save_system_info(system_info_file)
            logger.info(f"System configuration saved to: {system_info_file}")
        except Exception as e:
            logger.warning(f"Could not save system info: {e}")
        
        # Initialize timing tracker
        timing = {}
        
        all_stats = {
            'sample_id': sample_id,
            'fastq1': fastq1,
            'fastq2': fastq2,
            'output_dir': output_dir,
            'threads': self.threads,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # Step 1: Alignment
        step1_start = time.time()
        align_stats = self.align(fastq1, fastq2, output_dir, sample_id)
        step1_duration = time.time() - step1_start
        timing['step1_alignment'] = step1_duration
        align_stats['duration_seconds'] = step1_duration
        align_stats['duration_formatted'] = _format_duration(step1_duration)
        all_stats['alignment'] = align_stats
        logger.info(f"  Step 1 completed in: {_format_duration(step1_duration)}")
        
        # Step 2: SAM/BAM processing
        step2_start = time.time()
        sam_stats = self.process_sam(align_stats['output_sam'], output_dir, sample_id)
        step2_duration = time.time() - step2_start
        timing['step2_sam_processing'] = step2_duration
        sam_stats['duration_seconds'] = step2_duration
        sam_stats['duration_formatted'] = _format_duration(step2_duration)
        all_stats['sam_processing'] = sam_stats
        logger.info(f"  Step 2 completed in: {_format_duration(step2_duration)}")
        
        # Step 3: Pairs processing
        step3_start = time.time()
        pairs_stats = self.process_pairs(sam_stats['sorted_bam'], output_dir, sample_id)
        step3_duration = time.time() - step3_start
        timing['step3_pairs_processing'] = step3_duration
        pairs_stats['duration_seconds'] = step3_duration
        pairs_stats['duration_formatted'] = _format_duration(step3_duration)
        all_stats['pairs_processing'] = pairs_stats
        logger.info(f"  Step 3 completed in: {_format_duration(step3_duration)}")
        
        # Step 4: Contact matrix
        step4_start = time.time()
        matrix_stats = self.create_contact_matrix(
            pairs_stats['filtered_pairs'], output_dir, sample_id
        )
        step4_duration = time.time() - step4_start
        timing['step4_contact_matrix'] = step4_duration
        matrix_stats['duration_seconds'] = step4_duration
        matrix_stats['duration_formatted'] = _format_duration(step4_duration)
        all_stats['contact_matrix'] = matrix_stats
        logger.info(f"  Step 4 completed in: {_format_duration(step4_duration)}")

        # Step 5: TAD calling
        mcool_file = matrix_stats.get('mcool_file', '')
        tad_stats = {}
        if self.call_tads and mcool_file and os.path.exists(mcool_file):
            step5_start = time.time()
            try:
                from .tads import HiCTADCaller
                tad_dir = os.path.join(output_dir, 'tads')
                caller = HiCTADCaller(
                    windows=self.tad_windows,
                    threads=self.threads,
                )
                tad_stats = caller.run(
                    mcool_file=mcool_file,
                    output_dir=tad_dir,
                    sample_id=sample_id,
                    resolutions=self.resolutions,
                )
            except Exception as e:
                logger.warning(f"TAD calling failed (non-fatal): {e}")
                tad_stats = {'error': str(e)}
            step5_duration = time.time() - step5_start
            timing['step5_tad_calling'] = step5_duration
            tad_stats['duration_seconds'] = step5_duration
            tad_stats['duration_formatted'] = _format_duration(step5_duration)
            logger.info(f"  Step 5 completed in: {_format_duration(step5_duration)}")
        elif self.call_tads:
            logger.warning("  Step 5 (TAD calling) skipped — mcool not found")
        all_stats['tad_calling'] = tad_stats

        # Step 6: Loop calling
        loop_stats = {}
        if self.call_loops and mcool_file and os.path.exists(mcool_file):
            step6_start = time.time()
            try:
                from .loop_calling import HiCLoopCaller
                loop_dir = os.path.join(output_dir, 'loops')
                loop_caller = HiCLoopCaller(
                    resolutions=[r for r in self.resolutions if r >= 5_000],
                    fdr=self.loop_fdr,
                    threads=self.threads,
                )
                loop_stats = loop_caller.run(
                    mcool_file=mcool_file,
                    output_dir=loop_dir,
                    sample_id=sample_id,
                )
            except Exception as e:
                logger.warning(f"Loop calling failed (non-fatal): {e}")
                loop_stats = {'error': str(e)}
            step6_duration = time.time() - step6_start
            timing['step6_loop_calling'] = step6_duration
            loop_stats['duration_seconds'] = step6_duration
            loop_stats['duration_formatted'] = _format_duration(step6_duration)
            logger.info(f"  Step 6 completed in: {_format_duration(step6_duration)}")
        elif self.call_loops:
            logger.warning("  Step 6 (loop calling) skipped — mcool not found")
        all_stats['loop_calling'] = loop_stats

        # Step 7: A/B Compartment calling
        compartment_stats = {}
        if self.call_compartments and mcool_file and os.path.exists(mcool_file):
            step7_start = time.time()
            try:
                from .tads import HiCCompartmentCaller
                comp_dir = os.path.join(output_dir, 'compartments')
                comp_caller = HiCCompartmentCaller(
                    resolutions=[r for r in self.resolutions if r >= 25_000],
                    phasing_track=self.compartment_phasing_track,
                )
                compartment_stats = comp_caller.run(
                    mcool_file=mcool_file,
                    output_dir=comp_dir,
                    sample_id=sample_id,
                )
            except Exception as e:
                logger.warning(f"Compartment calling failed (non-fatal): {e}")
                compartment_stats = {'error': str(e)}
            step7_duration = time.time() - step7_start
            timing['step7_compartment_calling'] = step7_duration
            compartment_stats['duration_seconds'] = step7_duration
            compartment_stats['duration_formatted'] = _format_duration(step7_duration)
            logger.info(f"  Step 7 completed in: {_format_duration(step7_duration)}")
        elif self.call_compartments:
            logger.warning("  Step 7 (compartment calling) skipped — mcool not found")
        all_stats['compartment_calling'] = compartment_stats

        # Calculate total time
        total_duration = time.time() - pipeline_start_time
        timing['total'] = total_duration
        all_stats['timing'] = timing
        all_stats['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        all_stats['total_duration_seconds'] = total_duration
        all_stats['total_duration_formatted'] = _format_duration(total_duration)
        
        # Always delete SAM file (large, can be regenerated from BAM via samtools view)
        # SAM is deleted regardless of cleanup flag since BAM is kept
        sam_file = os.path.join(output_dir, 'aligned', f'{sample_id}.sam')
        deleted_files = []
        if os.path.exists(sam_file):
            os.remove(sam_file)
            deleted_files.append(sam_file)
            logger.info(f"Removed SAM file (BAM is kept): {sam_file}")
        
        # Additional cleanup if requested (removes dedup.pairs.gz)
        if cleanup:
            extra_deleted = self._cleanup(output_dir, sample_id)
            deleted_files.extend(extra_deleted)
        
        all_stats['deleted_files'] = deleted_files
        
        # Document final output files
        tads_dir = os.path.join(output_dir, 'tads')
        loops_dir = os.path.join(output_dir, 'loops')
        final_outputs = {
            'sorted_bam':    os.path.join(output_dir, 'processed', f'{sample_id}_sorted.bam'),
            'sorted_pairs':  os.path.join(output_dir, 'pairs', f'{sample_id}.sorted.pairs.gz'),
            'filtered_pairs': os.path.join(output_dir, 'pairs', f'{sample_id}.filtered.pairs.gz'),
            'cool_matrix':   os.path.join(output_dir, 'matrices', f'{sample_id}.cool'),
            'mcool_matrix':  os.path.join(output_dir, 'matrices', f'{sample_id}.mcool'),
            'tads_dir':         tads_dir if self.call_tads else None,
            'loops_dir':         loops_dir if self.call_loops else None,
            'compartments_dir':  os.path.join(output_dir, 'compartments') if self.call_compartments else None,
        }
        all_stats['final_outputs'] = final_outputs

        # Save timing summary to QC directory
        timing_file = os.path.join(qc_dir, f'{sample_id}_timing.txt')
        with open(timing_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("HI-C PIPELINE TIMING SUMMARY\n")
            f.write("=" * 70 + "\n")
            f.write(f"Sample: {sample_id}\n")
            f.write(f"Start time: {all_stats['start_time']}\n")
            f.write(f"End time: {all_stats['end_time']}\n")
            f.write(f"Threads: {self.threads}\n")
            f.write("\n" + "-" * 70 + "\n")
            f.write("STEP TIMING\n")
            f.write("-" * 70 + "\n")
            f.write(f"Step 1 - BWA MEM Alignment:    {_format_duration(timing['step1_alignment']):>25}\n")
            f.write(f"Step 2 - SAM/BAM Processing:   {_format_duration(timing['step2_sam_processing']):>25}\n")
            f.write(f"Step 3 - Pairs Processing:     {_format_duration(timing['step3_pairs_processing']):>25}\n")
            f.write(f"Step 4 - Contact Matrix:       {_format_duration(timing['step4_contact_matrix']):>25}\n")
            if 'step5_tad_calling' in timing:
                f.write(f"Step 5 - TAD Calling:          {_format_duration(timing['step5_tad_calling']):>25}\n")
            if 'step6_loop_calling' in timing:
                f.write(f"Step 6 - Loop Calling:         {_format_duration(timing['step6_loop_calling']):>25}\n")
            if 'step7_compartment_calling' in timing:
                f.write(f"Step 7 - Compartment Calling:  {_format_duration(timing['step7_compartment_calling']):>25}\n")
            f.write("-" * 70 + "\n")
            f.write(f"TOTAL:                         {_format_duration(timing['total']):>25}\n")
            f.write("=" * 70 + "\n")
        logger.info(f"Timing summary saved to: {timing_file}")
        
        logger.info("=" * 70)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Sample: {sample_id}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"End time: {all_stats['end_time']}")
        
        logger.info(f"\nTiming Summary:")
        logger.info(f"  Step 1 (Alignment):      {_format_duration(timing['step1_alignment'])}")
        logger.info(f"  Step 2 (SAM/BAM):        {_format_duration(timing['step2_sam_processing'])}")
        logger.info(f"  Step 3 (Pairs):          {_format_duration(timing['step3_pairs_processing'])}")
        logger.info(f"  Step 4 (Contact Matrix): {_format_duration(timing['step4_contact_matrix'])}")
        logger.info(f"  TOTAL:                   {_format_duration(timing['total'])}")
        
        logger.info(f"\nFinal output files (always kept):")
        logger.info(f"  Sorted BAM: {final_outputs['sorted_bam']}")
        logger.info(f"  Sorted pairs: {final_outputs['sorted_pairs']}")
        logger.info(f"  Filtered pairs: {final_outputs['filtered_pairs']}")
        logger.info(f"  Contact matrix (.cool): {final_outputs['cool_matrix']}")
        logger.info(f"  Multi-res matrix (.mcool): {final_outputs['mcool_matrix']}")
        
        logger.info(f"\nDeleted files: {len(deleted_files)}")
        for f in deleted_files:
            logger.info(f"  - {f}")
        
        if not cleanup:
            dedup_file = os.path.join(output_dir, 'pairs', f'{sample_id}.dedup.pairs.gz')
            if os.path.exists(dedup_file):
                logger.info(f"\nIntermediate files kept (use cleanup=True to remove):")
                logger.info(f"  - {dedup_file}")
        
        logger.info(f"\nNote: To convert BAM back to SAM, use: samtools view -h sorted.bam > output.sam")
        
        # Generate detailed QC report
        try:
            from .utils.qc_report import generate_hic_qc_report
            qc_report_file = os.path.join(qc_dir, f'{sample_id}_quality_report.txt')
            report = generate_hic_qc_report(
                qc_dir=qc_dir,
                sample_id=sample_id,
                output_file=qc_report_file,
                timing_info=all_stats
            )
            logger.info(f"\n{'=' * 70}")
            logger.info("DETAILED QUALITY REPORT")
            logger.info(f"{'=' * 70}")
            # Print the report to log
            for line in report.split('\n'):
                logger.info(line)
            logger.info(f"\nQuality report saved to: {qc_report_file}")
            all_stats['qc_report_file'] = qc_report_file
        except Exception as e:
            logger.warning(f"Could not generate QC report: {e}")
        
        return all_stats
    
    def _cleanup(self, output_dir: str, sample_id: str) -> List[str]:
        """
        Remove additional intermediate files to save disk space.
        
        Note: SAM files are ALWAYS deleted (handled in run() method) since
        BAM is kept and can be converted back to SAM via: samtools view -h file.bam > file.sam
        
        Files deleted by this method (only when cleanup=True):
            - pairs/{sample_id}.dedup.pairs.gz (intermediate, redundant with filtered)
            
        Files always kept:
            - processed/{sample_id}_sorted.bam (useful for reprocessing, can convert to SAM)
            - pairs/{sample_id}.sorted.pairs.gz (useful for reprocessing)
            - pairs/{sample_id}.filtered.pairs.gz (final filtered pairs)
            - matrices/{sample_id}.cool (contact matrix)
            - matrices/{sample_id}.mcool (multi-resolution matrix)
            - All QC stats files
            
        Args:
            output_dir: Output directory
            sample_id: Sample identifier
            
        Returns:
            List of deleted file paths
        """
        logger.info("Cleaning up additional intermediate files...")
        deleted_files = []
        
        # Remove dedup pairs (keep sorted pairs for potential reprocessing)
        # Note: sorted.pairs.gz and filtered.pairs.gz are kept
        pairs_dir = os.path.join(output_dir, 'pairs')
        dedup_file = os.path.join(pairs_dir, f'{sample_id}.dedup.pairs.gz')
        if os.path.exists(dedup_file):
            os.remove(dedup_file)
            deleted_files.append(dedup_file)
            logger.info(f"  Removed: {dedup_file}")
        
        logger.info(f"  Additional files removed: {len(deleted_files)}")
        logger.info(f"  Files kept: sorted.bam, sorted.pairs.gz, filtered.pairs.gz, .cool, .mcool")
        
        return deleted_files


class HiCQCAnalyzer:
    """
    Quality control analyzer for Hi-C data.
    
    Parses and summarizes QC metrics from Hi-C pipeline outputs.
    
    Example:
        >>> import chr3d as c3d
        >>> 
        >>> qc = c3d.HiCQCAnalyzer()
        >>> stats = qc.analyze(qc_dir="results/qc", output_dir="results/summary")
    """
    
    def __init__(self):
        """Initialize QC analyzer."""
        logger.info("HiCQCAnalyzer initialized")
    
    def parse_alignment_stats(self, stats_file: str) -> Dict[str, Any]:
        """
        Parse samtools stats output file.
        
        Args:
            stats_file: Path to samtools stats file
            
        Returns:
            Dictionary with alignment statistics
        """
        stats = {}
        
        if not os.path.exists(stats_file):
            logger.warning(f"Stats file not found: {stats_file}")
            return stats
        
        with open(stats_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('SN\t'):
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        key = parts[1].rstrip(':')
                        value = parts[2]
                        try:
                            if '.' in value:
                                stats[key] = float(value)
                            else:
                                stats[key] = int(value)
                        except ValueError:
                            stats[key] = value
        
        return stats
    
    def parse_pairs_stats(self, stats_file: str) -> Dict[str, Any]:
        """
        Parse pairtools stats output file.
        
        Args:
            stats_file: Path to pairtools stats file
            
        Returns:
            Dictionary with pairs statistics
        """
        stats = {}
        
        if not os.path.exists(stats_file):
            logger.warning(f"Stats file not found: {stats_file}")
            return stats
        
        with open(stats_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t') if '\t' in line else line.split()
                if len(parts) >= 2:
                    key = parts[0]
                    value = parts[1]
                    try:
                        if '.' in value:
                            stats[key] = float(value)
                        else:
                            stats[key] = int(value)
                    except ValueError:
                        stats[key] = value
        
        return stats
    
    def analyze(self, qc_dir: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze all QC files in a directory.
        
        Args:
            qc_dir: Directory containing QC files
            output_dir: Optional output directory for summary
            
        Returns:
            Dictionary with all QC statistics
        """
        logger.info(f"Analyzing QC files in: {qc_dir}")
        
        all_stats = {}
        
        # Parse alignment stats
        for stats_file in glob.glob(os.path.join(qc_dir, '*_alignment.stats')):
            sample = os.path.basename(stats_file).replace('_alignment.stats', '')
            all_stats[f'{sample}_alignment'] = self.parse_alignment_stats(stats_file)
        
        # Parse pairs stats
        for stats_file in glob.glob(os.path.join(qc_dir, '*_pairs.stats')):
            sample = os.path.basename(stats_file).replace('_pairs.stats', '')
            all_stats[f'{sample}_pairs'] = self.parse_pairs_stats(stats_file)
        
        # Parse dedup stats
        for stats_file in glob.glob(os.path.join(qc_dir, '*_dedup.stats')):
            sample = os.path.basename(stats_file).replace('_dedup.stats', '')
            all_stats[f'{sample}_dedup'] = self.parse_pairs_stats(stats_file)
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            import json
            summary_file = os.path.join(output_dir, 'qc_summary.json')
            with open(summary_file, 'w') as f:
                json.dump(all_stats, f, indent=2)
            logger.info(f"QC summary saved to: {summary_file}")
        
        return all_stats
