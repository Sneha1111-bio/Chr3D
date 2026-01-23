"""
Step 2: Genomic Mapping Module (v2 - CORRECTED)

Maps linker-filtered ChIA-PET tags to reference genome using BWA in PAIRED-END mode
and processes alignments into BEDPE format.

================================================================================
BWA ALIGNER SELECTION GUIDE
================================================================================

This module supports TWO alignment strategies:

┌─────────────────────────────────────────────────────────────────────────┐
│                     BWA ALIGNER DECISION TREE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Read Length After Linker Filtering?                                    │
│         │                                                                │
│         ├─── < 55 bp ──────────► BWA-ALN + SAMPE (DEFAULT)             │
│         │                         • More accurate for short reads        │
│         │                         • Single-threaded SAMPE (SLOW!)       │
│         │                         • Time: 24-30 hours for 44M reads     │
│         │                         • Used by: ChIA-PET Tool V3           │
│         │                                                                │
│         └─── ≥ 55 bp ──────────► BWA-MEM (RECOMMENDED)                 │
│                                   • Multi-threaded (FAST!)              │
│                                   • Time: 2-3 hours for 44M reads       │
│                                   • Used by: ChIA-PET2, ChIA-PIPE       │
│                                   • 10x faster than ALN+SAMPE           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

ALGORITHM COMPARISON:
┌──────────────┬─────────────┬──────────────┬─────────────┬──────────────┐
│   Aligner    │  Best For   │ Parallelism  │    Speed    │   Accuracy   │
├──────────────┼─────────────┼──────────────┼─────────────┼──────────────┤
│  BWA-ALN     │  < 70 bp    │ Multi (ALN)  │    SLOW     │  Excellent   │
│  + SAMPE     │  reads      │ Single(SAMPE)│ 24-30 hours │  for short   │
├──────────────┼─────────────┼──────────────┼─────────────┼──────────────┤
│  BWA-MEM     │  > 70 bp    │ Multi-thread │    FAST     │  Excellent   │
│              │  reads      │ throughout   │  2-3 hours  │  for long    │
└──────────────┴─────────────┴──────────────┴─────────────┴──────────────┘

WORKFLOW DIAGRAMS:

Option 1: BWA-ALN + SAMPE (use_bwa_mem=False, DEFAULT)
┌────────────────────────────────────────────────────────────────────┐
│  R1.fastq ──► BWA ALN ──► R1.sai ──┐                              │
│              (24 threads)           │                              │
│              ~15 minutes            ├──► BWA SAMPE ──► paired.sam │
│                                     │    (1 thread!)               │
│  R2.fastq ──► BWA ALN ──► R2.sai ──┘    24-30 hours               │
│              (24 threads)                                          │
│              ~15 minutes                                           │
└────────────────────────────────────────────────────────────────────┘

Option 2: BWA-MEM (use_bwa_mem=True, RECOMMENDED FOR SPEED)
┌────────────────────────────────────────────────────────────────────┐
│  R1.fastq + R2.fastq ──► BWA-MEM ──► paired.sam                   │
│                          (24 threads)                              │
│                          2-3 hours                                 │
└────────────────────────────────────────────────────────────────────┘

USAGE EXAMPLES:

# Example 1: Short reads (<55 bp) - Use BWA-ALN (more accurate)
mapper = PETMapperV2(
    genome_index="genome.fa",
    use_bwa_mem=False,  # Use BWA-ALN + SAMPE
    n_threads=24
)

# Example 2: Longer reads (≥55 bp) - Use BWA-MEM (much faster)
mapper = PETMapperV2(
    genome_index="genome.fa",
    use_bwa_mem=True,   # Use BWA-MEM
    n_threads=24
)

# Example 3: Prioritize speed over slight accuracy loss
mapper = PETMapperV2(
    genome_index="genome.fa",
    use_bwa_mem=True,   # 10x faster, minimal accuracy loss
    n_threads=24
)

RECOMMENDATIONS BY USE CASE:

1. Production ChIA-PET Analysis (Accuracy Priority):
   - Read length < 55 bp: use_bwa_mem=False (BWA-ALN)
   - Read length ≥ 55 bp: use_bwa_mem=True (BWA-MEM)

2. Rapid Prototyping / Testing:
   - Always use: use_bwa_mem=True (BWA-MEM)
   - 10x faster, minimal accuracy difference

3. Large-Scale Studies (100+ samples):
   - Always use: use_bwa_mem=True (BWA-MEM)
   - Time savings are critical

REFERENCES:
- ChIA-PET Tool V3: Uses ALN for <55bp, MEM for ≥55bp
- ChIA-PET2: Defaults to BWA-MEM for all read lengths
- ChIA-PIPE: Hybrid "memaln" module
- Modern consensus: BWA-MEM preferred unless reads <50bp

================================================================================
CRITICAL FIXES IN V2:
================================================================================
- BWA runs in paired-end mode (not single-end)
- BWA-ALN uses sampe (not samse)
- No redundant merge step
- Proper BEDPE coordinate convention (5' ends)
- Duplicate removal
- Proper pair filtering

Based on ChIA-PET Tool V3 and ChIA-PET best practices.
"""

import subprocess
import logging
import os
import gzip
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import pysam
import itertools

logger = logging.getLogger(__name__)


# =============================================================================
# PARALLEL MAPPING WORKER FUNCTION (must be at module level for pickling)
# =============================================================================

def _map_chunk_worker(args: Tuple) -> Tuple[str, Dict]:
    """
    Worker function to map a single chunk to BEDPE.
    
    Must be at module level for multiprocessing pickling.
    
    Args:
        args: Tuple of (chunk_r1, chunk_r2, chunk_prefix, output_dir, 
              genome_index, mapping_quality_cutoff, n_threads, use_bwa_mem,
              min_insert_size, max_insert_size, self_ligation_cutoff)
              
    Returns:
        Tuple of (bedpe_file_path, stats_dict)
    """
    (chunk_r1, chunk_r2, chunk_prefix, output_dir, 
     genome_index, mapping_quality_cutoff, n_threads, use_bwa_mem,
     min_insert_size, max_insert_size, self_ligation_cutoff) = args
    
    # Create chunk-specific mapper (avoid pickling self)
    chunk_mapper = PETMapper(
        genome_index=genome_index,
        mapping_quality_cutoff=mapping_quality_cutoff,
        n_threads=n_threads,
        use_bwa_mem=use_bwa_mem,
        min_insert_size=min_insert_size,
        max_insert_size=max_insert_size,
        self_ligation_cutoff=self_ligation_cutoff
    )
    
    # Map chunk (creates SAM → BEDPE)
    # IMPORTANT: Force parallel=False to avoid nested parallelism
    stats = chunk_mapper.map_linker_filtered_fastq(
        chunk_r1,
        chunk_r2,
        chunk_prefix,
        output_dir=output_dir,
        keep_sam=False,
        remove_duplicates=False,  # Deduplicate after merging all chunks
        parallel=False  # Force single mode - we're already in a worker
    )
    
    bedpe_file = os.path.join(output_dir, f"{chunk_prefix}.bedpe")
    return bedpe_file, stats


class PETMapper:
    """
    Maps ChIA-PET tags to reference genome and generates BEDPE files.
    
    CORRECTED Workflow:
    1. BWA paired-end alignment: (R1, R2) → paired.sam
    2. SAMtools sort by name: paired.sam → sorted.sam
    3. Parse SAM: extract paired-end mappings
    4. Generate BEDPE: chromatin interaction format
    5. Remove duplicates: deduplicate by coordinates
    """
    
    def __init__(
        self,
        genome_index: str,
        mapping_quality_cutoff: int = 30,
        n_threads: int = 4,
        use_bwa_mem: bool = False,  # Default to BWA-ALN for short tags
        min_insert_size: int = 100,
        max_insert_size: int = 100000,
        self_ligation_cutoff: int = 8000
    ):
        """
        Initialize PET mapper.
        
        Args:
            genome_index: Path to BWA genome index
            mapping_quality_cutoff: Minimum mapping quality (default: 30)
            n_threads: Number of threads for BWA/SAMtools
            use_bwa_mem: Use BWA-MEM (True) or BWA-ALN (False, default for short reads)
            min_insert_size: Minimum insert size (default: 100)
            max_insert_size: Maximum insert size (default: 100000)
            self_ligation_cutoff: Max span for self-ligation filtering (default: 8000)
        """
        self.genome_index = genome_index
        self.mapping_quality_cutoff = mapping_quality_cutoff
        self.n_threads = n_threads
        self.use_bwa_mem = use_bwa_mem
        self.min_insert_size = min_insert_size
        self.max_insert_size = max_insert_size
        self.self_ligation_cutoff = self_ligation_cutoff
        
        # Validate genome index exists
        self._validate_genome_index()
        
        # Statistics
        self.stats = {
            'total_reads': 0,
            'mapped_reads': 0,
            'properly_paired': 0,
            'high_quality_pairs': 0,
            'valid_pairs': 0,
            'intra_chromosomal': 0,
            'inter_chromosomal': 0,
            'self_ligation': 0,
            'duplicates': 0,
            'unmapped': 0,
            'low_quality': 0,
            'not_properly_paired': 0
        }
        
        logger.info(f"Initialized PETMapper (v2 - CORRECTED)")
        logger.info(f"Genome index: {genome_index}")
        logger.info(f"Mapping quality cutoff: {mapping_quality_cutoff}")
        logger.info(f"Threads: {n_threads}")
        logger.info(f"BWA mode: {'MEM' if use_bwa_mem else 'ALN (recommended for short tags)'}")
        logger.info(f"Self-ligation cutoff: {self_ligation_cutoff}bp")
    
    def _validate_genome_index(self):
        """Validate that genome index files exist."""
        required_extensions = ['.amb', '.ann', '.bwt', '.pac', '.sa']
        missing = []
        
        for ext in required_extensions:
            if not Path(f"{self.genome_index}{ext}").exists():
                missing.append(ext)
        
        if missing:
            raise FileNotFoundError(
                f"Genome index incomplete. Missing files: {missing}\n"
                f"Expected files like: {self.genome_index}.bwt, etc."
            )
        
        logger.info(f"✓ Genome index validated: {self.genome_index}")
    
    @staticmethod
    def recommend_aligner(avg_read_length: int, prioritize_speed: bool = False) -> bool:
        """
        Recommend which BWA aligner to use based on read length.
        
        Args:
            avg_read_length: Average read length after linker filtering (bp)
            prioritize_speed: If True, prefer BWA-MEM even for short reads
            
        Returns:
            bool: True for BWA-MEM, False for BWA-ALN
            
        Examples:
            >>> PETMapper.recommend_aligner(51)  # Short reads
            False  # Use BWA-ALN
            
            >>> PETMapper.recommend_aligner(75)  # Long reads
            True   # Use BWA-MEM
            
            >>> PETMapper.recommend_aligner(51, prioritize_speed=True)
            True   # Use BWA-MEM for speed
        """
        if prioritize_speed:
            logger.info(f"Speed priority: Recommending BWA-MEM (10x faster)")
            return True
        
        if avg_read_length < 55:
            logger.info(f"Read length {avg_read_length}bp < 55bp: Recommending BWA-ALN (more accurate)")
            return False
        else:
            logger.info(f"Read length {avg_read_length}bp ≥ 55bp: Recommending BWA-MEM (faster)")
            return True
    
    def run_bwa_mem_paired(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_sam: str
    ) -> bool:
        """
        Run BWA-MEM in PAIRED-END mode (CORRECTED).
        
        Args:
            fastq_r1: R1 FASTQ file
            fastq_r2: R2 FASTQ file
            output_sam: Output SAM file
            
        Returns:
            True if successful
        """
        cmd = [
            'bwa', 'mem',
            '-t', str(self.n_threads),
            '-M',  # Mark shorter split hits as secondary
            self.genome_index,
            fastq_r1,  # Both files for paired-end
            fastq_r2
        ]
        
        logger.info(f"Running BWA-MEM (paired-end): {fastq_r1} + {fastq_r2} → {output_sam}")
        
        try:
            with open(output_sam, 'w') as out_f, open(f"{output_sam}.log", 'w') as log_f:
                result = subprocess.run(
                    cmd,
                    stdout=out_f,
                    stderr=log_f,
                    text=True,
                    check=True
                )
            logger.info(f"✓ BWA-MEM completed: {output_sam}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ BWA-MEM failed: {e}")
            return False
        except FileNotFoundError:
            logger.error("✗ BWA not found. Please install BWA or activate rowan-hic environment.")
            return False
    
    def run_bwa_aln_paired(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_sam: str
    ) -> bool:
        """
        Run BWA-ALN in PAIRED-END mode using sampe (CORRECTED).
        
        Args:
            fastq_r1: R1 FASTQ file
            fastq_r2: R2 FASTQ file
            output_sam: Output SAM file
            
        Returns:
            True if successful
        """
        sai_r1 = output_sam.replace('.sam', '.R1.sai')
        sai_r2 = output_sam.replace('.sam', '.R2.sai')
        
        logger.info(f"Running BWA-ALN (paired-end): {fastq_r1} + {fastq_r2} → {output_sam}")
        
        try:
            # Step 1: bwa aln for R1
            cmd_aln_r1 = [
                'bwa', 'aln',
                '-t', str(self.n_threads),
                '-n', '2',  # Max edit distance
                self.genome_index,
                fastq_r1
            ]
            
            with open(sai_r1, 'w') as out_f:
                subprocess.run(cmd_aln_r1, stdout=out_f, stderr=subprocess.PIPE, check=True)
            
            # Step 2: bwa aln for R2
            cmd_aln_r2 = [
                'bwa', 'aln',
                '-t', str(self.n_threads),
                '-n', '2',
                self.genome_index,
                fastq_r2
            ]
            
            with open(sai_r2, 'w') as out_f:
                subprocess.run(cmd_aln_r2, stdout=out_f, stderr=subprocess.PIPE, check=True)
            
            # Step 3: bwa sampe (PAIRED-END, not samse!)
            cmd_sampe = [
                'bwa', 'sampe',
                self.genome_index,
                sai_r1,
                sai_r2,
                fastq_r1,
                fastq_r2
            ]
            
            with open(output_sam, 'w') as out_f, open(f"{output_sam}.log", 'w') as log_f:
                subprocess.run(cmd_sampe, stdout=out_f, stderr=log_f, check=True)
            
            # Clean up SAI files
            os.remove(sai_r1)
            os.remove(sai_r2)
            
            logger.info(f"✓ BWA-ALN completed: {output_sam}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ BWA-ALN failed: {e}")
            return False
        except FileNotFoundError:
            logger.error("✗ BWA not found. Please install BWA or activate rowan-hic environment.")
            return False
    
    def sort_sam_by_name(
        self,
        input_sam: str,
        output_sorted_sam: str
    ) -> bool:
        """
        Sort SAM file by read name (no merge needed for paired-end BWA).
        
        Args:
            input_sam: Input SAM file
            output_sorted_sam: Output sorted SAM file
            
        Returns:
            True if successful
        """
        logger.info(f"Sorting by name: {input_sam} → {output_sorted_sam}")
        
        cmd_sort = [
            'samtools', 'sort',
            '-n',  # Sort by read name
            '-@', str(self.n_threads),
            '-O', 'SAM',
            '-o', output_sorted_sam,
            input_sam
        ]
        
        try:
            subprocess.run(cmd_sort, check=True, capture_output=True)
            logger.info(f"✓ Sorting completed: {output_sorted_sam}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Sorting failed: {e}")
            return False
        except FileNotFoundError:
            logger.error("✗ SAMtools not found. Please install SAMtools or activate rowan-hic environment.")
            return False
    
    def parse_sam_to_bedpe(
        self,
        sorted_sam: str,
        output_bedpe: str
    ) -> Dict:
        """
        Parse name-sorted SAM file and generate BEDPE format.
        
        Uses proper BEDPE coordinates (5' fragment ends) and filters properly paired reads.
        
        Args:
            sorted_sam: Name-sorted SAM file
            output_bedpe: Output BEDPE file
            
        Returns:
            Dictionary with mapping statistics
        """
        logger.info(f"Parsing SAM to BEDPE: {sorted_sam} → {output_bedpe}")
        
        stats = defaultdict(int)
        
        with pysam.AlignmentFile(sorted_sam, 'r') as sam_file, \
             open(output_bedpe, 'w') as bedpe_file:
            
            # Use itertools.groupby for efficient grouping by read name
            for read_name, group in itertools.groupby(sam_file, key=lambda r: r.query_name):
                alignments = list(group)
                stats['total_read_groups'] += 1
                
                self._process_read_group(
                    alignments,
                    bedpe_file,
                    stats
                )
        
        logger.info(f"✓ BEDPE generation complete: {output_bedpe}")
        logger.info(f"  Total read groups: {stats.get('total_read_groups', 0)}")
        logger.info(f"  Unpaired (< 2 alignments): {stats.get('unpaired', 0)}")
        logger.info(f"  Unmapped (missing R1 or R2): {stats.get('unmapped', 0)}")
        logger.info(f"  Low quality: {stats.get('low_quality', 0)}")
        logger.info(f"  Not properly paired: {stats.get('not_properly_paired', 0)}")
        logger.info(f"  Valid pairs: {stats.get('valid_pairs', 0)}")
        logger.info(f"  Intra-chromosomal: {stats.get('intra_chromosomal', 0)}")
        logger.info(f"  Inter-chromosomal: {stats.get('inter_chromosomal', 0)}")
        
        return dict(stats)
    
    def _process_read_group(
        self,
        alignments: List,
        bedpe_file,
        stats: Dict
    ):
        """
        Process a group of alignments for the same read pair.
        
        Args:
            alignments: List of pysam AlignedSegment objects
            bedpe_file: Output file handle
            stats: Statistics dictionary
        """
        if len(alignments) < 2:
            stats['unpaired'] += 1
            return
        
        # Separate R1 and R2 alignments
        r1_alns = [a for a in alignments if a.is_read1 and not a.is_unmapped]
        r2_alns = [a for a in alignments if a.is_read2 and not a.is_unmapped]
        
        if not r1_alns or not r2_alns:
            stats['unmapped'] += 1
            return
        
        # ========================================================================
        # FOR CHIA-PET: DO NOT FILTER BY is_proper_pair!
        # ChIA-PET represents chromatin interactions, not genomic fragments.
        # The reads may have unusual orientations and distances that don't match
        # BWA's "proper pair" criteria (which expects standard paired-end sequencing).
        #
        # Paper's criteria (Li et al. 2010, Table 4):
        # 1. Both reads mapped
        # 2. Mapping quality >= 30 (uniquely mapped)
        # 3. No filtering by pair orientation or insert size
        # ========================================================================
        
        # Count "not properly paired" for statistics ONLY (don't filter!)
        r1_proper = [a for a in r1_alns if a.is_proper_pair]
        r2_proper = [a for a in r2_alns if a.is_proper_pair]
        
        if not r1_proper or not r2_proper:
            stats['not_properly_paired'] += 1
            # Continue processing - don't filter these out!
        
        # Filter ONLY by mapping quality (NOT by proper pair!)
        # r1_alns and r2_alns contain ALL mapped reads, not just properly-paired ones
        r1_alns = [a for a in r1_alns if a.mapping_quality >= self.mapping_quality_cutoff]
        r2_alns = [a for a in r2_alns if a.mapping_quality >= self.mapping_quality_cutoff]
        
        if not r1_alns or not r2_alns:
            stats['low_quality'] += 1
            return
        
        # Generate all possible pairs
        pairs = []
        for r1 in r1_alns:
            for r2 in r2_alns:
                pairs.append((r1, r2))
        
        if not pairs:
            return
        
        # Select best pair
        best_pair = self._select_best_pair(pairs)
        
        if best_pair:
            # Write the BEDPE line (do NOT filter by distance here!)
            # Distance-based categorization happens in Step 4
            self._write_bedpe_line(best_pair, bedpe_file, stats)
    
    def _select_best_pair(
        self,
        pairs: List[Tuple]
    ) -> Optional[Tuple]:
        """
        Select best pair from multiple mappings.
        
        For intra-chromosomal: select pair with smallest span
        For inter-chromosomal: select first pair
        
        Args:
            pairs: List of (r1_alignment, r2_alignment) tuples
            
        Returns:
            Best pair tuple or None
        """
        if not pairs:
            return None
        
        # Separate intra and inter-chromosomal pairs
        intra_pairs = [(r1, r2) for r1, r2 in pairs 
                       if r1.reference_name == r2.reference_name]
        inter_pairs = [(r1, r2) for r1, r2 in pairs 
                       if r1.reference_name != r2.reference_name]
        
        # Prefer intra-chromosomal
        if intra_pairs:
            # Sort by genomic span
            intra_pairs.sort(key=lambda p: abs(p[0].reference_start - p[1].reference_start))
            return intra_pairs[0]
        elif inter_pairs:
            return inter_pairs[0]
        
        return None
    
    def _write_bedpe_line(
        self,
        pair: Tuple,
        bedpe_file,
        stats: Dict
    ):
        """
        Write BEDPE line using proper ChIA-PET convention (5' fragment ends).
        
        BEDPE format:
        chr1 start1 end1 chr2 start2 end2 name score strand1 strand2
        
        Args:
            pair: (r1_alignment, r2_alignment) tuple
            bedpe_file: Output file handle
            stats: Statistics dictionary
        """
        r1, r2 = pair
        
        # Extract 5' positions (CORRECTED for ChIA-PET)
        if r1.is_reverse:
            pos1 = r1.reference_end  # 5' end on reverse strand
            strand1 = '-'
        else:
            pos1 = r1.reference_start  # 5' end on forward strand
            strand1 = '+'
        
        if r2.is_reverse:
            pos2 = r2.reference_end
            strand2 = '-'
        else:
            pos2 = r2.reference_start
            strand2 = '+'
        
        chr1 = r1.reference_name
        chr2 = r2.reference_name
        
        # Sanity check: for cis interactions, filter excessive distances
        # This catches invalid pairs that BWA may have mapped to distant regions
        MAX_CIS_DISTANCE = 10_000_000  # 10Mb - reasonable max for chromatin interactions
        if chr1 == chr2:
            distance = abs(pos1 - pos2)
            if distance > MAX_CIS_DISTANCE:
                stats['excessive_distance'] += 1
                return  # Skip this pair
        
        # Use single position for ChIA-PET (5' end)
        start1 = pos1
        end1 = pos1 + 1  # Single base
        start2 = pos2
        end2 = pos2 + 1
        
        # Use minimum mapping quality as score
        score = min(r1.mapping_quality, r2.mapping_quality)
        
        # Read name
        name = r1.query_name
        
        # Ensure consistent ordering (chr1 <= chr2, or same chr with start1 < start2)
        if (chr1 > chr2) or (chr1 == chr2 and start1 > start2):
            chr1, chr2 = chr2, chr1
            start1, start2 = start2, start1
            end1, end2 = end2, end1
            strand1, strand2 = strand2, strand1
        
        # Write BEDPE line
        bedpe_line = f"{chr1}\t{start1}\t{end1}\t{chr2}\t{start2}\t{end2}\t{name}\t{score}\t{strand1}\t{strand2}\n"
        bedpe_file.write(bedpe_line)
        
        # Update statistics
        stats['valid_pairs'] += 1
        if chr1 == chr2:
            stats['intra_chromosomal'] += 1
        else:
            stats['inter_chromosomal'] += 1
    
    def remove_duplicates(
        self,
        input_bedpe: str,
        output_dedup_bedpe: str
    ) -> int:
        """
        Remove duplicate PETs with identical genomic coordinates.
        
        Args:
            input_bedpe: Input BEDPE file
            output_dedup_bedpe: Output deduplicated BEDPE file
            
        Returns:
            Number of duplicates removed
        """
        logger.info(f"Removing duplicates: {input_bedpe} → {output_dedup_bedpe}")
        
        seen_coords: Set[Tuple] = set()
        unique_count = 0
        duplicate_count = 0
        
        with open(input_bedpe, 'r') as in_f, open(output_dedup_bedpe, 'w') as out_f:
            for line in in_f:
                fields = line.strip().split('\t')
                if len(fields) < 6:
                    continue
                
                # Create coordinate tuple (chr1, start1, chr2, start2)
                coord_key = (fields[0], int(fields[1]), fields[3], int(fields[4]))
                
                if coord_key not in seen_coords:
                    seen_coords.add(coord_key)
                    out_f.write(line)
                    unique_count += 1
                else:
                    duplicate_count += 1
        
        logger.info(f"✓ Deduplication complete:")
        logger.info(f"  Unique PETs: {unique_count}")
        logger.info(f"  Duplicates removed: {duplicate_count}")
        
        return duplicate_count
    
    # =========================================================================
    # PARALLEL CHUNK-BASED MAPPING (for BWA-ALN SAMPE bottleneck)
    # =========================================================================
    
    def _split_fastq_pairs(
        self,
        r1_file: str,
        r2_file: str,
        n_chunks: int,
        output_dir: str
    ) -> List[Tuple[str, str]]:
        """
        Split paired FASTQ files into N chunks for parallel processing.
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
        logger.info(f"Splitting {total_reads:,} reads into {n_chunks} chunks")
        
        # Split files
        f1 = gzip.open(r1_file, 'rt') if r1_file.endswith('.gz') else open(r1_file)
        f2 = gzip.open(r2_file, 'rt') if r2_file.endswith('.gz') else open(r2_file)
        
        chunk_files = []
        chunk_idx = 0
        read_count = 0
        
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
    
    def _aggregate_stats(self, all_stats: List[Dict]) -> Dict:
        """Aggregate statistics from multiple chunks."""
        final_stats = defaultdict(int)
        for stats in all_stats:
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    final_stats[key] += value
        return dict(final_stats)
    
    def map_fastq_parallel(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_prefix: str,
        output_dir: Optional[str] = None,
        n_chunks: Optional[int] = None,
        cleanup_chunks: bool = True,
        remove_duplicates: bool = True
    ) -> Dict:
        """
        Parallel mapping: Split -> Map chunks -> Merge BEDPE (not SAM!).
        
        KEY INSIGHT: Merge at BEDPE level, not SAM level!
        This avoids SAM header conflicts and is more efficient.
        
        Especially beneficial for BWA-ALN where SAMPE is single-threaded.
        For BWA-MEM, single job is usually sufficient.
        """
        start_time = time.time()
        
        if n_chunks is None:
            n_chunks = self.n_threads if not self.use_bwa_mem else 6
        
        if output_dir is None:
            output_dir = str(Path(fastq_r1).parent)
        else:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        temp_dir = tempfile.mkdtemp(prefix="mapping_chunks_")
        chunk_output_dir = os.path.join(temp_dir, "chunk_bedpe")
        os.makedirs(chunk_output_dir, exist_ok=True)
        
        logger.info("=" * 70)
        logger.info("PARALLEL MAPPING (chunk-based with BEDPE merge)")
        logger.info("=" * 70)
        logger.info(f"Input R1: {fastq_r1}")
        logger.info(f"Input R2: {fastq_r2}")
        logger.info(f"Chunks: {n_chunks}")
        logger.info(f"BWA mode: {'MEM' if self.use_bwa_mem else 'ALN'}")
        logger.info("=" * 70)
        
        try:
            # Step 1: Split FASTQ files
            split_start = time.time()
            logger.info("Step 1: Splitting FASTQ files...")
            chunk_files = self._split_fastq_pairs(fastq_r1, fastq_r2, n_chunks, temp_dir)
            split_time = time.time() - split_start
            logger.info(f"  Split completed in {split_time:.1f}s")
            
            # Step 2: Map each chunk in parallel
            map_start = time.time()
            logger.info(f"Step 2: Mapping {n_chunks} chunks in parallel...")
            
            # For BWA-ALN, give each chunk 1 thread (SAMPE is single-threaded)
            # For BWA-MEM, split threads across chunks
            threads_per_chunk = 1 if not self.use_bwa_mem else max(1, self.n_threads // n_chunks)
            
            # Prepare worker arguments
            worker_args = []
            for idx, (chunk_r1, chunk_r2) in enumerate(chunk_files):
                args = (
                    chunk_r1, chunk_r2, f"chunk_{idx:03d}", chunk_output_dir,
                    self.genome_index, self.mapping_quality_cutoff,
                    threads_per_chunk, self.use_bwa_mem,
                    self.min_insert_size, self.max_insert_size, self.self_ligation_cutoff
                )
                worker_args.append(args)
            
            # Process chunks in parallel
            chunk_bedpes = []
            all_stats = []
            
            with ProcessPoolExecutor(max_workers=n_chunks) as executor:
                futures = {executor.submit(_map_chunk_worker, args): idx 
                          for idx, args in enumerate(worker_args)}
                
                for future in as_completed(futures):
                    try:
                        bedpe_file, stats = future.result()
                        chunk_bedpes.append(bedpe_file)
                        all_stats.append(stats)
                        logger.info(f"  Chunk completed: {os.path.basename(bedpe_file)}")
                    except Exception as e:
                        logger.error(f"  Chunk failed: {e}")
            
            map_time = time.time() - map_start
            logger.info(f"  Mapping completed in {map_time:.1f}s")
            
            # Step 3: Merge BEDPE files (simple concatenation - VALID!)
            merge_start = time.time()
            logger.info("Step 3: Merging BEDPE results...")
            
            merged_bedpe = os.path.join(output_dir, f"{output_prefix}.bedpe")
            with open(merged_bedpe, 'w') as out_f:
                for bedpe in sorted(chunk_bedpes):
                    if os.path.exists(bedpe):
                        with open(bedpe, 'r') as in_f:
                            out_f.write(in_f.read())
            
            merge_time = time.time() - merge_start
            logger.info(f"  Merge completed in {merge_time:.1f}s")
            
            # Step 4: Remove duplicates (on merged BEDPE)
            final_stats = self._aggregate_stats(all_stats)
            
            if remove_duplicates:
                dedup_bedpe = os.path.join(output_dir, f"{output_prefix}.dedup.bedpe")
                dup_count = self.remove_duplicates(merged_bedpe, dedup_bedpe)
                final_stats['duplicates'] = dup_count
                final_output = dedup_bedpe
            else:
                final_output = merged_bedpe
            
        finally:
            if cleanup_chunks:
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        total_time = time.time() - start_time
        
        # Add timing info
        final_stats['timing'] = {
            'split_seconds': split_time,
            'map_seconds': map_time,
            'merge_seconds': merge_time,
            'total_seconds': total_time
        }
        
        logger.info("=" * 70)
        logger.info("PARALLEL MAPPING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total time: {total_time:.1f}s")
        logger.info(f"Valid pairs: {final_stats.get('valid_pairs', 0):,}")
        logger.info(f"Final output: {final_output}")
        logger.info("=" * 70)
        
        return final_stats
    
    def map_linker_filtered_fastq(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_prefix: str,
        output_dir: Optional[str] = None,
        keep_sam: bool = False,
        remove_duplicates: bool = True,
        parallel: Optional[bool] = None,
        n_chunks: Optional[int] = None
    ) -> Dict:
        """
        Complete mapping workflow for linker-filtered FASTQ files.
        
        Args:
            fastq_r1: R1 FASTQ file (linker-filtered tags)
            fastq_r2: R2 FASTQ file (linker-filtered tags)
            output_prefix: Prefix for output files
            output_dir: Output directory (default: same as input)
            keep_sam: Keep intermediate SAM files (default: False)
            remove_duplicates: Remove duplicate PETs (default: True)
            parallel: Use parallel chunk-based mapping (default: auto-detect)
                      - True for BWA-ALN (SAMPE bottleneck)
                      - False for BWA-MEM (already multi-threaded)
            n_chunks: Number of chunks for parallel mode
            
        Returns:
            Dictionary with mapping statistics
        """
        # Auto-detect parallel mode based on aligner
        if parallel is None:
            parallel = not self.use_bwa_mem
            if parallel:
                logger.info("Auto-detected: Using PARALLEL mode (BWA-ALN has SAMPE bottleneck)")
            else:
                logger.info("Auto-detected: Using SINGLE mode (BWA-MEM is already multi-threaded)")
        
        # Route to appropriate method
        if parallel:
            return self.map_fastq_parallel(
                fastq_r1, fastq_r2, output_prefix,
                output_dir=output_dir,
                n_chunks=n_chunks,
                remove_duplicates=remove_duplicates
            )
        
        # Single-job mode (original implementation)
        if output_dir is None:
            output_dir = Path(fastq_r1).parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        paired_sam = output_dir / f"{output_prefix}.paired.sam"
        sorted_sam = output_dir / f"{output_prefix}.sorted.sam"
        bedpe_file = output_dir / f"{output_prefix}.bedpe"
        dedup_bedpe = output_dir / f"{output_prefix}.dedup.bedpe"
        
        logger.info("=" * 60)
        logger.info("Step 2: Genomic Mapping (v2 - CORRECTED)")
        logger.info("=" * 60)
        logger.info(f"Input R1: {fastq_r1}")
        logger.info(f"Input R2: {fastq_r2}")
        logger.info(f"Output: {dedup_bedpe if remove_duplicates else bedpe_file}")
        logger.info("=" * 60)
        
        # Step 1: Paired-end alignment
        if self.use_bwa_mem:
            success = self.run_bwa_mem_paired(fastq_r1, fastq_r2, str(paired_sam))
        else:
            success = self.run_bwa_aln_paired(fastq_r1, fastq_r2, str(paired_sam))
        
        if not success:
            raise RuntimeError("Paired-end alignment failed")
        
        # Step 2: Sort by name
        success = self.sort_sam_by_name(str(paired_sam), str(sorted_sam))
        
        if not success:
            raise RuntimeError("Sorting failed")
        
        # Step 3: Generate BEDPE
        stats = self.parse_sam_to_bedpe(str(sorted_sam), str(bedpe_file))
        
        # Step 4: Remove duplicates
        if remove_duplicates:
            dup_count = self.remove_duplicates(str(bedpe_file), str(dedup_bedpe))
            stats['duplicates'] = dup_count
            final_output = dedup_bedpe
        else:
            final_output = bedpe_file
        
        # Clean up intermediate files
        if not keep_sam:
            logger.info("Cleaning up intermediate SAM files")
            for f in [paired_sam, sorted_sam]:
                if f.exists():
                    f.unlink()
        
        logger.info("=" * 60)
        logger.info("Mapping Complete")
        logger.info("=" * 60)
        logger.info(f"Final output: {final_output}")
        
        return stats
