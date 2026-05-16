"""Hi-C Analysis Module - Modular Hi-C data processing pipeline."""

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
    """Split large FASTQ files into smaller chunks for parallel processing."""
    
    def __init__(self, n_chunks: int = 10, reads_per_chunk: Optional[int] = None):
        """Initialize FASTQ splitter."""
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
    """Hi-C alignment using BWA MEM with -SP5M flags."""
    
    def __init__(self,
                 genome_index: str,
                 threads: int = 1):
        """Initialize Hi-C aligner."""
        self.genome_index = genome_index
        self.threads = threads
        
        self._validate_index()
        
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
    """SAM/BAM processing using samtools - converts SAM to sorted BAM."""
    
    def __init__(self, threads: int = 1, min_mapq: int = 0):
        """Initialize SAM processor."""
        self.threads = threads
        self.min_mapq = min_mapq
        
        if not _check_tool('samtools'):
            raise RuntimeError("samtools not found. Install with: conda install -c bioconda samtools")
        
        logger.info("HiCSamProcessor initialized")
        logger.info(f"  Threads: {threads}")
        logger.info(f"  Min MAPQ: {min_mapq or 'none (deferred to pairtools)'}")
    
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
        
        # Convert SAM to BAM (MAPQ filtering deferred to pairtools parse --min-mapq)
        mapq_opt = f"-q {self.min_mapq}" if self.min_mapq > 0 else ""
        cmd = f"samtools view -@ {self.threads} {mapq_opt} -bS {input_sam} > {unsorted_bam}"
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
    """Hi-C pairs processing using pairtools - parse, sort, dedup, filter."""
    
    def __init__(self,
                 chrom_sizes: str,
                 assembly: str = 'hg38',
                 threads: int = 1,
                 fragment_bed: Optional[str] = None,
                 min_mapq: int = 30):
        """Initialize pairs processor."""
        self.chrom_sizes = chrom_sizes
        self.assembly = assembly
        self.threads = threads
        self.fragment_bed = fragment_bed
        self.min_mapq = min_mapq
        
        if not os.path.exists(chrom_sizes):
            raise ValueError(f"Chromosome sizes file not found: {chrom_sizes}")
        
        if not _check_tool('pairtools'):
            raise RuntimeError("pairtools not found. Install with: conda install -c bioconda pairtools")
        
        logger.info("HiCPairsProcessor initialized")
        logger.info(f"  Chromosome sizes: {chrom_sizes}")
        logger.info(f"  Assembly: {assembly}")
        logger.info(f"  Threads: {threads}")
        logger.info(f"  Fragment BED: {fragment_bed or 'none (position-based)'}")
        logger.info(f"  Min MAPQ: {min_mapq}")
    
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
        # --chroms-path must be a chrom.sizes file, NEVER a fragment BED.
        # Fragment-aware annotation is done via `pairtools restrict` (see
        # HiCPairsProcessor.restrict / the pipeline process_pairs step).
        walks_opt = "--walks-policy all --max-inter-align-gap 20" if self.fragment_bed else ""
        mapq_opt = f"--min-mapq {self.min_mapq}" if self.min_mapq > 0 else ""
        cmd = f"""pairtools parse \
            --assembly {self.assembly} \
            --chroms-path {self.chrom_sizes} \
            --add-columns mapq \
            {mapq_opt} \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {output_pairs} \
            {stats_opt} \
            {walks_opt} \
            {input_bam}"""
        
        _run_command(cmd)
        
        return {'output_pairs': output_pairs, 'stats_file': stats_file}
    
    def restrict(self,
                 input_pairs: str,
                 output_pairs: str) -> Dict[str, Any]:
        """
        Annotate restriction fragments on a pairs file.
        
        Requires ``fragment_bed`` to have been set at construction.
        Adds rfrag1/rfrag2 columns so downstream tools can filter
        same-fragment (self-ligation) pairs.
        """
        if not self.fragment_bed:
            raise RuntimeError("restrict() requires fragment_bed to be set on HiCPairsProcessor")
        
        logger.info("PAIRTOOLS RESTRICT")
        logger.info(f"  Input: {input_pairs}")
        logger.info(f"  Fragments: {self.fragment_bed}")
        logger.info(f"  Output: {output_pairs}")
        
        os.makedirs(os.path.dirname(output_pairs) or '.', exist_ok=True)
        
        cmd = f"""pairtools restrict \
            --frags {self.fragment_bed} \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {output_pairs} \
            {input_pairs}"""
        
        _run_command(cmd)
        
        return {'output_pairs': output_pairs}
    
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
    
    def select_chroms(self,
                      input_pairs: str,
                      output_pairs: str) -> Dict[str, Any]:
        """
        Keep only pairs on standard chromosomes.
        
        Non-standard contigs (e.g. HLA-DRB1*12:01:01, decoy contigs) cause
        ``pairtools restrict`` to crash because they are absent from the
        fragment BED.  This step removes them before restrict.
        
        Args:
            input_pairs: Path to input pairs file
            output_pairs: Path to output cleaned pairs file
            
        Returns:
            Dictionary with output path
        """
        logger.info("PAIRTOOLS SELECT (STANDARD CHROMS)")
        logger.info(f"  Input: {input_pairs}")
        logger.info(f"  Output: {output_pairs}")
        
        os.makedirs(os.path.dirname(output_pairs) or '.', exist_ok=True)
        
        # Keep pairs where both chroms are standard (chr1-22, chrX, chrY, chrM)
        # or unmapped marker "!"
        cmd = f"""pairtools select \
            '(chrom1 == "!" or (chrom1.startswith("chr") and len(chrom1) <= 5 and chrom1[3:].isdigit() or chrom1 in ["chrX","chrY","chrM"])) and (chrom2 == "!" or (chrom2.startswith("chr") and len(chrom2) <= 5 and chrom2[3:].isdigit() or chrom2 in ["chrX","chrY","chrM"]))' \
            -o {output_pairs} {input_pairs}"""
        
        _run_command(cmd)
        
        pairs_size = os.path.getsize(output_pairs) if os.path.exists(output_pairs) else 0
        logger.info(f"  Output: {output_pairs} ({pairs_size / 1e6:.2f} MB)")
        
        return {'output_pairs': output_pairs, 'pairs_size_bytes': pairs_size}
    
    def filter(self,
               input_pairs: str,
               output_pairs: str,
               pair_types: Optional[List[str]] = None,
               min_mapq: Optional[int] = None) -> Dict[str, Any]:
        """
        Filter pairs by pair type and MAPQ score.
        
        Args:
            input_pairs: Path to deduplicated pairs file
            output_pairs: Path to output filtered pairs file
            pair_types: List of pair types to keep (default: ['UU', 'UR', 'RU'])
            min_mapq: Minimum MAPQ for both sides (default: use self.min_mapq)
            
        Returns:
            Dictionary with filtering statistics
        """
        logger.info("PAIRTOOLS SELECT (FILTER)")
        logger.info(f"  Input: {input_pairs}")
        logger.info(f"  Output: {output_pairs}")
        
        os.makedirs(os.path.dirname(output_pairs) or '.', exist_ok=True)
        
        if pair_types is None:
            pair_types = ['UU', 'UR', 'RU']
        if min_mapq is None:
            min_mapq = self.min_mapq
        
        # Build pair type sub-expression
        type_expr = ' or '.join([f'(pair_type == "{pt}")' for pt in pair_types])
        
        # Build MAPQ sub-expression (only if min_mapq > 0)
        if min_mapq > 0:
            mapq_expr = f'(mapq1 >= {min_mapq}) and (mapq2 >= {min_mapq})'
            filter_expr = f'{mapq_expr} and ({type_expr})'
            logger.info(f"  Filter: MAPQ >= {min_mapq} and pair types {pair_types}")
        else:
            filter_expr = type_expr
            logger.info(f"  Filter: pair types {pair_types} (no MAPQ filter)")
        
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
        
        # Step 1: Parse (includes --min-mapq and --add-columns mapq)
        parsed = os.path.join(output_dir, f"{prefix}.parsed.pairs.gz")
        parse_stats = os.path.join(output_dir, f"{prefix}.parse.stats")
        self.parse(input_bam, parsed, parse_stats)
        
        # Step 2: Sort
        sorted_pairs = os.path.join(output_dir, f"{prefix}.sorted.pairs.gz")
        self.sort(parsed, sorted_pairs, output_dir)
        
        # Step 2b: Select standard chromosomes (required before restrict)
        cleaned_pairs = os.path.join(output_dir, f"{prefix}.cleaned.pairs.gz")
        self.select_chroms(sorted_pairs, cleaned_pairs)
        
        # Step 3: Restrict (if fragment_bed is set)
        if self.fragment_bed:
            restricted_pairs = os.path.join(output_dir, f"{prefix}.restricted.pairs.gz")
            self.restrict(cleaned_pairs, restricted_pairs)
            dedup_input = restricted_pairs
        else:
            dedup_input = cleaned_pairs
        
        # Step 4: Dedup
        dedup_pairs = os.path.join(output_dir, f"{prefix}.dedup.pairs.gz")
        dedup_stats = os.path.join(output_dir, f"{prefix}.dedup.stats")
        self.dedup(dedup_input, dedup_pairs, dedup_stats)
        
        # Step 5: Filter (pair type only — MAPQ already applied at parse)
        filtered_pairs = os.path.join(output_dir, f"{prefix}.filtered.pairs.gz")
        self.filter(dedup_pairs, filtered_pairs, min_mapq=0)
        
        # Cleanup intermediate files
        if cleanup:
            for f in [parsed, cleaned_pairs]:
                if os.path.exists(f):
                    os.remove(f)
            if self.fragment_bed and os.path.exists(restricted_pairs):
                os.remove(restricted_pairs)
        
        return {
            'sorted_pairs': sorted_pairs,
            'dedup_pairs': dedup_pairs,
            'filtered_pairs': filtered_pairs,
            'parse_stats': parse_stats,
            'dedup_stats': dedup_stats
        }


class HiCMatrixGenerator:
    """Contact matrix generation using cooler - creates .cool and .mcool files."""
    
    def __init__(self,
                 chrom_sizes: str,
                 assembly: str = 'hg38',
                 threads: int = 1):
        """Initialize matrix generator."""
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
    """Complete Hi-C pipeline orchestrator combining all processing steps."""
    
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
        """Initialize Hi-C pipeline."""
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
        if os.path.isdir(self.genome_index):
            amb_files = [f for f in os.listdir(self.genome_index) if f.endswith('.amb')]
            if not amb_files:
                raise ValueError(f"No BWA index files found in: {self.genome_index}")
            base_name = amb_files[0][:-4]
            self.genome_index = os.path.join(self.genome_index, base_name)
        
        bwa_suffixes = ['.amb', '.ann', '.bwt', '.pac', '.sa']
        missing = []
        for s in bwa_suffixes:
            standard = f"{self.genome_index}{s}"
            with_64 = f"{self.genome_index}.64{s}"
            if not os.path.exists(standard) and not os.path.exists(with_64):
                missing.append(standard)
        if missing:
            raise ValueError(f"Missing BWA index files: {missing}")
        
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
        """Run BWA MEM alignment for Hi-C data."""
        logger.info("=" * 70)
        logger.info("STEP 1: BWA MEM ALIGNMENT")
        logger.info("=" * 70)
        logger.info(f"FASTQ R1: {fastq1}")
        logger.info(f"FASTQ R2: {fastq2}")
        
        aligned_dir = os.path.join(output_dir, 'aligned')
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(aligned_dir, exist_ok=True)
        os.makedirs(qc_dir, exist_ok=True)
        
        output_sam = os.path.join(aligned_dir, f"{sample_id}.sam")
        stats_file = os.path.join(qc_dir, f"{sample_id}_alignment.stats")
        
        output_sam_abs = os.path.abspath(output_sam)
        stats_file_abs = os.path.abspath(stats_file)
        cmd = f"bwa mem -SP5M -t {self.threads} {self.genome_index} {fastq1} {fastq2} > {output_sam_abs} 2> {stats_file_abs}"
        
        self._run_command(cmd, f"Aligning {sample_id}...")
        
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
        """Process SAM to sorted BAM."""
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
        
        # MAPQ filtering deferred to pairtools parse --min-mapq
        cmd = f"samtools view -@ {self.threads} -bS {input_sam} > {bam_file}"
        self._run_command(cmd, "Converting SAM to BAM...")
        
        cmd = f"samtools sort -@ {self.threads} -n -o {sorted_bam} {bam_file}"
        self._run_command(cmd, "Sorting BAM by read name...")
        
        cmd = f"samtools stats -@ {self.threads} {sorted_bam} > {stats_file}"
        self._run_command(cmd, "Generating BAM statistics...")
        
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
        """Process Hi-C pairs using pairtools."""
        logger.info("=" * 70)
        logger.info("STEP 3: PAIRS PROCESSING")
        logger.info("=" * 70)
        
        pairs_dir = os.path.join(output_dir, 'pairs')
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(pairs_dir, exist_ok=True)
        os.makedirs(qc_dir, exist_ok=True)
        
        temp_pairs = os.path.join(pairs_dir, f"{sample_id}.temp.pairs.gz")
        restrict_pairs = os.path.join(pairs_dir, f"{sample_id}.restrict.pairs.gz")
        sorted_pairs = os.path.join(pairs_dir, f"{sample_id}.sorted.pairs.gz")
        dedup_pairs = os.path.join(pairs_dir, f"{sample_id}.dedup.pairs.gz")
        filtered_pairs = os.path.join(pairs_dir, f"{sample_id}.filtered.pairs.gz")
        
        parse_stats = os.path.join(qc_dir, f"{sample_id}_pairs.stats")
        dedup_stats = os.path.join(qc_dir, f"{sample_id}_dedup.stats")
        
        # Parse BAM to pairs
        # NOTE: --chroms-path requires a chrom.sizes file (used only to order
        # chromosomes for mate flipping). It must NEVER be a fragment BED.
        # For fragment-aware processing we run `pairtools restrict` AFTER parse.
        # Resume-within-step-3: if the temp pairs file already exists and is
        # non-trivial, skip parse and reuse it (parse is the most expensive
        # sub-step; this lets us recover from later sub-step failures).
        _PARSE_RESUME_MIN_BYTES = 10 * 1024 * 1024  # 10 MB
        if os.path.exists(temp_pairs) and os.path.getsize(temp_pairs) >= _PARSE_RESUME_MIN_BYTES:
            logger.info(
                f"  Skipping `pairtools parse` — reusing existing temp pairs: "
                f"{temp_pairs} ({os.path.getsize(temp_pairs) / 1e9:.2f} GB)"
            )
        else:
            logger.info("  Parsing BAM to pairs format...")
            _walks_opt = "--walks-policy all --max-inter-align-gap 20" if self.fragment_bed else ""
            if self.fragment_bed:
                logger.info(f"  Walk rescue enabled (fragment-aware). Fragments: {self.fragment_bed}")
            cmd = f"""pairtools parse \
                --assembly {self.assembly} \
                --chroms-path {self.chrom_sizes} \
                --nproc-in {self.threads} \
                --nproc-out {self.threads} \
                --output {temp_pairs} \
                --output-stats {parse_stats} \
                {_walks_opt} \
                {input_bam}"""
            self._run_command(cmd)

        # Optional: Annotate restriction fragments with `pairtools restrict`.
        # This adds rfrag1/rfrag2 columns so downstream tools can filter
        # same-fragment (self-ligation) pairs.
        #
        # IMPORTANT: `pairtools restrict` raises KeyError if it encounters a
        # chromosome in the pairs file that is not present in the fragment BED
        # (e.g. decoy / ALT / HLA contigs aligned by BWA but not digested).
        # We therefore first drop pairs whose chroms aren't in the BED using
        # `pairtools select --chrom-subset`. The chrom.sizes file matches the
        # BED's chrom set (both come from the same digest reference).
        sort_input = temp_pairs
        if self.fragment_bed:
            # Step 3a: filter to BED-known chroms (drops decoy/ALT-aligned pairs)
            chrom_filtered_pairs = os.path.join(
                pairs_dir, f"{sample_id}.chrom_filtered.pairs.gz"
            )
            logger.info(
                "  Filtering pairs to chroms present in fragment BED "
                "(drops decoy/ALT/HLA-aligned pairs not in digest)..."
            )
            cmd = f"""pairtools select \
                'True' \
                --chrom-subset {self.chrom_sizes} \
                --nproc-in {self.threads} \
                --nproc-out {self.threads} \
                -o {chrom_filtered_pairs} \
                {temp_pairs}"""
            self._run_command(cmd)

            logger.info("  Annotating restriction fragments...")
            cmd = f"""pairtools restrict \
                --frags {self.fragment_bed} \
                --nproc-in {self.threads} \
                --nproc-out {self.threads} \
                --output {restrict_pairs} \
                {chrom_filtered_pairs}"""
            self._run_command(cmd)

            if os.path.exists(chrom_filtered_pairs):
                os.remove(chrom_filtered_pairs)

            sort_input = restrict_pairs

        logger.info("  Sorting pairs...")
        temp_sort_dir = os.path.join(pairs_dir, 'temp_sort')
        os.makedirs(temp_sort_dir, exist_ok=True)
        cmd = f"""pairtools sort \
            --tmpdir {temp_sort_dir} \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {sorted_pairs} \
            {sort_input}"""
        self._run_command(cmd)
        
        if os.path.exists(temp_sort_dir):
            shutil.rmtree(temp_sort_dir)
        
        logger.info("  Removing duplicates...")
        cmd = f"""pairtools dedup \
            --nproc-in {self.threads} \
            --nproc-out {self.threads} \
            --output {dedup_pairs} \
            --output-stats {dedup_stats} \
            --mark-dups \
            {sorted_pairs}"""
        self._run_command(cmd)
        
        logger.info("  Filtering valid pairs...")
        cmd = f"""pairtools select '(pair_type == "UU") or (pair_type == "UR") or (pair_type == "RU")' \
            -o {filtered_pairs} {dedup_pairs}"""
        self._run_command(cmd)
        
        for _f in (temp_pairs, restrict_pairs):
            if os.path.exists(_f):
                os.remove(_f)
        
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
        """Create contact matrices using cooler."""
        logger.info("=" * 70)
        logger.info("STEP 4: CONTACT MATRIX GENERATION")
        logger.info("=" * 70)
        
        matrices_dir = os.path.join(output_dir, 'matrices')
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(matrices_dir, exist_ok=True)
        os.makedirs(qc_dir, exist_ok=True)
        
        output_cool = os.path.join(matrices_dir, f"{sample_id}.cool")
        output_mcool = os.path.join(matrices_dir, f"{sample_id}.mcool")
        
        logger.info("  Creating contact matrix at 1kb resolution...")
        cmd = f"""cooler cload pairs \
            -c1 2 -p1 3 -c2 4 -p2 5 \
            --assembly {self.assembly} \
            {self.chrom_sizes}:1000 \
            {input_pairs} \
            {output_cool}"""
        self._run_command(cmd)
        
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
        
        logger.info(f"  Creating multi-resolution matrix ({self.resolutions})...")
        resolutions_str = ','.join(map(str, self.resolutions))
        cmd = f"cooler zoomify --balance -n {self.threads} --resolutions {resolutions_str} {output_cool} -o {output_mcool}"
        self._run_command(cmd)
        
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
            fastq1: Optional[str] = None,
            fastq2: Optional[str] = None,
            output_dir: str = './results',
            sample_id: str = 'sample',
            cleanup: bool = False,
            start_from: int = 1) -> Dict[str, Any]:
        """Run the complete Hi-C pipeline or resume from a later step.
        
        Steps: 1. Alignment, 2. SAM/BAM, 3. Pairs, 4. Matrix, 5. TADs, 6. Loops, 7. Compartments
        
        Args:
            fastq1: Path to R1 FASTQ (required for step 1)
            fastq2: Path to R2 FASTQ (required for step 1)
            output_dir: Output directory
            sample_id: Sample identifier
            cleanup: Remove intermediate files
            start_from: Step to resume from (1-7)
            
        Returns:
            Dictionary with pipeline statistics
        """
        pipeline_start_time = time.time()

        # Validate start_from
        if start_from < 1 or start_from > 7:
            raise ValueError(f"start_from must be between 1 and 7 (got {start_from})")
        if start_from == 1 and (not fastq1 or not fastq2):
            raise ValueError("fastq1 and fastq2 are required when start_from=1")

        logger.info("=" * 70)
        logger.info("BULK Hi-C PIPELINE")
        logger.info("=" * 70)
        logger.info(f"Sample: {sample_id}")
        logger.info(f"FASTQ R1: {fastq1}")
        logger.info(f"FASTQ R2: {fastq2}")
        logger.info(f"Output: {output_dir}")
        logger.info(f"Threads: {self.threads}")
        logger.info(f"Start from: step {start_from}")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if start_from <= 1:
            if not os.path.exists(fastq1):
                raise ValueError(f"FASTQ R1 not found: {fastq1}")
            if not os.path.exists(fastq2):
                raise ValueError(f"FASTQ R2 not found: {fastq2}")
        
        os.makedirs(output_dir, exist_ok=True)
        qc_dir = os.path.join(output_dir, 'qc')
        os.makedirs(qc_dir, exist_ok=True)
        
        try:
            system_info_file = os.path.join(qc_dir, f'{sample_id}_system_config.txt')
            save_system_info(system_info_file)
            logger.info(f"System configuration saved to: {system_info_file}")
        except Exception as e:
            logger.warning(f"Could not save system info: {e}")
        
        timing = {}
        
        all_stats = {
            'sample_id': sample_id,
            'fastq1': fastq1,
            'fastq2': fastq2,
            'output_dir': output_dir,
            'threads': self.threads,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        expected_sam   = os.path.join(output_dir, 'aligned',  f'{sample_id}.sam')
        expected_bam   = os.path.join(output_dir, 'processed', f'{sample_id}_sorted.bam')
        expected_pairs = os.path.join(output_dir, 'pairs',    f'{sample_id}.filtered.pairs.gz')
        expected_mcool = os.path.join(output_dir, 'matrices', f'{sample_id}.mcool')
        expected_cool  = os.path.join(output_dir, 'matrices', f'{sample_id}.cool')

        if start_from <= 1:
            step1_start = time.time()
            align_stats = self.align(fastq1, fastq2, output_dir, sample_id)
            step1_duration = time.time() - step1_start
            timing['step1_alignment'] = step1_duration
            align_stats['duration_seconds'] = step1_duration
            align_stats['duration_formatted'] = _format_duration(step1_duration)
            all_stats['alignment'] = align_stats
            logger.info(f"  Step 1 completed in: {_format_duration(step1_duration)}")
        else:
            logger.info("  Step 1 (alignment) SKIPPED — resume mode")
            align_stats = {'output_sam': expected_sam, 'resumed': True}
            all_stats['alignment'] = align_stats

        if start_from <= 2:
            if not os.path.exists(align_stats['output_sam']):
                raise FileNotFoundError(
                    f"Cannot run step 2: SAM not found at {align_stats['output_sam']}"
                )
            step2_start = time.time()
            sam_stats = self.process_sam(align_stats['output_sam'], output_dir, sample_id)
            step2_duration = time.time() - step2_start
            timing['step2_sam_processing'] = step2_duration
            sam_stats['duration_seconds'] = step2_duration
            sam_stats['duration_formatted'] = _format_duration(step2_duration)
            all_stats['sam_processing'] = sam_stats
            logger.info(f"  Step 2 completed in: {_format_duration(step2_duration)}")
        else:
            logger.info("  Step 2 (SAM→BAM) SKIPPED — resume mode")
            sam_stats = {'sorted_bam': expected_bam, 'resumed': True}
            all_stats['sam_processing'] = sam_stats

        if start_from <= 3:
            if not os.path.exists(sam_stats['sorted_bam']):
                raise FileNotFoundError(
                    f"Cannot run step 3: sorted BAM not found at {sam_stats['sorted_bam']}"
                )
            step3_start = time.time()
            pairs_stats = self.process_pairs(sam_stats['sorted_bam'], output_dir, sample_id)
            step3_duration = time.time() - step3_start
            timing['step3_pairs_processing'] = step3_duration
            pairs_stats['duration_seconds'] = step3_duration
            pairs_stats['duration_formatted'] = _format_duration(step3_duration)
            all_stats['pairs_processing'] = pairs_stats
            logger.info(f"  Step 3 completed in: {_format_duration(step3_duration)}")
        else:
            logger.info("  Step 3 (pairs) SKIPPED — resume mode")
            pairs_stats = {'filtered_pairs': expected_pairs, 'resumed': True}
            all_stats['pairs_processing'] = pairs_stats

        if start_from <= 4:
            if not os.path.exists(pairs_stats['filtered_pairs']):
                raise FileNotFoundError(
                    f"Cannot run step 4: filtered pairs not found at {pairs_stats['filtered_pairs']}"
                )
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
        else:
            logger.info("  Step 4 (matrix) SKIPPED — resume mode")
            matrix_stats = {
                'cool_file':  expected_cool,
                'mcool_file': expected_mcool,
                'resumed': True,
            }
            all_stats['contact_matrix'] = matrix_stats

        mcool_file = matrix_stats.get('mcool_file', '')
        tad_stats = {}
        if start_from <= 5 and self.call_tads and mcool_file and os.path.exists(mcool_file):
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

        loop_stats = {}
        if start_from <= 6 and self.call_loops and mcool_file and os.path.exists(mcool_file):
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

        compartment_stats = {}
        if start_from <= 7 and self.call_compartments and mcool_file and os.path.exists(mcool_file):
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

        total_duration = time.time() - pipeline_start_time
        timing['total'] = total_duration
        all_stats['timing'] = timing
        all_stats['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        all_stats['total_duration_seconds'] = total_duration
        all_stats['total_duration_formatted'] = _format_duration(total_duration)
        
        sam_file = os.path.join(output_dir, 'aligned', f'{sample_id}.sam')
        deleted_files = []
        if os.path.exists(sam_file):
            os.remove(sam_file)
            deleted_files.append(sam_file)
            logger.info(f"Removed SAM file (BAM is kept): {sam_file}")
        
        if cleanup:
            extra_deleted = self._cleanup(output_dir, sample_id)
            deleted_files.extend(extra_deleted)
        
        all_stats['deleted_files'] = deleted_files
        
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
            f.write(f"Step 1 - BWA MEM Alignment:    {_format_duration(timing.get('step1_alignment', 0)):>25}\n")
            f.write(f"Step 2 - SAM/BAM Processing:   {_format_duration(timing.get('step2_sam_processing', 0)):>25}\n")
            f.write(f"Step 3 - Pairs Processing:     {_format_duration(timing.get('step3_pairs_processing', 0)):>25}\n")
            f.write(f"Step 4 - Contact Matrix:       {_format_duration(timing.get('step4_contact_matrix', 0)):>25}\n")
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
        logger.info(f"  Step 1 (Alignment):      {_format_duration(timing.get('step1_alignment', 0))}")
        logger.info(f"  Step 2 (SAM/BAM):        {_format_duration(timing.get('step2_sam_processing', 0))}")
        logger.info(f"  Step 3 (Pairs):          {_format_duration(timing.get('step3_pairs_processing', 0))}")
        logger.info(f"  Step 4 (Contact Matrix): {_format_duration(timing.get('step4_contact_matrix', 0))}")
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
            for line in report.split('\n'):
                logger.info(line)
            logger.info(f"\nQuality report saved to: {qc_report_file}")
            all_stats['qc_report_file'] = qc_report_file
        except Exception as e:
            logger.warning(f"Could not generate QC report: {e}")
        
        return all_stats
    
    def _cleanup(self, output_dir: str, sample_id: str) -> List[str]:
        """Remove intermediate files when cleanup=True."""
        logger.info("Cleaning up additional intermediate files...")
        deleted_files = []
        
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
    """Quality control analyzer for Hi-C pipeline outputs."""
    
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
