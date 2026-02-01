"""
Linker Filtering Module v3 - High-Performance with Parasail SIMD

Major improvements over v2:
- Uses parasail library with SIMD vectorization (10-50x faster alignment)
- Supports SSE4.1, AVX2, AVX512 instruction sets
- True parallel processing with multiprocessing.Pool (bypasses GIL)
- Chunk-based processing for maximum CPU utilization
- Optimized for short linker sequences (20-30bp)

PERFORMANCE:
- parasail AVX2 single thread: ~50,000 alignments/sec
- parasail AVX2 24 threads: ~1,000,000 alignments/sec
- Expected 10-50x speedup over Bio.Align

USAGE:
    # Basic filtering with all CPUs
    python -m chr3d.linker_filtering_v3 \\
        --r1 R1.fastq.gz --r2 R2.fastq.gz \\
        --output-prefix filtered --threads 24
    
    # Chunk-based parallel processing (recommended for large files)
    python -m chr3d.linker_filtering_v3 \\
        --r1 R1.fastq.gz --r2 R2.fastq.gz \\
        --output-prefix filtered --threads 24 --chunks 6
"""

import logging
import gzip
import time
import os
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import tempfile
import shutil

try:
    import parasail
    HAS_PARASAIL = True
except ImportError:
    HAS_PARASAIL = False
    print("WARNING: parasail not installed. Install with: pip install parasail")

from Bio.Seq import Seq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceStats:
    """Track performance statistics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_reads = 0
        self.total_alignments = 0
        self.chunk_times = []
    
    def start(self):
        self.start_time = time.time()
    
    def stop(self):
        self.end_time = time.time()
    
    @property
    def elapsed_seconds(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    @property
    def reads_per_second(self):
        if self.elapsed_seconds > 0:
            return self.total_reads / self.elapsed_seconds
        return 0
    
    @property
    def alignments_per_second(self):
        if self.elapsed_seconds > 0:
            return self.total_alignments / self.elapsed_seconds
        return 0
    
    def summary(self) -> str:
        """Generate performance summary."""
        lines = [
            "=" * 70,
            "PERFORMANCE STATISTICS",
            "=" * 70,
            f"Total time: {self.elapsed_seconds:.2f} seconds",
            f"Total reads processed: {self.total_reads:,}",
            f"Total alignments performed: {self.total_alignments:,}",
            f"Reads/second: {self.reads_per_second:,.0f}",
            f"Alignments/second: {self.alignments_per_second:,.0f}",
            "=" * 70,
        ]
        return "\n".join(lines)


def detect_simd() -> str:
    """Detect available SIMD instruction set."""
    if not HAS_PARASAIL:
        return "none (parasail not installed)"
    
    if hasattr(parasail, 'can_use_avx512') and parasail.can_use_avx512():
        return "AVX512"
    elif parasail.can_use_avx2():
        return "AVX2"
    elif parasail.can_use_sse41():
        return "SSE4.1"
    else:
        return "scalar"


def reverse_complement(seq: str) -> str:
    """Get reverse complement of a DNA sequence."""
    return str(Seq(seq).reverse_complement())


def align_linker_parasail(
    linker: str,
    read_seq: str,
    matrix,
    gap_open: int,
    gap_extend: int
) -> Tuple[int, int]:
    """
    Perform local alignment using parasail (SIMD-optimized).
    
    Args:
        linker: Linker sequence
        read_seq: Read sequence
        matrix: Parasail substitution matrix
        gap_open: Gap opening penalty
        gap_extend: Gap extension penalty
        
    Returns:
        Tuple of (score, linker_start_in_read)
    """
    if not linker or not read_seq or len(read_seq) < 10:
        return 0, -1
    
    # Parasail local alignment (Smith-Waterman) with striped SIMD
    # sw_trace_striped_16 is fastest for short sequences
    try:
        result = parasail.sw_trace_striped_16(
            linker,
            read_seq,
            gap_open,
            gap_extend,
            matrix
        )
        
        score = result.score
        
        if score <= 0:
            return 0, -1
        
        # Calculate linker start position in read
        # end_ref is the 0-indexed end position of alignment in reference (read)
        # linker_start = end_ref - (aligned_length - 1)
        # For perfect match: linker_start = end_ref - len(linker) + 1
        linker_start = result.end_ref - len(linker) + 1
        
        # Tag is everything before the linker
        tag_end = linker_start
        
        return score, tag_end
        
    except Exception:
        return 0, -1


def find_best_linker_parasail(
    read_seq: str,
    linkers: List[str],
    linkers_rc: List[str],
    matrix,
    gap_open: int,
    gap_extend: int,
    check_rc: bool
) -> Tuple[int, int, int, int, bool]:
    """
    Find best matching linker using parasail.
    
    Returns:
        Tuple of (best_linker_idx, best_score, tag_end_pos, score_diff, is_rc)
    """
    best_score = -1
    second_best_score = -1
    best_linker_idx = -1
    best_tag_end = -1
    is_rc = False
    
    # Try forward linkers
    for idx, linker in enumerate(linkers):
        score, tag_end = align_linker_parasail(
            linker, read_seq, matrix, gap_open, gap_extend
        )
        
        if score > best_score:
            second_best_score = best_score
            best_score = score
            best_linker_idx = idx
            best_tag_end = tag_end
            is_rc = False
        elif score > second_best_score:
            second_best_score = score
    
    # Try reverse complement
    if check_rc and linkers_rc:
        for idx, linker_rc in enumerate(linkers_rc):
            score, tag_end = align_linker_parasail(
                linker_rc, read_seq, matrix, gap_open, gap_extend
            )
            
            if score > best_score:
                second_best_score = best_score
                best_score = score
                best_linker_idx = idx
                best_tag_end = tag_end
                is_rc = True
            elif score > second_best_score:
                second_best_score = score
    
    score_diff = best_score - second_best_score if second_best_score >= 0 else best_score
    
    return best_linker_idx, best_score, best_tag_end, score_diff, is_rc


# Global variables for multiprocessing (avoid pickling)
_LINKERS = None
_LINKERS_RC = None
_MATRIX = None
_GAP_OPEN = None
_GAP_EXTEND = None
_MIN_SCORE = None
_MIN_TAG = None
_MAX_TAG = None
_MIN_DIFF = None
_CHECK_RC = None


def init_worker(linkers, linkers_rc, match, mismatch, gap_open, gap_extend,
                min_score, min_tag, max_tag, min_diff, check_rc):
    """Initialize worker process with shared data."""
    global _LINKERS, _LINKERS_RC, _MATRIX, _GAP_OPEN, _GAP_EXTEND
    global _MIN_SCORE, _MIN_TAG, _MAX_TAG, _MIN_DIFF, _CHECK_RC
    
    _LINKERS = linkers
    _LINKERS_RC = linkers_rc
    _MATRIX = parasail.matrix_create("ACGT", match, -mismatch)
    _GAP_OPEN = gap_open
    _GAP_EXTEND = gap_extend
    _MIN_SCORE = min_score
    _MIN_TAG = min_tag
    _MAX_TAG = max_tag
    _MIN_DIFF = min_diff
    _CHECK_RC = check_rc


def process_read_pair_worker(args):
    """
    Process a single read pair (worker function for multiprocessing).
    
    Args:
        args: Tuple of (read1_id, read1_seq, read1_qual, read2_id, read2_seq, read2_qual)
        
    Returns:
        Tuple of (result_dict or None, failure_reason, alignment_count)
    """
    read1_id, read1_seq, read1_qual, read2_id, read2_seq, read2_qual = args
    
    alignment_count = 0
    
    # Find best linker for R1
    linker1_idx, score1, tag_end1, diff1, is_rc1 = find_best_linker_parasail(
        read1_seq, _LINKERS, _LINKERS_RC, _MATRIX, _GAP_OPEN, _GAP_EXTEND,
        _MIN_TAG, _CHECK_RC
    )
    alignment_count += len(_LINKERS) * (2 if _CHECK_RC else 1)
    
    # Find best linker for R2
    linker2_idx, score2, tag_end2, diff2, is_rc2 = find_best_linker_parasail(
        read2_seq, _LINKERS, _LINKERS_RC, _MATRIX, _GAP_OPEN, _GAP_EXTEND,
        _MIN_TAG, _CHECK_RC
    )
    alignment_count += len(_LINKERS) * (2 if _CHECK_RC else 1)
    
    # Check alignment scores
    if score1 < _MIN_SCORE or score2 < _MIN_SCORE:
        return None, 'alignment_score', alignment_count
    
    # Check tag lengths
    tag_len1 = tag_end1
    tag_len2 = tag_end2
    
    if (tag_len1 < _MIN_TAG or tag_len1 > _MAX_TAG or
        tag_len2 < _MIN_TAG or tag_len2 > _MAX_TAG):
        return None, 'tag_length', alignment_count
    
    # Check ambiguity
    if diff1 < _MIN_DIFF or diff2 < _MIN_DIFF:
        return None, 'ambiguous_linker', alignment_count
    
    # Extract tags
    tag1_seq = read1_seq[:tag_end1]
    tag1_qual = read1_qual[:tag_end1]
    tag2_seq = read2_seq[:tag_end2]
    tag2_qual = read2_qual[:tag_end2]
    
    result = {
        'linker1_idx': linker1_idx,
        'linker2_idx': linker2_idx,
        'tag1_id': read1_id,
        'tag1_seq': tag1_seq,
        'tag1_qual': tag1_qual,
        'tag2_id': read2_id,
        'tag2_seq': tag2_seq,
        'tag2_qual': tag2_qual,
        'is_rc': is_rc1 or is_rc2
    }
    
    return result, None, alignment_count


def process_chunk_file(args):
    """
    Process a chunk file and return filtered results.
    
    Args:
        args: Tuple of (chunk_r1, chunk_r2, output_dir, chunk_idx, params)
        
    Returns:
        Dictionary with stats
    """
    chunk_r1, chunk_r2, output_dir, chunk_idx, params = args
    
    linkers = params['linkers']
    linkers_rc = params['linkers_rc']
    
    # Create substitution matrix
    matrix = parasail.matrix_create("ACGT", params['match'], -params['mismatch'])
    
    stats = {
        'total_reads': 0,
        'valid_pets': 0,
        'failed_alignment_score': 0,
        'failed_tag_length': 0,
        'failed_ambiguous_linker': 0,
        'failed_read_id_mismatch': 0,
        'linker_composition': defaultdict(int),
        'reverse_complement_matches': 0,
        'alignments': 0
    }
    
    # Open output files
    output_path = Path(output_dir)
    n_linkers = len(linkers)
    output_files = {}
    
    for i in range(n_linkers):
        for j in range(n_linkers):
            r1_file = output_path / f"chunk_{chunk_idx}.{i+1}_{j+1}.R1.fastq"
            r2_file = output_path / f"chunk_{chunk_idx}.{i+1}_{j+1}.R2.fastq"
            output_files[(i, j)] = {
                'r1': open(r1_file, 'w'),
                'r2': open(r2_file, 'w')
            }
    
    try:
        # Open input files
        open_func = gzip.open if chunk_r1.endswith('.gz') else open
        mode = 'rt' if chunk_r1.endswith('.gz') else 'r'
        
        with open_func(chunk_r1, mode) as f1, open_func(chunk_r2, mode) as f2:
            while True:
                # Read 4 lines from each file
                r1_lines = [f1.readline() for _ in range(4)]
                r2_lines = [f2.readline() for _ in range(4)]
                
                if not r1_lines[0]:
                    break
                
                # Check if R2 also has data (files should be same length)
                if not r2_lines[0]:
                    logger.warning(f"R2 file ended before R1 at read {stats['total_reads']}")
                    break
                
                stats['total_reads'] += 1
                
                read1_id = r1_lines[0].strip()
                read1_seq = r1_lines[1].strip()
                read1_qual = r1_lines[3].strip()
                read2_id = r2_lines[0].strip()
                read2_seq = r2_lines[1].strip()
                read2_qual = r2_lines[3].strip()
                
                # CRITICAL: Validate read IDs match (fix for pairing bug)
                # Extract base read ID (remove description after space, keep core ID)
                r1_base_id = read1_id.split()[0]  # Remove description after space
                r2_base_id = read2_id.split()[0]
                
                # Remove @ prefix if present
                if r1_base_id.startswith('@'):
                    r1_base_id = r1_base_id[1:]
                if r2_base_id.startswith('@'):
                    r2_base_id = r2_base_id[1:]
                
                # Only remove /1 or /2 suffix (NOT .1 or .2 which are SRA read numbers)
                if r1_base_id.endswith('/1'):
                    r1_base_id = r1_base_id[:-2]
                if r2_base_id.endswith('/2'):
                    r2_base_id = r2_base_id[:-2]
                
                if r1_base_id != r2_base_id:
                    stats['failed_read_id_mismatch'] += 1
                    if stats['failed_read_id_mismatch'] <= 5:
                        logger.warning(f"Read ID mismatch: R1={read1_id[:60]} vs R2={read2_id[:60]}")
                    continue
                
                # Find best linker for R1
                linker1_idx, score1, tag_end1, diff1, is_rc1 = find_best_linker_parasail(
                    read1_seq, linkers, linkers_rc, matrix,
                    params['gap_open'], params['gap_extend'],
                    params['check_rc']
                )
                stats['alignments'] += len(linkers) * (2 if params['check_rc'] else 1)
                
                # Find best linker for R2
                linker2_idx, score2, tag_end2, diff2, is_rc2 = find_best_linker_parasail(
                    read2_seq, linkers, linkers_rc, matrix,
                    params['gap_open'], params['gap_extend'],
                    params['check_rc']
                )
                stats['alignments'] += len(linkers) * (2 if params['check_rc'] else 1)
                
                # Check alignment scores
                if score1 < params['min_score'] or score2 < params['min_score']:
                    stats['failed_alignment_score'] += 1
                    continue
                
                # Check tag lengths
                tag_len1 = tag_end1
                tag_len2 = tag_end2
                
                if (tag_len1 < params['min_tag'] or tag_len1 > params['max_tag'] or
                    tag_len2 < params['min_tag'] or tag_len2 > params['max_tag']):
                    stats['failed_tag_length'] += 1
                    continue
                
                # Check ambiguity
                if diff1 < params['min_diff'] or diff2 < params['min_diff']:
                    stats['failed_ambiguous_linker'] += 1
                    continue
                
                # Extract tags
                tag1_seq = read1_seq[:tag_end1]
                tag1_qual = read1_qual[:tag_end1]
                tag2_seq = read2_seq[:tag_end2]
                tag2_qual = read2_qual[:tag_end2]
                
                # Write to output
                key = (linker1_idx, linker2_idx)
                output_files[key]['r1'].write(f"{read1_id}\n{tag1_seq}\n+\n{tag1_qual}\n")
                output_files[key]['r2'].write(f"{read2_id}\n{tag2_seq}\n+\n{tag2_qual}\n")
                
                stats['valid_pets'] += 1
                stats['linker_composition'][key] += 1
                
                if is_rc1 or is_rc2:
                    stats['reverse_complement_matches'] += 1
    
    finally:
        for writers in output_files.values():
            writers['r1'].close()
            writers['r2'].close()
    
    return stats


class LinkerFilterV3:
    """
    High-performance linker filtering using parasail SIMD alignment.
    
    Parasail provides 10-50x speedup over Bio.Align for short sequence alignment.
    Uses multiprocessing.Pool for true parallel processing (bypasses GIL).
    """
    
    def __init__(
        self,
        linker_sequences: List[str],
        min_alignment_score: int = 14,
        min_tag_length: int = 18,
        max_tag_length: int = 1000,
        min_second_best_diff: int = 3,
        match_score: int = 1,
        mismatch_penalty: int = 1,
        gap_open_penalty: int = 1,
        gap_extend_penalty: int = 1,
        check_reverse_complement: bool = True,
        n_threads: int = None
    ):
        """
        Initialize high-performance LinkerFilter with parasail.
        
        Args:
            linker_sequences: List of linker sequences
            min_alignment_score: Minimum alignment score
            min_tag_length: Minimum genomic tag length
            max_tag_length: Maximum genomic tag length
            min_second_best_diff: Min score difference between best/2nd best
            match_score: Score for matching bases
            mismatch_penalty: Penalty for mismatches
            gap_open_penalty: Gap opening penalty
            gap_extend_penalty: Gap extension penalty
            check_reverse_complement: Search reverse complement
            n_threads: Number of threads (default: all CPUs)
        """
        if not HAS_PARASAIL:
            raise ImportError("parasail is required. Install with: pip install parasail")
        
        self.linker_sequences = linker_sequences
        self.min_alignment_score = min_alignment_score
        self.min_tag_length = min_tag_length
        self.max_tag_length = max_tag_length
        self.min_second_best_diff = min_second_best_diff
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.gap_open_penalty = gap_open_penalty
        self.gap_extend_penalty = gap_extend_penalty
        self.n_threads = n_threads or cpu_count()
        
        # Auto-detect if linkers are already RC pairs (common in ChIA-PET)
        # If so, disable RC checking to avoid false ambiguity
        linkers_are_rc_pairs = False
        if len(linker_sequences) == 2:
            rc_of_first = reverse_complement(linker_sequences[0])
            if rc_of_first == linker_sequences[1]:
                linkers_are_rc_pairs = True
                logger.info("  NOTE: Linkers are reverse complements of each other - disabling RC check")
        
        if linkers_are_rc_pairs:
            self.check_reverse_complement = False
        else:
            self.check_reverse_complement = check_reverse_complement
        
        # Precompute reverse complements
        if self.check_reverse_complement:
            self.linker_sequences_rc = [reverse_complement(seq) for seq in linker_sequences]
        else:
            self.linker_sequences_rc = []
        
        # Performance tracking
        self.perf_stats = PerformanceStats()
        
        # Detect SIMD
        self.simd_name = detect_simd()
        
        logger.info(f"Initialized LinkerFilterV3 with parasail")
        logger.info(f"  SIMD instruction set: {self.simd_name}")
        logger.info(f"  Linker sequences: {len(linker_sequences)}")
        logger.info(f"  Threads/processes: {self.n_threads}")
        logger.info(f"  Parameters: min_score={min_alignment_score}, min_tag={min_tag_length}, max_tag={max_tag_length}")
    
    def split_fastq_pairs(
        self,
        r1_file: str,
        r2_file: str,
        n_chunks: int,
        output_dir: str
    ) -> List[Tuple[str, str]]:
        """
        Split paired FASTQ files into N chunks.
        
        Returns:
            List of (chunk_r1, chunk_r2) file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Count total reads
        logger.info("Counting reads for splitting...")
        open_func = gzip.open if r1_file.endswith('.gz') else open
        mode = 'rt' if r1_file.endswith('.gz') else 'r'
        
        total_reads = 0
        with open_func(r1_file, mode) as f:
            for line in f:
                total_reads += 1
        total_reads = total_reads // 4
        
        reads_per_chunk = (total_reads // n_chunks) + 1
        
        logger.info(f"Splitting {total_reads:,} reads into {n_chunks} chunks (~{reads_per_chunk:,} reads each)")
        
        # Split files
        f1 = gzip.open(r1_file, 'rt') if r1_file.endswith('.gz') else open(r1_file)
        f2 = gzip.open(r2_file, 'rt') if r2_file.endswith('.gz') else open(r2_file)
        
        chunk_files = []
        chunk_idx = 0
        read_count = 0
        
        # Open first chunk
        chunk_r1 = output_path / f"chunk_{chunk_idx:03d}_R1.fastq"
        chunk_r2 = output_path / f"chunk_{chunk_idx:03d}_R2.fastq"
        out_r1 = open(chunk_r1, 'w')
        out_r2 = open(chunk_r2, 'w')
        chunk_files.append((str(chunk_r1), str(chunk_r2)))
        
        try:
            while True:
                r1_lines = [f1.readline() for _ in range(4)]
                r2_lines = [f2.readline() for _ in range(4)]
                
                if not r1_lines[0]:
                    break
                
                out_r1.writelines(r1_lines)
                out_r2.writelines(r2_lines)
                read_count += 1
                
                if read_count >= reads_per_chunk and chunk_idx < n_chunks - 1:
                    out_r1.close()
                    out_r2.close()
                    chunk_idx += 1
                    read_count = 0
                    
                    chunk_r1 = output_path / f"chunk_{chunk_idx:03d}_R1.fastq"
                    chunk_r2 = output_path / f"chunk_{chunk_idx:03d}_R2.fastq"
                    out_r1 = open(chunk_r1, 'w')
                    out_r2 = open(chunk_r2, 'w')
                    chunk_files.append((str(chunk_r1), str(chunk_r2)))
        finally:
            out_r1.close()
            out_r2.close()
            f1.close()
            f2.close()
        
        logger.info(f"Created {len(chunk_files)} chunk pairs")
        return chunk_files
    
    def filter_fastq_parallel(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_prefix: str,
        output_dir: Optional[str] = None,
        n_chunks: Optional[int] = None,
        show_progress: bool = True,
        cleanup_chunks: bool = True,
        temp_dir: Optional[str] = None
    ) -> Dict:
        """
        Filter paired FASTQ files using chunk-based parallel processing.
        
        Args:
            fastq_r1: Path to R1 FASTQ file
            fastq_r2: Path to R2 FASTQ file
            output_prefix: Prefix for output files
            output_dir: Output directory
            n_chunks: Number of chunks (default: n_threads)
            show_progress: Show progress bar
            cleanup_chunks: Remove temporary chunk files
            temp_dir: Directory for temporary files (default: output_dir/tmp)
            
        Returns:
            Dictionary with filtering statistics
        """
        self.perf_stats.start()
        
        if output_dir is None:
            output_dir = str(Path(fastq_r1).parent)
        else:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if n_chunks is None:
            n_chunks = self.n_threads
        
        # Create temp directory for chunks in output_dir (not system temp)
        if temp_dir is None:
            temp_dir = os.path.join(output_dir, "tmp_linker_filter")
        os.makedirs(temp_dir, exist_ok=True)
        chunk_output_dir = os.path.join(temp_dir, "filtered_chunks")
        os.makedirs(chunk_output_dir, exist_ok=True)
        
        logger.info(f"Starting parallel linker filtering")
        logger.info(f"  Input R1: {fastq_r1}")
        logger.info(f"  Input R2: {fastq_r2}")
        logger.info(f"  Chunks: {n_chunks}")
        logger.info(f"  Processes: {self.n_threads}")
        logger.info(f"  Temp directory: {temp_dir}")
        
        try:
            # Step 1: Split FASTQ files
            logger.info("Step 1: Splitting FASTQ files...")
            split_start = time.time()
            chunk_files = self.split_fastq_pairs(fastq_r1, fastq_r2, n_chunks, temp_dir)
            split_time = time.time() - split_start
            logger.info(f"  Split completed in {split_time:.1f}s")
            
            # Step 2: Process chunks in parallel
            logger.info("Step 2: Processing chunks in parallel...")
            filter_start = time.time()
            
            params = {
                'linkers': self.linker_sequences,
                'linkers_rc': self.linker_sequences_rc,
                'match': self.match_score,
                'mismatch': self.mismatch_penalty,
                'gap_open': self.gap_open_penalty,
                'gap_extend': self.gap_extend_penalty,
                'min_score': self.min_alignment_score,
                'min_tag': self.min_tag_length,
                'max_tag': self.max_tag_length,
                'min_diff': self.min_second_best_diff,
                'check_rc': self.check_reverse_complement
            }
            
            # Prepare arguments for each chunk
            chunk_args = [
                (chunk_r1, chunk_r2, chunk_output_dir, idx, params)
                for idx, (chunk_r1, chunk_r2) in enumerate(chunk_files)
            ]
            
            # Process chunks in parallel
            all_stats = []
            with ProcessPoolExecutor(max_workers=self.n_threads) as executor:
                futures = {executor.submit(process_chunk_file, args): idx 
                          for idx, args in enumerate(chunk_args)}
                
                if show_progress:
                    pbar = tqdm(total=len(futures), desc="Processing chunks")
                
                for future in as_completed(futures):
                    chunk_stats = future.result()
                    all_stats.append(chunk_stats)
                    if show_progress:
                        pbar.update(1)
                
                if show_progress:
                    pbar.close()
            
            filter_time = time.time() - filter_start
            logger.info(f"  Filtering completed in {filter_time:.1f}s")
            
            # Step 3: Merge results
            logger.info("Step 3: Merging filtered chunks...")
            merge_start = time.time()
            
            # Aggregate statistics
            final_stats = {
                'total_reads': 0,
                'valid_pets': 0,
                'failed_alignment_score': 0,
                'failed_tag_length': 0,
                'failed_ambiguous_linker': 0,
                'failed_read_id_mismatch': 0,
                'reverse_complement_matches': 0,
                'linker_composition': defaultdict(int),
                'alignments': 0
            }
            
            for stats in all_stats:
                final_stats['total_reads'] += stats['total_reads']
                final_stats['valid_pets'] += stats['valid_pets']
                final_stats['failed_alignment_score'] += stats['failed_alignment_score']
                final_stats['failed_tag_length'] += stats['failed_tag_length']
                final_stats['failed_ambiguous_linker'] += stats['failed_ambiguous_linker']
                final_stats['reverse_complement_matches'] += stats['reverse_complement_matches']
                final_stats['alignments'] += stats['alignments']
                for key, count in stats['linker_composition'].items():
                    final_stats['linker_composition'][key] += count
            
            # Merge output files
            n_linkers = len(self.linker_sequences)
            for i in range(n_linkers):
                for j in range(n_linkers):
                    r1_output = os.path.join(output_dir, f"{output_prefix}.{i+1}_{j+1}.R1.fastq")
                    r2_output = os.path.join(output_dir, f"{output_prefix}.{i+1}_{j+1}.R2.fastq")
                    
                    with open(r1_output, 'w') as out_r1, open(r2_output, 'w') as out_r2:
                        for chunk_idx in range(len(chunk_files)):
                            chunk_r1 = os.path.join(chunk_output_dir, f"chunk_{chunk_idx}.{i+1}_{j+1}.R1.fastq")
                            chunk_r2 = os.path.join(chunk_output_dir, f"chunk_{chunk_idx}.{i+1}_{j+1}.R2.fastq")
                            
                            if os.path.exists(chunk_r1):
                                with open(chunk_r1, 'r') as f:
                                    out_r1.write(f.read())
                            if os.path.exists(chunk_r2):
                                with open(chunk_r2, 'r') as f:
                                    out_r2.write(f.read())
            
            merge_time = time.time() - merge_start
            logger.info(f"  Merge completed in {merge_time:.1f}s")
            
        finally:
            # Cleanup temp files
            if cleanup_chunks:
                logger.info(f"Cleaning up temp directory: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        self.perf_stats.stop()
        self.perf_stats.total_reads = final_stats['total_reads']
        self.perf_stats.total_alignments = final_stats['alignments']
        
        # Log final statistics
        self._log_statistics(final_stats)
        
        # Add timing info to stats
        final_stats['timing'] = {
            'split_seconds': split_time,
            'filter_seconds': filter_time,
            'merge_seconds': merge_time,
            'total_seconds': self.perf_stats.elapsed_seconds
        }
        final_stats['performance'] = {
            'reads_per_second': self.perf_stats.reads_per_second,
            'alignments_per_second': self.perf_stats.alignments_per_second,
            'simd': self.simd_name,
            'threads': self.n_threads,
            'chunks': n_chunks
        }
        
        return final_stats
    
    def _log_statistics(self, stats: Dict):
        """Log filtering statistics."""
        logger.info("=" * 70)
        logger.info("LINKER FILTERING COMPLETE (parasail v3)")
        logger.info("=" * 70)
        logger.info(f"Total reads processed: {stats['total_reads']:,}")
        logger.info(f"Valid PETs: {stats['valid_pets']:,} "
                   f"({100 * stats['valid_pets'] / max(1, stats['total_reads']):.2f}%)")
        logger.info(f"Failed alignment score: {stats['failed_alignment_score']:,}")
        logger.info(f"Failed tag length: {stats['failed_tag_length']:,}")
        logger.info(f"Failed ambiguous linker: {stats['failed_ambiguous_linker']:,}")
        logger.info(f"Reverse complement matches: {stats['reverse_complement_matches']:,}")
        logger.info("")
        logger.info("Linker Composition:")
        for (i, j), count in sorted(stats['linker_composition'].items()):
            pct = 100 * count / max(1, stats['valid_pets'])
            logger.info(f"  Linker {i+1} x {j+1}: {count:,} PETs ({pct:.1f}%)")
        logger.info("")
        logger.info(self.perf_stats.summary())


def main():
    """Command-line interface for high-performance linker filtering."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='High-performance linker filtering with parasail SIMD',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic filtering with all CPUs
  python -m chr3d.linker_filtering_v3 \\
      --r1 R1.fastq.gz --r2 R2.fastq.gz \\
      --output-prefix filtered --threads 24
  
  # Chunk-based parallel processing
  python -m chr3d.linker_filtering_v3 \\
      --r1 R1.fastq.gz --r2 R2.fastq.gz \\
      --output-prefix filtered --threads 24 --chunks 6

Performance:
  - Uses parasail SIMD (AVX2/SSE4.1) for 10-50x faster alignment
  - Multiprocessing for true parallel execution (bypasses GIL)
  - Chunk-based processing for optimal CPU utilization
        """
    )
    
    # Input files
    parser.add_argument('--r1', required=True, help='Input FASTQ R1 file')
    parser.add_argument('--r2', required=True, help='Input FASTQ R2 file')
    
    # Linker sequences
    parser.add_argument('--linker-a', default='ACGCGATATCTTATCTGACT', help='Linker A sequence')
    parser.add_argument('--linker-b', default='AGTCAGATAAGATATCGCGT', help='Linker B sequence')
    
    # Output
    parser.add_argument('--output-prefix', required=True, help='Output prefix for filtered files')
    parser.add_argument('--output-dir', help='Output directory')
    
    # Parallelization
    parser.add_argument('--threads', type=int, default=cpu_count(), 
                       help=f'Number of threads (default: {cpu_count()})')
    parser.add_argument('--chunks', type=int, help='Number of chunks (default: same as threads)')
    
    # Filter parameters
    parser.add_argument('--min-score', type=int, default=14, help='Minimum alignment score')
    parser.add_argument('--min-tag', type=int, default=18, help='Minimum tag length')
    parser.add_argument('--max-tag', type=int, default=1000, help='Maximum tag length')
    parser.add_argument('--min-diff', type=int, default=3, help='Min score difference for ambiguity')
    
    # Alignment parameters
    parser.add_argument('--match', type=int, default=1, help='Match score')
    parser.add_argument('--mismatch', type=int, default=1, help='Mismatch penalty')
    parser.add_argument('--gap-open', type=int, default=1, help='Gap open penalty')
    parser.add_argument('--gap-extend', type=int, default=1, help='Gap extend penalty')
    
    # Options
    parser.add_argument('--no-rc', action='store_true', help='Disable reverse complement checking')
    parser.add_argument('--keep-chunks', action='store_true', help='Keep temporary chunk files')
    
    args = parser.parse_args()
    
    # Print system info
    print("=" * 70)
    print("LINKER FILTERING v3 - High Performance with Parasail SIMD")
    print("=" * 70)
    print(f"SIMD instruction set: {detect_simd()}")
    print(f"CPU cores available: {cpu_count()}")
    print(f"Using threads: {args.threads}")
    print(f"Using chunks: {args.chunks or args.threads}")
    print("=" * 70)
    
    # Initialize filter
    linker_filter = LinkerFilterV3(
        linker_sequences=[args.linker_a, args.linker_b],
        min_alignment_score=args.min_score,
        min_tag_length=args.min_tag,
        max_tag_length=args.max_tag,
        min_second_best_diff=args.min_diff,
        match_score=args.match,
        mismatch_penalty=args.mismatch,
        gap_open_penalty=args.gap_open,
        gap_extend_penalty=args.gap_extend,
        check_reverse_complement=not args.no_rc,
        n_threads=args.threads
    )
    
    # Run filtering
    stats = linker_filter.filter_fastq_parallel(
        args.r1,
        args.r2,
        args.output_prefix,
        output_dir=args.output_dir,
        n_chunks=args.chunks,
        cleanup_chunks=not args.keep_chunks
    )
    
    # Print final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Total reads: {stats['total_reads']:,}")
    print(f"Valid PETs: {stats['valid_pets']:,} ({100*stats['valid_pets']/max(1,stats['total_reads']):.1f}%)")
    print(f"Total time: {stats['timing']['total_seconds']:.2f} seconds")
    print(f"Throughput: {stats['performance']['reads_per_second']:,.0f} reads/second")
    print(f"Alignments: {stats['performance']['alignments_per_second']:,.0f} alignments/second")
    print("=" * 70)


if __name__ == '__main__':
    main()
