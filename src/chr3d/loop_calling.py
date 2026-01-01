"""
Step 6: Loop Calling Module

This module implements loop calling steps from the ChIA-PET pipeline:
- Step 6.1: Pre-clustering - Extends tags and creates cluster objects
- Step 6.2: Anchor Clustering - Merges overlapping anchor clusters

Reference: 
- ChIA-PET_Tool_V3/program/LGL/src/process/Pet2Cluster1.java
- ChIA-PET_Tool_V3/program/LGL/src/LGL/chiapet/PetCluster2.java
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import subprocess
from collections import defaultdict
import multiprocessing as mp
from functools import partial
import os

logger = logging.getLogger(__name__)


def _count_overlaps_vectorized(tag_starts, tag_ends, anchor_starts, anchor_ends):
    """
    Vectorized overlap counting for multiple anchors at once.
    
    Uses broadcasting to compute all overlaps in parallel.
    Much faster than looping through anchors one by one.
    
    Args:
        tag_starts: 1D array of tag start positions (sorted)
        tag_ends: 1D array of tag end positions
        anchor_starts: 1D array of anchor start positions
        anchor_ends: 1D array of anchor end positions
    
    Returns:
        1D array of overlap counts for each anchor
    """
    n_anchors = len(anchor_starts)
    n_tags = len(tag_starts)
    
    # For small number of tags, use simple approach
    if n_tags < 10000:
        # Reshape for broadcasting: anchors (n, 1) vs tags (1, m)
        anchor_starts_2d = anchor_starts.reshape(-1, 1)
        anchor_ends_2d = anchor_ends.reshape(-1, 1)
        tag_starts_2d = tag_starts.reshape(1, -1)
        tag_ends_2d = tag_ends.reshape(1, -1)
        
        # Overlap: tag_start <= anchor_end AND tag_end >= anchor_start
        overlaps = (tag_starts_2d <= anchor_ends_2d) & (tag_ends_2d >= anchor_starts_2d)
        counts = np.sum(overlaps, axis=1)
        return counts.astype(np.int64)
    
    # For large tag arrays, use binary search per anchor (still vectorized per anchor)
    counts = np.zeros(n_anchors, dtype=np.int64)
    for i in range(n_anchors):
        # Binary search to find relevant tag range
        right_idx = np.searchsorted(tag_starts, anchor_ends[i], side='right')
        if right_idx > 0:
            counts[i] = np.sum(tag_ends[:right_idx] >= anchor_starts[i])
    
    return counts


def _process_cluster_chunk(args):
    """
    Worker function for parallel cluster processing.
    Processes a chunk of clusters and returns tag overlap counts.
    
    This function must be at module level for multiprocessing pickle.
    Uses vectorized operations for maximum speed.
    """
    (start_idx, end_idx, chunk_chr1, chunk_start1, chunk_end1,
     chunk_chr2, chunk_start2, chunk_end2, chunk_ipets, tags_by_chr) = args
    
    n_clusters = len(chunk_chr1)
    
    # Group clusters by chromosome for vectorized processing
    chr_groups = defaultdict(lambda: {
        'anchor1_indices': [], 'anchor1_starts': [], 'anchor1_ends': [],
        'anchor2_indices': [], 'anchor2_starts': [], 'anchor2_ends': []
    })
    
    for i in range(n_clusters):
        chr1 = chunk_chr1[i]
        chr2 = chunk_chr2[i]
        
        chr_groups[chr1]['anchor1_indices'].append(i)
        chr_groups[chr1]['anchor1_starts'].append(chunk_start1[i])
        chr_groups[chr1]['anchor1_ends'].append(chunk_end1[i])
        
        chr_groups[chr2]['anchor2_indices'].append(i)
        chr_groups[chr2]['anchor2_starts'].append(chunk_start2[i])
        chr_groups[chr2]['anchor2_ends'].append(chunk_end2[i])
    
    # Initialize count arrays
    counts1 = np.zeros(n_clusters, dtype=np.int64)
    counts2 = np.zeros(n_clusters, dtype=np.int64)
    
    # Process each chromosome's anchors in batch
    for chr_name, group in chr_groups.items():
        if chr_name not in tags_by_chr:
            continue
        
        tag_starts = tags_by_chr[chr_name]['starts']
        tag_ends = tags_by_chr[chr_name]['ends']
        
        # Process anchor1 for this chromosome
        if 'anchor1_indices' in group and len(group['anchor1_indices']) > 0:
            indices = np.array(group['anchor1_indices'])
            starts = np.array(group['anchor1_starts'], dtype=np.int64)
            ends = np.array(group['anchor1_ends'], dtype=np.int64)
            overlap_counts = _count_overlaps_vectorized(tag_starts, tag_ends, starts, ends)
            counts1[indices] = overlap_counts
        
        # Process anchor2 for this chromosome
        if 'anchor2_indices' in group and len(group['anchor2_indices']) > 0:
            indices = np.array(group['anchor2_indices'])
            starts = np.array(group['anchor2_starts'], dtype=np.int64)
            ends = np.array(group['anchor2_ends'], dtype=np.int64)
            overlap_counts = _count_overlaps_vectorized(tag_starts, tag_ends, starts, ends)
            counts2[indices] = overlap_counts
    
    # Build result list
    counts = []
    for i in range(n_clusters):
        counts.append({
            'ipets_between': int(chunk_ipets[i]),
            'tags_anchor1': int(counts1[i]),
            'tags_anchor2': int(counts2[i])
        })
    
    return (start_idx, counts)


class PreClusterer:
    """
    Pre-clustering step for loop calling.
    
    Extends each PET tag by extension_length and creates cluster objects.
    Each cluster represents an anchor pair with extended regions.
    
    Reference logic from Pet2Cluster1.java:
    - For forward strand (+): extend upstream (position - extension)
    - For reverse strand (-): extend downstream (position + extension)
    - Sort head and tail regions by genomic location
    - Split by chromosome and merge
    """
    
    def __init__(self, 
                 extension_length: int = 500,
                 chrom_sizes_file: Optional[str] = None):
        """
        Initialize pre-clusterer.
        
        Args:
            extension_length: Extension length for each tag (default: 500bp)
            chrom_sizes_file: Path to chromosome sizes file (optional)
        """
        self.extension_length = extension_length
        self.chrom_sizes = {}
        
        if chrom_sizes_file and Path(chrom_sizes_file).exists():
            self._load_chrom_sizes(chrom_sizes_file)
        
        logger.info(f"PreClusterer initialized")
        logger.info(f"  Extension length: {extension_length}bp")
        logger.info(f"  Chromosome sizes: {len(self.chrom_sizes)} loaded" if self.chrom_sizes else "  Chromosome sizes: Not provided")
    
    def _load_chrom_sizes(self, chrom_sizes_file: str):
        """Load chromosome sizes from file."""
        logger.info(f"Loading chromosome sizes from: {chrom_sizes_file}")
        
        with open(chrom_sizes_file, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        chrom = parts[0]
                        size = int(parts[1])
                        self.chrom_sizes[chrom] = size
        
        logger.info(f"  Loaded {len(self.chrom_sizes)} chromosomes")
    
    def extend_tag(self, chrom: str, position: int, strand: str) -> Tuple[int, int]:
        """
        Extend a single tag based on strand orientation.
        
        Reference from CLUSTER.java constructor (lines 62-106):
        - Forward strand (+): extend upstream (pos - ext, pos)
        - Reverse strand (-): extend downstream (pos, pos + ext)
        
        Args:
            chrom: Chromosome name
            position: Tag position
            strand: Strand orientation (+ or -)
            
        Returns:
            Tuple of (start, end) coordinates
        """
        # Get chromosome size if available
        chrom_size = self.chrom_sizes.get(chrom, float('inf'))
        
        if strand == '+':
            # Forward strand: extend upstream
            start = max(1, position - self.extension_length)
            end = position
        else:
            # Reverse strand: extend downstream
            start = position
            end = min(chrom_size, position + self.extension_length)
        
        return (start, end)
    
    def create_cluster(self, pet_entry: pd.Series) -> Dict:
        """
        Create a cluster object from a PET entry.
        
        Reference from CLUSTER.java (lines 62-106):
        - Extend each anchor based on strand
        - Sort head and tail by genomic location
        
        Args:
            pet_entry: PET entry with columns:
                       chr1, pos1, strand1, chr2, pos2, strand2, name, score
            
        Returns:
            Dictionary with cluster information:
            {
                'chr1': chromosome of anchor 1,
                'start1': start of extended anchor 1,
                'end1': end of extended anchor 1,
                'chr2': chromosome of anchor 2,
                'start2': start of extended anchor 2,
                'end2': end of extended anchor 2,
                'weight': weight (default 1.0),
                'pet_index': PET identifier
            }
        """
        # Extract PET information
        chr1 = pet_entry['chr1']
        pos1 = int(float(pet_entry['pos1']))  # Handle float coordinates
        strand1 = pet_entry['strand1']
        
        chr2 = pet_entry['chr2']
        pos2 = int(float(pet_entry['pos2']))
        strand2 = pet_entry['strand2']
        
        weight = float(pet_entry.get('weight', 1.0))
        pet_index = pet_entry.get('name', '---')
        
        # Extend anchor 1
        start1, end1 = self.extend_tag(chr1, pos1, strand1)
        
        # Extend anchor 2
        start2, end2 = self.extend_tag(chr2, pos2, strand2)
        
        # Create cluster object
        cluster = {
            'chr1': chr1,
            'start1': start1,
            'end1': end1,
            'chr2': chr2,
            'start2': start2,
            'end2': end2,
            'weight': weight,
            'pet_index': pet_index
        }
        
        # Sort head and tail by genomic location
        # Reference: sortHeadTail() in CLUSTER.java (lines 149-155)
        cluster = self._sort_head_tail(cluster)
        
        return cluster
    
    def _sort_head_tail(self, cluster: Dict) -> Dict:
        """
        Sort head and tail regions by genomic location.
        
        Reference from CLUSTER.java sortHeadTail() (lines 149-155):
        - Compare head and tail regions
        - Swap if head > tail
        
        Args:
            cluster: Cluster dictionary
            
        Returns:
            Sorted cluster dictionary
        """
        # Compare regions: first by chromosome, then by start position
        head_chr = cluster['chr1']
        head_start = cluster['start1']
        tail_chr = cluster['chr2']
        tail_start = cluster['start2']
        
        # Swap if head > tail
        if (head_chr > tail_chr) or (head_chr == tail_chr and head_start > tail_start):
            cluster = {
                'chr1': tail_chr,
                'start1': cluster['start2'],
                'end1': cluster['end2'],
                'chr2': head_chr,
                'start2': head_start,
                'end2': cluster['end1'],
                'weight': cluster['weight'],
                'pet_index': cluster['pet_index']
            }
        
        return cluster
    
    def pre_cluster(self, 
                   ipet_file: str, 
                   output_prefix: str) -> Dict:
        """
        Run pre-clustering on iPET file.
        
        Reference from Pet2Cluster1.java preCluster() (lines 29-96):
        1. Read iPET file
        2. For each PET, create cluster with extended anchors
        3. Split by chromosome
        4. Sort each chromosome file
        5. Merge all sorted files
        
        Args:
            ipet_file: Input iPET file
            output_prefix: Output prefix for pre-cluster files
            
        Returns:
            Dictionary with statistics
        """
        logger.info("=" * 70)
        logger.info("STEP 6.1: PRE-CLUSTERING")
        logger.info("=" * 70)
        logger.info(f"Input iPET file: {ipet_file}")
        logger.info(f"Output prefix: {output_prefix}")
        logger.info(f"Extension length: {self.extension_length}bp")
        
        # Create output directory
        output_dir = Path(output_prefix).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read iPET file (skip comment lines)
        # Standard BEDPE format: chr1, start1, end1, chr2, start2, end2, name, score, strand1, strand2, [weight, ...]
        # HiChIP purified format may have extra columns (fragment indices)
        logger.info("Reading iPET file...")
        
        # First, detect number of columns
        with open(ipet_file, 'r') as f:
            first_line = f.readline().strip()
            num_cols = len(first_line.split('\t'))
        
        # Define column names based on number of columns
        base_cols = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2', 'name', 'score', 'strand1', 'strand2']
        if num_cols >= 11:
            col_names = base_cols + ['weight'] + [f'extra_{i}' for i in range(num_cols - 11)]
        else:
            col_names = base_cols[:num_cols]
        
        df = pd.read_csv(ipet_file, sep='\t', header=None, comment='#', names=col_names)
        
        # Filter out NaN rows in essential columns
        essential_cols = ['chr1', 'start1', 'chr2', 'start2', 'strand1', 'strand2']
        df = df.dropna(subset=[c for c in essential_cols if c in df.columns])
        
        # Add weight column if missing
        if 'weight' not in df.columns:
            df['weight'] = 1.0
        
        # Use only necessary columns (use start positions as anchor points)
        df = df[['chr1', 'start1', 'strand1', 'chr2', 'start2', 'strand2', 'name', 'weight']]
        # Rename for compatibility with create_cluster method
        df = df.rename(columns={'start1': 'pos1', 'start2': 'pos2'})
        
        num_pets = len(df)
        logger.info(f"  Loaded {num_pets:,} iPETs")
        
        # Process each PET and create clusters
        logger.info("Creating clusters...")
        clusters = []
        chr_files = {}  # Track files per chromosome
        
        for idx, pet in df.iterrows():
            cluster = self.create_cluster(pet)
            clusters.append(cluster)
            
            # Track chromosome for splitting
            chr1 = cluster['chr1']
            if chr1 not in chr_files:
                chr_files[chr1] = []
            chr_files[chr1].append(cluster)
            
            if (idx + 1) % 10000 == 0:
                logger.info(f"  Processed {idx + 1:,} / {num_pets:,} PETs")
        
        logger.info(f"  Created {len(clusters):,} clusters")
        logger.info(f"  Chromosomes: {len(chr_files)}")
        
        # Write clusters split by chromosome
        logger.info("Writing chromosome-specific files...")
        chr_file_paths = []
        
        for chrom in sorted(chr_files.keys()):
            chr_clusters = chr_files[chrom]
            chr_file = f"{output_prefix}.{chrom}.pre_cluster.txt"
            chr_file_paths.append(chr_file)
            
            with open(chr_file, 'w') as f:
                for cluster in chr_clusters:
                    # Format: chr1 start1 end1 chr2 start2 end2 weight pet_index
                    line = f"{cluster['chr1']}\t{cluster['start1']}\t{cluster['end1']}\t"
                    line += f"{cluster['chr2']}\t{cluster['start2']}\t{cluster['end2']}\t"
                    line += f"{cluster['weight']}\t{cluster['pet_index']}\n"
                    f.write(line)
            
            logger.info(f"  {chrom}: {len(chr_clusters):,} clusters -> {chr_file}")
        
        # Sort each chromosome file
        logger.info("Sorting chromosome files...")
        sorted_files = []
        
        for chr_file in chr_file_paths:
            sorted_file = chr_file.replace('.pre_cluster.txt', '.sort.pre_cluster.txt')
            self._sort_cluster_file(chr_file, sorted_file)
            sorted_files.append(sorted_file)
            
            # Remove unsorted file
            Path(chr_file).unlink()
        
        # Merge all sorted files
        logger.info("Merging sorted files...")
        merged_file = f"{output_prefix}.pre_cluster.sorted"
        self._merge_sorted_files(sorted_files, merged_file)
        
        # Clean up individual sorted files
        for sorted_file in sorted_files:
            Path(sorted_file).unlink()
        
        logger.info("=" * 70)
        logger.info("PRE-CLUSTERING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Input PETs: {num_pets:,}")
        logger.info(f"Output clusters: {len(clusters):,}")
        logger.info(f"Chromosomes processed: {len(chr_files)}")
        logger.info(f"Output file: {merged_file}")
        logger.info("=" * 70)
        
        return {
            'num_pets': num_pets,
            'num_clusters': len(clusters),
            'num_chromosomes': len(chr_files),
            'output_file': merged_file,
            'extension_length': self.extension_length
        }
    
    def _sort_cluster_file(self, input_file: str, output_file: str):
        """
        Sort cluster file by chr1, chr2, start1, start2.
        
        Reference: psort-cluster.sh in ChIA-PET Tool
        Sort order: column 1 (chr1), column 4 (chr2), column 2 (start1), column 5 (start2)
        
        Args:
            input_file: Input cluster file
            output_file: Output sorted file
        """
        # Read clusters
        df = pd.read_csv(input_file, sep='\t', header=None,
                        names=['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2', 'weight', 'pet_index'])
        
        # Sort by chr1, chr2, start1, start2
        df_sorted = df.sort_values(by=['chr1', 'chr2', 'start1', 'start2'])
        
        # Write sorted file
        df_sorted.to_csv(output_file, sep='\t', header=False, index=False)
        
        logger.info(f"  Sorted: {input_file} -> {output_file}")
    
    def _merge_sorted_files(self, sorted_files: list, output_file: str):
        """
        Merge sorted chromosome files into one file.
        
        Args:
            sorted_files: List of sorted chromosome files
            output_file: Output merged file
        """
        with open(output_file, 'w') as outf:
            for sorted_file in sorted_files:
                with open(sorted_file, 'r') as inf:
                    outf.write(inf.read())
        
        logger.info(f"  Merged {len(sorted_files)} files -> {output_file}")


class Anchor:
    """
    Represents a genomic anchor region.
    
    Reference: ANCHOR.java extends REGION.java
    An anchor is a genomic region that can be merged with overlapping anchors.
    """
    
    def __init__(self, chrom: str, start: int, end: int, ipets_intra: int = 0, ipets_inter: int = 0):
        """
        Initialize an anchor.
        
        Args:
            chrom: Chromosome name
            start: Start position
            end: End position
            ipets_intra: Number of intra-chromosomal PETs
            ipets_inter: Number of inter-chromosomal PETs
        """
        self.chrom = chrom
        self.start = start
        self.end = end
        self.ipets_intra = ipets_intra
        self.ipets_inter = ipets_inter
    
    def overlap(self, other: 'Anchor') -> bool:
        """
        Check if this anchor overlaps with another anchor.
        
        Args:
            other: Another anchor
            
        Returns:
            True if anchors overlap, False otherwise
        """
        if self.chrom != other.chrom:
            return False
        
        # Check if regions overlap
        return not (self.end < other.start or self.start > other.end)
    
    def combine(self, other: 'Anchor'):
        """
        Combine this anchor with another overlapping anchor.
        Extends the region to cover both anchors.
        
        Args:
            other: Another anchor to combine with
        """
        if self.chrom != other.chrom:
            raise ValueError(f"Cannot combine anchors from different chromosomes: {self.chrom} vs {other.chrom}")
        
        # Extend to cover both regions
        self.start = min(self.start, other.start)
        self.end = max(self.end, other.end)
        
        # Combine PET counts
        self.ipets_intra += other.ipets_intra
        self.ipets_inter += other.ipets_inter
    
    def compare_to(self, other: 'Anchor') -> int:
        """
        Compare this anchor to another for sorting.
        
        Args:
            other: Another anchor
            
        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        # First compare by chromosome
        if self.chrom < other.chrom:
            return -1
        elif self.chrom > other.chrom:
            return 1
        
        # Then compare by start position
        if self.start < other.start:
            return -1
        elif self.start > other.start:
            return 1
        
        # Finally compare by end position
        if self.end < other.end:
            return -1
        elif self.end > other.end:
            return 1
        
        return 0
    
    def __str__(self):
        """String representation."""
        return f"{self.chrom}\t{self.start}\t{self.end}\t{self.ipets_intra}\t{self.ipets_inter}"


class AnchorCluster:
    """
    Represents a cluster of anchors (an interaction between two anchor regions).
    
    Reference: AnchorCluster.java
    Contains two anchors (head and tail) and the number of PETs between them.
    """
    
    def __init__(self, head: Anchor, tail: Anchor, ipets_between: int, pet_indexes: str = "---"):
        """
        Initialize an anchor cluster.
        
        Args:
            head: Head anchor
            tail: Tail anchor
            ipets_between: Number of PETs between the anchors
            pet_indexes: PET identifiers (optional)
        """
        self.head = head
        self.tail = tail
        self.ipets_between = ipets_between
        self.score = 0.0
        self.searched = False
        self.pet_indexes = pet_indexes
        
        # Sort head and tail by genomic location
        self._sort_head_tail()
    
    def _sort_head_tail(self):
        """Sort head and tail anchors by genomic location."""
        if self.head.compare_to(self.tail) > 0:
            self.head, self.tail = self.tail, self.head
    
    def overlap(self, other: 'AnchorCluster') -> bool:
        """
        Check if this cluster overlaps with another cluster.
        Both head AND tail must overlap.
        
        Args:
            other: Another anchor cluster
            
        Returns:
            True if both anchors overlap, False otherwise
        """
        return self.head.overlap(other.head) and self.tail.overlap(other.tail)
    
    def combine(self, other: 'AnchorCluster'):
        """
        Combine this cluster with another overlapping cluster.
        
        Args:
            other: Another cluster to combine with
        """
        # Combine head anchors
        self.head.combine(other.head)
        
        # Combine tail anchors
        self.tail.combine(other.tail)
        
        # Sum PET counts
        self.ipets_between += other.ipets_between
    
    def compare_to(self, other: 'AnchorCluster') -> int:
        """
        Compare this cluster to another for sorting.
        
        Args:
            other: Another cluster
            
        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        # First compare by head
        result = self.head.compare_to(other.head)
        if result != 0:
            return result
        
        # Then compare by tail
        return self.tail.compare_to(other.tail)
    
    def calculate_distance(self) -> int:
        """
        Calculate distance between head and tail anchors.
        
        Returns:
            Distance in base pairs, or -1 if different chromosomes
        """
        if self.head.chrom != self.tail.chrom:
            return -1
        
        # Distance between anchor centers
        head_center = (self.head.start + self.head.end) // 2
        tail_center = (self.tail.start + self.tail.end) // 2
        return abs(tail_center - head_center)
    
    def is_same_chromosome(self) -> bool:
        """Check if head and tail are on the same chromosome."""
        return self.head.chrom == self.tail.chrom
    
    def __str__(self):
        """
        String representation matching reference format.
        
        Format: chr1 start1 end1 ipets1_intra ipets1_inter 
                chr2 start2 end2 ipets2_intra ipets2_inter 
                ipets_between same_chr distance score pet_indexes
        """
        same_chr = 1 if self.is_same_chromosome() else 0
        distance = self.calculate_distance()
        
        return (f"{self.head}\t{self.tail}\t{self.ipets_between}\t"
                f"{same_chr}\t{distance}\t{self.score}\t{self.pet_indexes}")


class AnchorClusterer:
    """
    Step 6.2: Anchor Clustering
    
    Merges overlapping anchor clusters iteratively.
    
    Reference: PetCluster2.java
    Algorithm:
    1. Read pre-clusters chromosome-pair by chromosome-pair
    2. For each batch, create AnchorClusters
    3. Iteratively merge overlapping clusters (both head AND tail must overlap)
    4. Repeat until no more merges possible
    """
    
    def __init__(self, debug_level: int = 4):
        """
        Initialize anchor clusterer.
        
        Args:
            debug_level: Debug verbosity level (default: 4)
        """
        self.debug_level = debug_level
        
        logger.info(f"AnchorClusterer initialized")
        logger.info(f"  Debug level: {debug_level}")
    
    def cluster_anchors(self, 
                       precluster_file: str, 
                       output_file: str) -> Dict:
        """
        Run anchor clustering on pre-cluster file.
        
        Reference from PetCluster2.java (lines 48-96):
        1. Read pre-clusters sorted by chr1, chr2
        2. Process chromosome-pair batches
        3. Generate and merge anchor clusters
        4. Output merged clusters
        
        Args:
            precluster_file: Input pre-cluster file (sorted)
            output_file: Output cluster file
            
        Returns:
            Dictionary with statistics
        """
        logger.info("=" * 70)
        logger.info("STEP 6.2: ANCHOR CLUSTERING")
        logger.info("=" * 70)
        logger.info(f"Input file: {precluster_file}")
        logger.info(f"Output file: {output_file}")
        
        # Create output directory
        output_dir = Path(output_file).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read pre-clusters
        logger.info("Reading pre-clusters...")
        df = pd.read_csv(precluster_file, sep='\t', header=None,
                        names=['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2', 
                              'weight', 'pet_index'])
        
        total_preclusters = len(df)
        logger.info(f"  Loaded {total_preclusters:,} pre-clusters")
        
        # Process chromosome-pair batches
        all_anchor_clusters = []
        current_chr1 = None
        current_chr2 = None
        batch_clusters = []
        batch_count = 0
        
        logger.info("Processing chromosome-pair batches...")
        
        for idx, row in df.iterrows():
            chr1 = row['chr1']
            chr2 = row['chr2']
            
            # Check if we need to process the current batch
            if current_chr1 is not None and (chr1 != current_chr1 or chr2 != current_chr2):
                # Process current batch
                batch_count += 1
                logger.info(f"  Batch {batch_count}: {current_chr1} <-> {current_chr2} ({len(batch_clusters):,} pre-clusters)")
                
                merged = self._generate_clusters(batch_clusters)
                all_anchor_clusters.extend(merged)
                
                logger.info(f"    Merged to {len(merged):,} anchor clusters")
                
                # Start new batch
                batch_clusters = []
            
            # Update current chromosome pair
            current_chr1 = chr1
            current_chr2 = chr2
            
            # Create cluster from row
            head = Anchor(row['chr1'], int(row['start1']), int(row['end1']))
            tail = Anchor(row['chr2'], int(row['start2']), int(row['end2']))
            weight = int(row['weight'])
            pet_index = str(row['pet_index'])
            
            cluster = AnchorCluster(head, tail, weight, pet_index)
            batch_clusters.append(cluster)
            
            if (idx + 1) % 10000 == 0:
                logger.info(f"  Processed {idx + 1:,} / {total_preclusters:,} pre-clusters")
        
        # Process final batch
        if batch_clusters:
            batch_count += 1
            logger.info(f"  Batch {batch_count}: {current_chr1} <-> {current_chr2} ({len(batch_clusters):,} pre-clusters)")
            
            merged = self._generate_clusters(batch_clusters)
            all_anchor_clusters.extend(merged)
            
            logger.info(f"    Merged to {len(merged):,} anchor clusters")
        
        # Write output
        logger.info("Writing anchor clusters...")
        with open(output_file, 'w') as f:
            for cluster in all_anchor_clusters:
                f.write(str(cluster) + '\n')
        
        logger.info("=" * 70)
        logger.info("ANCHOR CLUSTERING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Input pre-clusters: {total_preclusters:,}")
        logger.info(f"Output anchor clusters: {len(all_anchor_clusters):,}")
        logger.info(f"Chromosome-pair batches: {batch_count}")
        logger.info(f"Reduction: {total_preclusters - len(all_anchor_clusters):,} clusters merged")
        logger.info(f"Output file: {output_file}")
        logger.info("=" * 70)
        
        return {
            'num_preclusters': total_preclusters,
            'num_anchor_clusters': len(all_anchor_clusters),
            'num_batches': batch_count,
            'num_merged': total_preclusters - len(all_anchor_clusters),
            'output_file': output_file
        }
    
    def _generate_clusters(self, clusters: List[AnchorCluster]) -> List[AnchorCluster]:
        """
        Generate merged anchor clusters from a list of clusters.
        
        Reference from PetCluster2.java generateClusters() (lines 109-124):
        Iteratively merge overlapping clusters until no more merges possible.
        
        Args:
            clusters: List of anchor clusters
            
        Returns:
            List of merged anchor clusters
        """
        if not clusters:
            return []
        
        anchor_clusters = clusters.copy()
        
        # Iteratively merge until no more merges possible
        old_size = -1
        new_size = len(anchor_clusters)
        iteration = 0
        
        while old_size != new_size:
            iteration += 1
            old_size = new_size
            anchor_clusters = self._merge_anchor_clusters(anchor_clusters)
            new_size = len(anchor_clusters)
            
            if self.debug_level > 3 and old_size != new_size:
                logger.info(f"      Iteration {iteration}: {old_size} -> {new_size} clusters")
        
        return anchor_clusters
    
    def _merge_anchor_clusters(self, old_clusters: List[AnchorCluster]) -> List[AnchorCluster]:
        """
        Merge overlapping anchor clusters.
        
        Reference from PetCluster2.java mergeAnchorClusters() (lines 126-194):
        1. Sort clusters
        2. For each cluster, find overlapping clusters
        3. Merge if both head AND tail overlap
        4. Mark merged clusters as searched
        
        Args:
            old_clusters: List of anchor clusters to merge
            
        Returns:
            List of merged anchor clusters
        """
        if len(old_clusters) <= 1:
            return old_clusters
        
        # Sort clusters
        sorted_clusters = sorted(old_clusters, key=lambda c: (c.head.chrom, c.head.start, 
                                                              c.tail.chrom, c.tail.start))
        
        # Reset searched flags
        for cluster in sorted_clusters:
            cluster.searched = False
        
        new_clusters = []
        i = 0
        
        while i < len(sorted_clusters):
            if sorted_clusters[i].searched:
                i += 1
                continue
            
            current = sorted_clusters[i]
            current.searched = True
            
            # Look for overlapping clusters
            for j in range(i + 1, len(sorted_clusters)):
                # If head doesn't overlap, no point checking further
                if not current.head.overlap(sorted_clusters[j].head):
                    break
                
                # Skip already merged clusters
                if sorted_clusters[j].searched:
                    continue
                
                # Check if both head AND tail overlap
                if current.tail.overlap(sorted_clusters[j].tail):
                    # Merge clusters
                    current.combine(sorted_clusters[j])
                    sorted_clusters[j].searched = True
            
            new_clusters.append(current)
            i += 1
        
        return new_clusters


class StatisticalSignificance:
    """
    Step 6.3: Statistical Significance Testing
    
    Calculates statistical significance of chromatin loops using:
    1. Tag counting in anchor regions
    2. Distance-corrected statistical test (for HiChIP) or hypergeometric test (for ChIA-PET)
    3. Benjamini-Hochberg FDR correction
    4. P-value filtering
    
    For HiChIP data, uses a Fit-Hi-C style distance-corrected approach that accounts
    for the distance-dependent decay in contact frequency due to polymer physics.
    
    Reference: Pvalues.java, hypergeometric.r, Fit-Hi-C (Ay et al. 2014)
    """
    
    def __init__(self, 
                 ipet_count_threshold: int = 2,
                 pvalue_cutoff: float = 0.05,
                 extension_length: int = 500,
                 use_distance_correction: bool = True,
                 distance_bin_size: int = 5000):
        """
        Initialize statistical significance calculator.
        
        Args:
            ipet_count_threshold: Minimum iPET count to consider (default: 2)
            pvalue_cutoff: P-value cutoff for filtering (default: 0.05)
            extension_length: Extension length for tag counting (default: 500bp)
            use_distance_correction: Use distance-corrected test for HiChIP (default: True)
            distance_bin_size: Size of distance bins in bp for background model (default: 5000)
        """
        self.ipet_count_threshold = ipet_count_threshold
        self.pvalue_cutoff = pvalue_cutoff
        self.extension_length = extension_length
        self.use_distance_correction = use_distance_correction
        self.distance_bin_size = distance_bin_size
        
        logger.info(f"StatisticalSignificance initialized")
        logger.info(f"  iPET count threshold: {ipet_count_threshold}")
        logger.info(f"  P-value cutoff: {pvalue_cutoff}")
        logger.info(f"  Extension length: {extension_length}bp")
        logger.info(f"  Distance correction: {'Enabled (HiChIP mode)' if use_distance_correction else 'Disabled (ChIA-PET mode)'}")
        if use_distance_correction:
            logger.info(f"  Distance bin size: {distance_bin_size}bp")
    
    def calculate_significance(self,
                              cluster_file: str,
                              ipet_file: str,
                              output_prefix: str) -> Dict:
        """
        Calculate statistical significance for chromatin loops.
        
        Reference from Pvalues.java:
        1. Filter clusters by iPET count
        2. Count tags in anchor regions
        3. Run hypergeometric test
        4. Apply FDR correction
        5. Filter by p-value
        
        Args:
            cluster_file: Input anchor cluster file
            ipet_file: Input iPET file for tag counting
            output_prefix: Output prefix
            
        Returns:
            Dictionary with statistics
        """
        logger.info("=" * 70)
        logger.info("STEP 6.3: STATISTICAL SIGNIFICANCE")
        logger.info("=" * 70)
        logger.info(f"Cluster file: {cluster_file}")
        logger.info(f"iPET file: {ipet_file}")
        logger.info(f"Output prefix: {output_prefix}")
        
        # Create output directory
        output_dir = Path(output_prefix).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Filter clusters by iPET count
        logger.info(f"\nStep 1: Filtering clusters (iPET >= {self.ipet_count_threshold})...")
        filtered_file = f"{output_prefix}.cluster.filtered"
        num_filtered = self._filter_clusters(cluster_file, filtered_file)
        logger.info(f"  Filtered clusters: {num_filtered:,}")
        
        # Step 2: Count tags in anchor regions
        logger.info(f"\nStep 2: Counting tags in anchor regions...")
        tag_counts = self._count_tags_in_anchors(filtered_file, ipet_file)
        logger.info(f"  Tag counts calculated for {len(tag_counts):,} clusters")
        
        # Step 3: Calculate total tags
        total_tags = self._count_total_tags(ipet_file)
        logger.info(f"  Total tags: {total_tags:,}")
        
        # Step 4: Run statistical test (distance-corrected for HiChIP or hypergeometric for ChIA-PET)
        if self.use_distance_correction:
            logger.info(f"\nStep 3: Running distance-corrected statistical test (HiChIP mode)...")
            results = self._distance_corrected_test(filtered_file, tag_counts, total_tags)
        else:
            logger.info(f"\nStep 3: Running hypergeometric test (ChIA-PET mode)...")
            results = self._hypergeometric_test(tag_counts, total_tags)
        logger.info(f"  Statistical tests completed")
        
        # Step 5: Apply FDR correction
        logger.info(f"\nStep 4: Applying FDR correction (Benjamini-Hochberg)...")
        results = self._apply_fdr_correction(results)
        logger.info(f"  FDR correction applied")
        
        # Step 6: Combine results with cluster data
        logger.info(f"\nStep 5: Combining results...")
        output_file = f"{output_prefix}.cluster.FDRfiltered.txt"
        num_significant, num_fdr_005, num_fdr_001 = self._write_results(filtered_file, results, output_file)
        
        logger.info("=" * 70)
        logger.info("STATISTICAL SIGNIFICANCE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Input clusters: {num_filtered:,}")
        logger.info(f"Significant loops (FDR < {self.pvalue_cutoff}): {num_significant:,}")
        if num_filtered > 0:
            logger.info(f"Percentage significant: {num_significant/num_filtered*100:.1f}%")
            logger.info(f"FDR < 0.05: {num_fdr_005:,} ({num_fdr_005/num_filtered*100:.1f}%)")
            logger.info(f"FDR < 0.01: {num_fdr_001:,} ({num_fdr_001/num_filtered*100:.1f}%)")
        else:
            logger.warning("No clusters passed iPET count filter")
        logger.info(f"Output file: {output_file}")
        logger.info("=" * 70)
        
        return {
            'num_input_clusters': num_filtered,
            'num_significant_loops': num_significant,
            'num_fdr_005': num_fdr_005,
            'num_fdr_001': num_fdr_001,
            'pvalue_cutoff': self.pvalue_cutoff,
            'output_file': output_file,
            'total_tags': total_tags
        }
    
    def _filter_clusters(self, cluster_file: str, output_file: str) -> int:
        """
        Filter clusters by iPET count threshold.
        
        Args:
            cluster_file: Input cluster file
            output_file: Output filtered file
            
        Returns:
            Number of filtered clusters
        """
        df = pd.read_csv(cluster_file, sep='\t', header=None,
                        names=['chr1', 'start1', 'end1', 'ipets1_intra', 'ipets1_inter',
                              'chr2', 'start2', 'end2', 'ipets2_intra', 'ipets2_inter',
                              'ipets_between', 'same_chr', 'distance', 'score', 'pet_indexes'])
        
        # Filter by iPET count
        df_filtered = df[df['ipets_between'] >= self.ipet_count_threshold]
        
        # Write filtered clusters
        df_filtered.to_csv(output_file, sep='\t', header=False, index=False)

        return len(df_filtered)

    def _count_tags_in_anchors(self, cluster_file: str, ipet_file: str) -> List[Dict]:
        """
        Count EXTENDED tags in anchor regions - MEMORY OPTIMIZED VERSION.

        Reference: ChIA-PET Tool paper (2010, 2019)
        - Extend each tag by extension_length in 5' to 3' direction
        - Count how many extended tags from ALL inter-ligation PETs overlap each anchor

        This version uses chunked processing and numpy arrays to minimize memory usage.

        Args:
            cluster_file: Filtered cluster file
            ipet_file: iPET file (contains ALL inter-ligation PETs)

        Returns:
            List of dictionaries with tag counts
        """
        # Read clusters
        clusters = pd.read_csv(cluster_file, sep='\t', header=None,
                              names=['chr1', 'start1', 'end1', 'ipets1_intra', 'ipets1_inter',
                                    'chr2', 'start2', 'end2', 'ipets2_intra', 'ipets2_inter',
                                    'ipets_between', 'same_chr', 'distance', 'score', 'pet_indexes'])
        
        logger.info(f"    Extension length: {self.extension_length} bp")
        logger.info(f"    Total clusters to process: {len(clusters):,}")

        # Detect column count for HiChIP compatibility
        with open(ipet_file, 'r') as f:
            first_line = f.readline().strip()
            num_cols = len(first_line.split('\t'))
        
        # Count total iPETs first (memory efficient line count)
        total_ipets = sum(1 for _ in open(ipet_file, 'r'))
        logger.info(f"    Total inter-ligation PETs: {total_ipets:,}")
        logger.info(f"    Building tag index by chromosome (memory-optimized)...")

        # Build tag arrays by chromosome using chunked processing
        # Store only (start, end) as numpy arrays per chromosome
        tags_by_chr = defaultdict(lambda: {'starts': [], 'ends': []})
        
        chunk_size = 100000
        base_cols = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2', 'name', 'score', 'strand1', 'strand2']
        if num_cols >= 11:
            col_names = base_cols + ['weight'] + [f'extra_{i}' for i in range(num_cols - 11)]
        else:
            col_names = base_cols[:num_cols]
        
        chunks_processed = 0
        for chunk in pd.read_csv(ipet_file, sep='\t', header=None, comment='#', 
                                  names=col_names, chunksize=chunk_size):
            # Filter out NaN rows in essential columns
            essential_cols = ['chr1', 'start1', 'chr2', 'start2', 'strand1', 'strand2']
            chunk = chunk.dropna(subset=[c for c in essential_cols if c in chunk.columns])
            
            for _, ipet in chunk.iterrows():
                # Tag 1 (left end of iPET)
                pos1 = int(float(ipet['start1']))
                strand1 = ipet['strand1']
                if strand1 == '+':
                    tag1_start = max(0, pos1 - self.extension_length)
                    tag1_end = pos1
                else:
                    tag1_start = pos1
                    tag1_end = pos1 + self.extension_length
                chr1 = ipet['chr1']
                tags_by_chr[chr1]['starts'].append(tag1_start)
                tags_by_chr[chr1]['ends'].append(tag1_end)

                # Tag 2 (right end of iPET)
                pos2 = int(float(ipet['start2']))
                strand2 = ipet['strand2']
                if strand2 == '+':
                    tag2_start = max(0, pos2 - self.extension_length)
                    tag2_end = pos2
                else:
                    tag2_start = pos2
                    tag2_end = pos2 + self.extension_length
                chr2 = ipet['chr2']
                tags_by_chr[chr2]['starts'].append(tag2_start)
                tags_by_chr[chr2]['ends'].append(tag2_end)
            
            chunks_processed += 1
            if chunks_processed % 10 == 0:
                logger.info(f"      Processed {chunks_processed * chunk_size:,} iPETs...")
        
        # Convert lists to numpy arrays and sort by start position for binary search
        logger.info(f"    Converting to numpy arrays and sorting...")
        for chr_name in tags_by_chr:
            starts = np.array(tags_by_chr[chr_name]['starts'], dtype=np.int64)
            ends = np.array(tags_by_chr[chr_name]['ends'], dtype=np.int64)
            
            # Sort by start position for binary search
            sort_idx = np.argsort(starts)
            tags_by_chr[chr_name]['starts'] = starts[sort_idx]
            tags_by_chr[chr_name]['ends'] = ends[sort_idx]
        
        total_tags = sum(len(v['starts']) for v in tags_by_chr.values())
        logger.info(f"    Total extended tags indexed: {total_tags:,} (2 per iPET)")

        # Count extended tags that OVERLAP each anchor region using parallel processing
        n_clusters = len(clusters)
        logger.info(f"    Counting tag overlaps for {n_clusters:,} clusters...")
        
        # Determine number of workers
        n_workers = max(1, min(mp.cpu_count() - 2, 24))
        logger.info(f"    Using {n_workers} parallel workers")
        
        # Prepare cluster data as numpy arrays for efficient parallel processing
        cluster_chr1 = clusters['chr1'].values
        cluster_start1 = clusters['start1'].values.astype(np.int64)
        cluster_end1 = clusters['end1'].values.astype(np.int64)
        cluster_chr2 = clusters['chr2'].values
        cluster_start2 = clusters['start2'].values.astype(np.int64)
        cluster_end2 = clusters['end2'].values.astype(np.int64)
        cluster_ipets = clusters['ipets_between'].values.astype(np.int64)
        
        # Process clusters in parallel using multiprocessing Pool
        # Split work into chunks for each worker
        chunk_size = max(1000, n_clusters // (n_workers * 10))  # ~10 chunks per worker
        
        # Prepare arguments for parallel processing
        chunk_args = []
        for start_idx in range(0, n_clusters, chunk_size):
            end_idx = min(start_idx + chunk_size, n_clusters)
            chunk_args.append((
                start_idx, end_idx,
                cluster_chr1[start_idx:end_idx],
                cluster_start1[start_idx:end_idx],
                cluster_end1[start_idx:end_idx],
                cluster_chr2[start_idx:end_idx],
                cluster_start2[start_idx:end_idx],
                cluster_end2[start_idx:end_idx],
                cluster_ipets[start_idx:end_idx],
                dict(tags_by_chr)  # Pass copy of tag data
            ))
        
        logger.info(f"    Processing {len(chunk_args)} chunks of ~{chunk_size:,} clusters each...")
        
        # Process chunks in parallel
        tag_counts = [None] * n_clusters  # Pre-allocate for ordered results
        processed = 0
        
        with mp.Pool(processes=n_workers) as pool:
            results = pool.imap_unordered(_process_cluster_chunk, chunk_args)
            
            for chunk_result in results:
                start_idx, counts = chunk_result
                for i, count in enumerate(counts):
                    tag_counts[start_idx + i] = count
                processed += len(counts)
                
                if processed % (chunk_size * 20) < chunk_size or processed == n_clusters:
                    logger.info(f"    Processed {processed:,} / {n_clusters:,} clusters ({100*processed/n_clusters:.1f}%)")

        # Log tag count statistics
        if tag_counts:
            m_values = [tc['tags_anchor1'] for tc in tag_counts]
            k_values = [tc['tags_anchor2'] for tc in tag_counts]
            logger.info(f"    Tag count stats (anchor1 m): min={min(m_values)}, max={max(m_values)}, median={sorted(m_values)[len(m_values)//2]}")
            logger.info(f"    Tag count stats (anchor2 k): min={min(k_values)}, max={max(k_values)}, median={sorted(k_values)[len(k_values)//2]}")
        else:
            logger.warning("    No clusters to count tags for")

        return tag_counts

    def _count_total_tags(self, ipet_file: str) -> int:
        """
        Count total number of inter-ligation PETs (N).
        
        Reference: ChIA-PET Tool paper (2010, 2019)
        N = total number of inter-ligation PETs in the library
        
        The hypergeometric test uses 2*N as the total number of ends
        (since each PET has 2 tags/ends).
        
        Args:
            ipet_file: iPET file
            
        Returns:
            Total number of inter-ligation PETs (N)
        """
        # Detect column count for HiChIP compatibility
        with open(ipet_file, 'r') as f:
            first_line = f.readline().strip()
            num_cols = len(first_line.split('\t'))
        
        base_cols = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2', 'name', 'score', 'strand1', 'strand2']
        if num_cols >= 11:
            col_names = base_cols + ['weight'] + [f'extra_{i}' for i in range(num_cols - 11)]
        else:
            col_names = base_cols[:num_cols]
        
        ipets = pd.read_csv(ipet_file, sep='\t', header=None, comment='#', names=col_names)
        ipets = ipets.dropna(subset=[c for c in ['chr1', 'start1', 'chr2', 'start2'] if c in ipets.columns])
        
        # Return total number of inter-ligation PETs
        # The hypergeometric test will use 2*N for total ends
        return len(ipets)
    
    def _hypergeometric_test(self, tag_counts: List[Dict], total_ipets: int) -> List[Dict]:
        """
        Run hypergeometric test for each cluster.
        
        Reference: ChIA-PET Tool paper (2010, 2019) Equation 1
        
        The test asks: "When c_B ends are randomly chosen from 2N ends as ends 
        in region R_B, what is the probability of choosing I_A,B ends from 
        c_A ends of region R_A?"
        
        Parameters (from paper):
        - N = total number of inter-ligation PETs in the library
        - 2N = total number of ends (each PET has 2 ends)
        - c_A = number of extended tag ends overlapping anchor A
        - c_B = number of extended tag ends overlapping anchor B
        - I_A,B = number of inter-ligation PETs between anchors A and B
        
        Hypergeometric test: P(X >= I_A,B | 2N, c_A, c_B)
        
        Args:
            tag_counts: List of tag count dictionaries
            total_ipets: Total number of inter-ligation PETs (N)
            
        Returns:
            List of dictionaries with p-values
        """
        from scipy.stats import hypergeom
        
        # Total ends = 2 * N (each iPET has 2 ends)
        total_ends = 2 * total_ipets
        
        results = []
        debug_count = 0
        for idx, counts in enumerate(tag_counts):
            # From the paper:
            # I_A,B = iPETs between anchors (observed interaction count)
            # c_A = extended tags overlapping anchor A
            # c_B = extended tags overlapping anchor B
            # 2N = total ends
            
            observed_ipets = counts['ipets_between']  # I_A,B
            c_A = counts['tags_anchor1']  # Extended tags in anchor A
            c_B = counts['tags_anchor2']  # Extended tags in anchor B
            
            # Hypergeometric test (upper tail)
            # P(X >= observed_ipets) = hypergeom.sf(observed_ipets - 1, 2N, c_A, c_B)
            # Tests: "What's the probability of seeing at least this many iPETs
            #         between these anchors by chance?"
            if c_A > 0 and c_B > 0 and observed_ipets > 0:
                # sf(k, M, n, N) = P(X > k) = 1 - P(X <= k)
                # We want P(X >= observed), so use sf(observed - 1)
                pvalue = hypergeom.sf(observed_ipets - 1, total_ends, c_A, c_B)
            else:
                pvalue = 1.0  # No enrichment if no tags
            
            # Debug logging for first 10 clusters
            if debug_count < 10:
                logger.info(f"  DEBUG Cluster {idx}: iPET={observed_ipets}, "
                           f"c_A={c_A}, c_B={c_B}, 2N={total_ends}, "
                           f"pval={pvalue:.3e}")
                debug_count += 1
            
            results.append({
                'ipets_between': observed_ipets,
                'tags_anchor1': c_A,
                'tags_anchor2': c_B,
                'pvalue': pvalue
            })
        
        # Log p-value distribution statistics
        import numpy as np
        pvalues = [r['pvalue'] for r in results]
        logger.info(f"\n  P-value distribution:")
        if pvalues:
            pval_array = np.array(pvalues)
            logger.info(f"    Min: {pval_array.min():.3e}")
            logger.info(f"    Max: {pval_array.max():.3e}")
            logger.info(f"    Median: {np.median(pval_array):.3e}")
            logger.info(f"    Mean: {np.mean(pval_array):.3e}")
            logger.info(f"    P < 0.001: {(pval_array < 0.001).sum()} ({(pval_array < 0.001).sum()/len(pval_array)*100:.1f}%)")
            logger.info(f"    P < 0.01: {(pval_array < 0.01).sum()} ({(pval_array < 0.01).sum()/len(pval_array)*100:.1f}%)")
            logger.info(f"    P < 0.05: {(pval_array < 0.05).sum()} ({(pval_array < 0.05).sum()/len(pval_array)*100:.1f}%)")
        else:
            logger.warning("    No p-values to compute (empty results)")
        
        return results
    
    def _distance_corrected_test(self, cluster_file: str, tag_counts: List[Dict], total_ipets: int) -> List[Dict]:
        """
        Distance-corrected statistical test for HiChIP data.
        
        Uses a Fit-Hi-C style approach that accounts for distance-dependent contact frequency:
        1. Bin interactions by genomic distance
        2. Calculate expected contact probability per distance bin
        3. Use binomial test comparing observed vs expected counts
        
        This corrects for the polymer physics effect where nearby loci interact
        more frequently simply due to 3D proximity.
        
        Reference: Fit-Hi-C (Ay et al. 2014), Mango (Phanstiel et al. 2015)
        
        Args:
            cluster_file: Filtered cluster file with distance information
            tag_counts: List of tag count dictionaries
            total_ipets: Total number of inter-ligation PETs
            
        Returns:
            List of dictionaries with p-values
        """
        from scipy.stats import poisson, nbinom
        
        # Read cluster file to get distances
        df = pd.read_csv(cluster_file, sep='\t', header=None,
                        names=['chr1', 'start1', 'end1', 'ipets1_intra', 'ipets1_inter',
                              'chr2', 'start2', 'end2', 'ipets2_intra', 'ipets2_inter',
                              'ipets_between', 'same_chr', 'distance', 'score', 'pet_indexes'])
        
        distances = df['distance'].values
        same_chr = df['same_chr'].values
        ipet_counts = df['ipets_between'].values
        
        logger.info(f"    Building distance-dependent background model...")
        logger.info(f"    Distance bin size: {self.distance_bin_size:,} bp")
        
        # Step 1: Build distance-dependent background model for intra-chromosomal contacts
        # Bin interactions by distance and calculate mean contact frequency per bin
        intra_mask = same_chr == 1
        intra_distances = distances[intra_mask]
        intra_ipets = ipet_counts[intra_mask]
        
        # Create distance bins (log-scale for better resolution at short distances)
        max_distance = max(intra_distances) if len(intra_distances) > 0 else 1e8
        min_distance = max(1, min(intra_distances)) if len(intra_distances) > 0 else 1
        
        # Use log-spaced bins for better resolution
        n_bins = max(50, int(np.log10(max_distance / min_distance) * 20))
        bin_edges = np.logspace(np.log10(min_distance), np.log10(max_distance + 1), n_bins + 1)
        
        # Calculate mean iPET count per distance bin
        bin_indices = np.digitize(intra_distances, bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)
        
        bin_sums = np.zeros(n_bins)
        bin_counts = np.zeros(n_bins)
        
        for i in range(len(intra_distances)):
            bin_idx = bin_indices[i]
            bin_sums[bin_idx] += intra_ipets[i]
            bin_counts[bin_idx] += 1
        
        # Calculate expected iPET count per bin (mean)
        bin_means = np.zeros(n_bins)
        for i in range(n_bins):
            if bin_counts[i] > 0:
                bin_means[i] = bin_sums[i] / bin_counts[i]
            else:
                bin_means[i] = 0
        
        # Smooth the background model using a rolling average
        window_size = 5
        smoothed_means = np.convolve(bin_means, np.ones(window_size)/window_size, mode='same')
        
        # For inter-chromosomal contacts, use a separate (much lower) expected value
        inter_mask = same_chr == 0
        if inter_mask.sum() > 0:
            inter_expected = np.mean(ipet_counts[inter_mask])
        else:
            inter_expected = 0.1  # Very low expected for inter-chromosomal
        
        logger.info(f"    Intra-chromosomal contacts: {intra_mask.sum():,}")
        logger.info(f"    Inter-chromosomal contacts: {inter_mask.sum():,}")
        logger.info(f"    Distance bins: {n_bins}")
        logger.info(f"    Inter-chromosomal expected: {inter_expected:.3f}")
        
        # Step 2: Calculate p-values using Poisson test
        logger.info(f"    Calculating distance-corrected p-values...")
        
        results = []
        debug_count = 0
        
        for idx, counts in enumerate(tag_counts):
            observed_ipets = counts['ipets_between']
            c_A = counts['tags_anchor1']
            c_B = counts['tags_anchor2']
            
            is_intra = same_chr[idx] == 1
            distance = distances[idx]
            
            if is_intra:
                # Get expected count from distance-dependent model
                bin_idx = np.searchsorted(bin_edges, distance) - 1
                bin_idx = max(0, min(bin_idx, n_bins - 1))
                expected = max(smoothed_means[bin_idx], 0.1)  # Minimum expected of 0.1
            else:
                expected = max(inter_expected, 0.1)
            
            # Poisson test: P(X >= observed | lambda = expected)
            # Using survival function: sf(k) = P(X > k)
            if observed_ipets > 0 and expected > 0:
                pvalue = poisson.sf(observed_ipets - 1, expected)
            else:
                pvalue = 1.0
            
            # Debug logging for first 10 clusters
            if debug_count < 10:
                logger.info(f"  DEBUG Cluster {idx}: iPET={observed_ipets}, "
                           f"expected={expected:.2f}, distance={distance:,}, "
                           f"intra={is_intra}, pval={pvalue:.3e}")
                debug_count += 1
            
            results.append({
                'ipets_between': observed_ipets,
                'tags_anchor1': c_A,
                'tags_anchor2': c_B,
                'expected': expected,
                'distance': distance,
                'pvalue': pvalue
            })
        
        # Log p-value distribution statistics
        pvalues = [r['pvalue'] for r in results]
        logger.info(f"\n  P-value distribution (distance-corrected):")
        if pvalues:
            pval_array = np.array(pvalues)
            logger.info(f"    Min: {pval_array.min():.3e}")
            logger.info(f"    Max: {pval_array.max():.3e}")
            logger.info(f"    Median: {np.median(pval_array):.3e}")
            logger.info(f"    Mean: {np.mean(pval_array):.3e}")
            logger.info(f"    P < 0.001: {(pval_array < 0.001).sum()} ({(pval_array < 0.001).sum()/len(pval_array)*100:.1f}%)")
            logger.info(f"    P < 0.01: {(pval_array < 0.01).sum()} ({(pval_array < 0.01).sum()/len(pval_array)*100:.1f}%)")
            logger.info(f"    P < 0.05: {(pval_array < 0.05).sum()} ({(pval_array < 0.05).sum()/len(pval_array)*100:.1f}%)")
            logger.info(f"    P >= 0.05: {(pval_array >= 0.05).sum()} ({(pval_array >= 0.05).sum()/len(pval_array)*100:.1f}%)")
        else:
            logger.warning("    No p-values to compute (empty results)")
        
        return results
    
    def _apply_fdr_correction(self, results: List[Dict]) -> List[Dict]:
        """
        Apply Benjamini-Hochberg FDR correction.
        
        Reference: hypergeometric.r (p.adjust with "BH" method)
        
        Args:
            results: List of results with p-values
            
        Returns:
            List of results with FDR values
        """
        # Handle empty results
        if not results:
            logger.warning("No results to apply FDR correction to")
            return results
        
        from scipy.stats import false_discovery_control
        
        # Extract p-values
        pvalues = [r['pvalue'] for r in results]
        
        # Apply FDR correction (Benjamini-Hochberg)
        try:
            # scipy >= 1.11.0
            fdr_values = false_discovery_control(pvalues, method='bh')
        except AttributeError:
            # Fallback for older scipy versions
            from statsmodels.stats.multitest import multipletests
            _, fdr_values, _, _ = multipletests(pvalues, method='fdr_bh')
        
        # Add FDR and -log10 values
        for i, result in enumerate(results):
            result['fdr'] = fdr_values[i]
            
            # Calculate -log10(p-value) and -log10(FDR)
            # Replace infinite values with 1000
            import numpy as np
            if result['pvalue'] > 0:
                result['neg_log10_pvalue'] = min(-1 * np.log10(result['pvalue']), 1000)
            else:
                result['neg_log10_pvalue'] = 1000
            
            if result['fdr'] > 0:
                result['neg_log10_fdr'] = min(-1 * np.log10(result['fdr']), 1000)
            else:
                result['neg_log10_fdr'] = 1000
        
        return results
    
    def _write_results(self, cluster_file: str, results: List[Dict], output_file: str) -> int:
        """
        Write results with p-values and filter by FDR.
        
        Args:
            cluster_file: Filtered cluster file
            results: Statistical test results
            output_file: Output file
            
        Returns:
            Number of significant loops
        """
        # Read clusters
        clusters = pd.read_csv(cluster_file, sep='\t', header=None,
                              names=['chr1', 'start1', 'end1', 'ipets1_intra', 'ipets1_inter',
                                    'chr2', 'start2', 'end2', 'ipets2_intra', 'ipets2_inter',
                                    'ipets_between', 'same_chr', 'distance', 'score', 'pet_indexes'])
        
        # Combine with results and count FDR thresholds
        num_significant = 0
        num_fdr_005 = 0
        num_fdr_001 = 0
        
        with open(output_file, 'w') as f:
            for idx, (_, cluster) in enumerate(clusters.iterrows()):
                result = results[idx]
                
                # Count FDR thresholds
                if result['fdr'] < 0.05:
                    num_fdr_005 += 1
                if result['fdr'] < 0.01:
                    num_fdr_001 += 1
                
                # Only write if FDR < cutoff
                if result['fdr'] < self.pvalue_cutoff:
                    # Format: chr1 start1 end1 chr2 start2 end2 iPET_count type distance tagA tagB p-value FDR -log10(p) -log10(FDR)
                    interaction_type = 'intra' if cluster['same_chr'] == 1 else 'inter'
                    distance = int(cluster['distance']) if cluster['same_chr'] == 1 else -1
                    
                    line = (f"{cluster['chr1']}\t{int(cluster['start1'])}\t{int(cluster['end1'])}\t"
                           f"{cluster['chr2']}\t{int(cluster['start2'])}\t{int(cluster['end2'])}\t"
                           f"{int(cluster['ipets_between'])}\t{interaction_type}\t{distance}\t"
                           f"{result['tags_anchor1']}\t{result['tags_anchor2']}\t"
                           f"{result['pvalue']:.3e}\t{result['fdr']:.3e}\t"
                           f"{result['neg_log10_pvalue']:.2f}\t{result['neg_log10_fdr']:.2f}\n")
                    f.write(line)
                    num_significant += 1
        
        return num_significant, num_fdr_005, num_fdr_001


def main():
    """Command-line interface for pre-clustering."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Step 6.1: Pre-clustering for loop calling'
    )
    parser.add_argument('ipet_file', help='Input iPET file')
    parser.add_argument('output_prefix', help='Output prefix')
    parser.add_argument('--extension', type=int, default=500,
                       help='Extension length (default: 500bp)')
    parser.add_argument('--chrom-sizes', help='Chromosome sizes file (optional)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run pre-clustering
    pre_clusterer = PreClusterer(
        extension_length=args.extension,
        chrom_sizes_file=args.chrom_sizes
    )
    
    stats = pre_clusterer.pre_cluster(args.ipet_file, args.output_prefix)
    
    logger.info("Pre-clustering completed successfully!")


if __name__ == '__main__':
    main()
