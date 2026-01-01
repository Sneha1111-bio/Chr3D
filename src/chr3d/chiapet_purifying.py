"""
ChIA-PET Purifying Module

This module implements PET purifying for ChIA-PET data analysis, including:
- Deduplication
- PET merging (MERGE_DISTANCE = 2bp)
- Quality filtering
- Chimeric read filtering

Reference: ChIA-PET Tool V3 - Purifying.java and MergeSimilarPETs2.java
"""

import logging
from typing import Dict, List, Tuple
from pathlib import Path
from collections import defaultdict
import heapq

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PET:
    """Represents a Paired-End Tag."""
    
    VALID_STRANDS = {'+', '-', '.'}
    
    def __init__(self, chr1: str, start1: int, end1: int, strand1: str,
                 chr2: str, start2: int, end2: int, strand2: str,
                 name: str = ".", score: int = 0, weight: float = 1.0,
                 validate: bool = False):
        """
        Initialize a PET.
        
        Args:
            validate: If True, perform input validation (slower but safer)
        """
        if validate:
            self._validate_inputs(chr1, start1, end1, strand1, chr2, start2, end2, strand2, weight)
        
        self.chr1 = chr1
        self.start1 = start1
        self.end1 = end1
        self.strand1 = strand1
        self.chr2 = chr2
        self.start2 = start2
        self.end2 = end2
        self.strand2 = strand2
        self.name = name
        self.score = score
        self.weight = weight
    
    def _validate_inputs(self, chr1, start1, end1, strand1, chr2, start2, end2, strand2, weight):
        """Validate PET inputs."""
        # Check coordinates are non-negative
        if start1 < 0 or end1 < 0 or start2 < 0 or end2 < 0:
            raise ValueError(f"Coordinates must be non-negative: {start1}, {end1}, {start2}, {end2}")
        
        # Check start <= end
        if start1 > end1:
            raise ValueError(f"start1 ({start1}) > end1 ({end1})")
        if start2 > end2:
            raise ValueError(f"start2 ({start2}) > end2 ({end2})")
        
        # Check valid strands
        if strand1 not in self.VALID_STRANDS:
            raise ValueError(f"Invalid strand1: {strand1}")
        if strand2 not in self.VALID_STRANDS:
            raise ValueError(f"Invalid strand2: {strand2}")
        
        # Check weight is positive
        if weight <= 0:
            raise ValueError(f"Weight must be positive: {weight}")
    
    def __lt__(self, other):
        """Sort by chr1, start1, chr2, start2."""
        if self.chr1 != other.chr1:
            return self.chr1 < other.chr1
        if self.start1 != other.start1:
            return self.start1 < other.start1
        if self.chr2 != other.chr2:
            return self.chr2 < other.chr2
        return self.start2 < other.start2
    
    def to_bedpe(self) -> str:
        """Convert to BEDPE format."""
        return f"{self.chr1}\t{self.start1}\t{self.end1}\t{self.chr2}\t{self.start2}\t{self.end2}\t{self.name}\t{self.score}\t{self.strand1}\t{self.strand2}\t{self.weight:.1f}"
    
    # def canonical_key(self) -> tuple:
    #     """
    #     Return a canonical key for this PET that treats chr1↔chr2 swaps as equivalent.
        
    #     This ensures that the same interaction is identified regardless of which
    #     anchor is labeled as R1 vs R2.
    #     """
    #     # Create tuples for each anchor
    #     anchor1 = (self.chr1, self.start1, self.end1, self.strand1)
    #     anchor2 = (self.chr2, self.start2, self.end2, self.strand2)
        
    #     # Return in canonical order (smaller first)
    #     if anchor1 <= anchor2:
    #         return (anchor1, anchor2)
    #     else:
    #         return (anchor2, anchor1)

    def canonical_key(self) -> tuple:
        """
        Return key for exact duplicate detection.
        
        CRITICAL: Do NOT canonicalize intra-chromosomal PETs.
        Different R1/R2 orientations may represent different interactions.
        """
        anchor1 = (self.chr1, self.start1, self.end1, self.strand1)
        anchor2 = (self.chr2, self.start2, self.end2, self.strand2)
        
        # Only canonicalize for inter-chromosomal (trans) interactions
        if self.chr1 != self.chr2:
            if anchor1 <= anchor2:
                return (anchor1, anchor2)
            else:
                return (anchor2, anchor1)
        else:
            # For intra-chromosomal (cis): keep original orientation
            return (anchor1, anchor2)

    
    @staticmethod
    def from_bedpe(line: str) -> 'PET':
        """Parse from BEDPE format."""
        fields = line.strip().split('\t')
        weight = float(fields[10]) if len(fields) > 10 else 1.0
        return PET(
            chr1=fields[0],
            start1=int(fields[1]),
            end1=int(fields[2]),
            strand1=fields[8] if len(fields) > 8 else '+',
            chr2=fields[3],
            start2=int(fields[4]),
            end2=int(fields[5]),
            strand2=fields[9] if len(fields) > 9 else '+',
            name=fields[6] if len(fields) > 6 else '.',
            score=int(fields[7]) if len(fields) > 7 else 0,
            weight=weight
        )
    
    def distance_to(self, other: 'PET') -> Tuple[int, int]:
        """
        Calculate distance to another PET.
        
        Returns:
            Tuple of (distance_r1, distance_r2)
        """
        # Distance for R1 (use midpoint)
        mid1_self = (self.start1 + self.end1) // 2
        mid1_other = (other.start1 + other.end1) // 2
        dist1 = abs(mid1_self - mid1_other)
        
        # Distance for R2 (use midpoint)
        mid2_self = (self.start2 + self.end2) // 2
        mid2_other = (other.start2 + other.end2) // 2
        dist2 = abs(mid2_self - mid2_other)
        
        return (dist1, dist2)
    
    def is_similar_to(self, other: 'PET', merge_distance: int) -> bool:
        """
        Check if two PETs are similar enough to merge.
        
        Args:
            other: Another PET
            merge_distance: Maximum distance for merging
        
        Returns:
            True if PETs should be merged
        
        Reference: PET.java mergeSimilarPets() (lines 268-297)
        """
        # Must have same chromosome pair and strands
        if (self.chr1 != other.chr1 or self.chr2 != other.chr2 or
            self.strand1 != other.strand1 or self.strand2 != other.strand2):
            return False
        
        # Check distance
        dist1, dist2 = self.distance_to(other)
        return dist1 <= merge_distance and dist2 <= merge_distance


class ChIAPETPurifier:
    """
    ChIA-PET purifying with deduplication and PET merging.
    
    Reference: ChIA-PET Tool V3 Purifying.java and MergeSimilarPETs2.java
    """
    
    def __init__(self, merge_distance: int = 2):
        """
        Initialize ChIA-PET purifier.
        
        Args:
            merge_distance: Maximum distance for merging similar PETs (default: 2bp)
        """
        self.merge_distance = merge_distance
        
        logger.info("=" * 70)
        logger.info("ChIA-PET PURIFIER INITIALIZATION")
        logger.info("=" * 70)
        logger.info(f"Merge distance: {merge_distance}bp")
    
    def deduplicate(self, bedpe_file: str, output_file: str) -> Dict:
        """
        Remove exact duplicate PETs.
        
        Args:
            bedpe_file: Input BEDPE file
            output_file: Output BEDPE file (deduplicated)
        
        Returns:
            Statistics dictionary
        """
        logger.info("=" * 70)
        logger.info("DEDUPLICATION")
        logger.info("=" * 70)
        logger.info(f"Input: {bedpe_file}")
        logger.info(f"Output: {output_file}")
        
        stats = {
            'total_pets': 0,
            'unique_pets': 0,
            'duplicates': 0
        }
        
        seen = set()
        
        with open(bedpe_file, 'r') as in_f, open(output_file, 'w') as out_f:
            for line in in_f:
                line = line.strip()
                if not line:
                    continue
                
                stats['total_pets'] += 1
                
                # Parse PET
                fields = line.split('\t')
                if len(fields) < 10:
                    continue
                
                # Create canonical key that treats chr1↔chr2 swaps as equivalent
                pet = PET.from_bedpe(line)
                key = pet.canonical_key()
                
                if key not in seen:
                    seen.add(key)
                    stats['unique_pets'] += 1
                    out_f.write(line + '\n')
                else:
                    stats['duplicates'] += 1
                
                if stats['total_pets'] % 100000 == 0:
                    logger.info(f"Processed {stats['total_pets']:,} PETs...")
        
        logger.info("=" * 70)
        logger.info("DEDUPLICATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total PETs: {stats['total_pets']:,}")
        logger.info(f"Unique PETs: {stats['unique_pets']:,}")
        if stats['total_pets'] > 0:
            logger.info(f"Duplicates removed: {stats['duplicates']:,} ({100*stats['duplicates']/stats['total_pets']:.1f}%)")
        else:
            logger.info(f"Duplicates removed: 0")
        logger.info("=" * 70)
        
        return stats
    
    def merge_similar_pets(self, bedpe_file: str, output_file: str) -> Dict:
        """
        Merge similar PETs within merge_distance.
        
        Two PETs are merged if:
        - Same chromosome pair
        - Same strand orientation
        - R1 positions within merge_distance
        - R2 positions within merge_distance
        
        Args:
            bedpe_file: Input BEDPE file (should be deduplicated)
            output_file: Output BEDPE file (merged)
        
        Returns:
            Statistics dictionary
        
        Reference: MergeSimilarPETs2.java and PET.java mergeSimilarPets() (lines 268-297)
        """
        logger.info("=" * 70)
        logger.info("PET MERGING")
        logger.info("=" * 70)
        logger.info(f"Input: {bedpe_file}")
        logger.info(f"Output: {output_file}")
        logger.info(f"Merge distance: {self.merge_distance}bp")
        
        stats = {
            'total_pets': 0,
            'merged_pets': 0,
            'groups_merged': 0
        }
        
        # Group PETs by chromosome pair and strand
        groups = defaultdict(list)
        
        logger.info("\nLoading and grouping PETs...")
        with open(bedpe_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                stats['total_pets'] += 1
                pet = PET.from_bedpe(line)
                
                # Group key: (chr1, chr2, strand1, strand2)
                key = (pet.chr1, pet.chr2, pet.strand1, pet.strand2)
                groups[key].append(pet)
                
                if stats['total_pets'] % 100000 == 0:
                    logger.info(f"Loaded {stats['total_pets']:,} PETs...")
        
        logger.info(f"Loaded {stats['total_pets']:,} PETs into {len(groups)} groups")
        
        # Merge PETs within each group
        logger.info("\nMerging similar PETs...")
        
        with open(output_file, 'w') as out_f:
            for group_idx, (key, pets) in enumerate(groups.items()):
                if (group_idx + 1) % 1000 == 0:
                    logger.info(f"Processing group {group_idx + 1}/{len(groups)}...")
                
                # Sort PETs by position
                pets.sort()
                
                # Merge similar PETs
                merged = self._merge_pet_list(pets)
                
                # Write merged PETs
                for pet in merged:
                    out_f.write(pet.to_bedpe() + '\n')
                
                stats['merged_pets'] += len(merged)
                if len(merged) < len(pets):
                    stats['groups_merged'] += 1
        
        logger.info("=" * 70)
        logger.info("PET MERGING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Input PETs: {stats['total_pets']:,}")
        logger.info(f"Output PETs: {stats['merged_pets']:,}")
        if stats['total_pets'] > 0:
            logger.info(f"PETs merged: {stats['total_pets'] - stats['merged_pets']:,} ({100*(stats['total_pets'] - stats['merged_pets'])/stats['total_pets']:.1f}%)")
        else:
            logger.info(f"PETs merged: 0")
        logger.info(f"Groups with merging: {stats['groups_merged']:,}")
        logger.info("=" * 70)
        
        return stats
    
    def _merge_pet_list(self, pets: List[PET]) -> List[PET]:
        """
        Merge a list of PETs that are similar (within merge_distance).
        
        Algorithm:
        1. Track which PETs have been used in a merge group
        2. For each unused PET, find all similar unused PETs
        3. Merge them by summing weights
        
        Reference: PET.java mergeSimilarPets() (lines 268-297)
        """
        if len(pets) <= 1:
            return pets
        
        n = len(pets)
        used = [False] * n  # Track which PETs have been merged
        merged = []
        
        for i in range(n):
            if used[i]:
                continue
            
            # Start a new merge group with PET i
            group_weight = pets[i].weight
            group_indices = [i]
            used[i] = True
            
            # Find all similar PETs to merge with this group
            for j in range(i + 1, n):
                if used[j]:
                    continue
                
                # Check distance from group anchor (first PET) to candidate
                dist1, dist2 = pets[i].distance_to(pets[j])
                
                # If R1 is too far, no more candidates can match (sorted by R1)
                if dist1 > self.merge_distance:
                    break
                
                # Both R1 and R2 must be within merge_distance
                if dist2 <= self.merge_distance:
                    group_weight += pets[j].weight
                    group_indices.append(j)
                    used[j] = True
                # If R2 is far, this PET stays unused for potential other groups
            
            # Use the last PET in the group as representative
            # representative = pets[group_indices[-1]]
            representative = pets[group_indices[0]] # PERSONAL EXPERIMENTAL UPDATED 

            representative.weight = group_weight
            merged.append(representative)
        
        return merged
    
    def purify(self, bedpe_file: str, output_prefix: str) -> Dict:
        """
        Complete purifying workflow: deduplicate + merge.
        
        Args:
            bedpe_file: Input BEDPE file
            output_prefix: Output file prefix
        
        Returns:
            Combined statistics dictionary
        """
        logger.info("=" * 70)
        logger.info("COMPLETE ChIA-PET PURIFYING")
        logger.info("=" * 70)
        logger.info(f"Input: {bedpe_file}")
        logger.info(f"Output prefix: {output_prefix}")
        
        # Step 1: Deduplicate
        dedup_file = f"{output_prefix}.deduplicated.bedpe"
        dedup_stats = self.deduplicate(bedpe_file, dedup_file)
        
        # Step 2: Merge similar PETs
        merged_file = f"{output_prefix}.merged.bedpe"
        merge_stats = self.merge_similar_pets(dedup_file, merged_file)
        
        # Combined statistics
        stats = {
            'input_pets': dedup_stats['total_pets'],
            'after_dedup': dedup_stats['unique_pets'],
            'after_merge': merge_stats['merged_pets'],
            'duplicates_removed': dedup_stats['duplicates'],
            'pets_merged': dedup_stats['unique_pets'] - merge_stats['merged_pets']
        }
        
        logger.info("=" * 70)
        logger.info("PURIFYING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Input PETs: {stats['input_pets']:,}")
        if stats['input_pets'] > 0:
            logger.info(f"After deduplication: {stats['after_dedup']:,} ({100*stats['after_dedup']/stats['input_pets']:.1f}%)")
            logger.info(f"After merging: {stats['after_merge']:,} ({100*stats['after_merge']/stats['input_pets']:.1f}%)")
        else:
            logger.warning("No input PETs to process - check linker filtering step")
            logger.info(f"After deduplication: {stats['after_dedup']:,}")
            logger.info(f"After merging: {stats['after_merge']:,}")
        logger.info(f"\nRemoved:")
        logger.info(f"  Duplicates: {stats['duplicates_removed']:,}")
        logger.info(f"  Merged: {stats['pets_merged']:,}")
        logger.info(f"  Total removed: {stats['input_pets'] - stats['after_merge']:,}")
        logger.info(f"\nFinal output: {merged_file}")
        logger.info("=" * 70)
        
        return stats


def main():
    """Example usage of ChIAPETPurifier."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Purify ChIA-PET data: deduplicate and merge similar PETs'
    )
    parser.add_argument('--bedpe', required=True, help='Input BEDPE file')
    parser.add_argument('--output', required=True, help='Output prefix')
    parser.add_argument('--merge-distance', type=int, default=2, help='Merge distance (default: 2bp)')
    
    args = parser.parse_args()
    
    # Create purifier
    purifier = ChIAPETPurifier(merge_distance=args.merge_distance)
    
    # Run purifying
    stats = purifier.purify(args.bedpe, args.output)
    
    print(f"\nPurifying complete!")
    print(f"Input: {stats['input_pets']:,} PETs")
    print(f"Output: {stats['after_merge']:,} PETs")


if __name__ == '__main__':
    main()
