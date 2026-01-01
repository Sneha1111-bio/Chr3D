"""
HiChIP-Specific Purifying Module

This module implements same-fragment PET removal for HiChIP data analysis.
It identifies PETs where both R1 and R2 anchors fall within the same restriction
fragment and removes them as self-ligation artifacts.

Reference: ChIA-PET Tool V3 - Purifying.java removePETinsameblock() (lines 106-172)
"""

import logging
from typing import Dict, Tuple, List
from pathlib import Path
from collections import defaultdict
import bisect

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RestrictionFragment:
    """Represents a restriction fragment (region between two restriction sites)."""
    
    def __init__(self, chrom: str, start: int, end: int, index: int):
        self.chrom = chrom
        self.start = start
        self.end = end
        self.index = index
    
    def contains(self, position: int) -> bool:
        """Check if position is within this fragment."""
        return self.start <= position < self.end
    
    def overlaps(self, start: int, end: int) -> bool:
        """Check if region [start, end) overlaps with this fragment."""
        return not (end <= self.start or start >= self.end)
    
    def __repr__(self):
        return f"Fragment({self.chrom}:{self.start}-{self.end}, idx={self.index})"


class HiChIPPurifier:
    """
    HiChIP-specific purifying with same-fragment PET removal.
    
    This class removes PETs where both R1 and R2 anchors fall within the same
    restriction fragment, as these are likely self-ligation artifacts.
    
    Reference: ChIA-PET Tool V3 Purifying.java
    """
    
    def __init__(self,
                 restriction_file: str,
                 min_fragment_skip: int = 1):
        """
        Initialize HiChIP purifier.
        
        Args:
            restriction_file: BED file with restriction site positions
            min_fragment_skip: Minimum number of fragments between reads (default: 1).
                              A value of 1 means reads must be in different fragments.
                              A value of 2 means at least one fragment between reads.
        """
        self.restriction_file = restriction_file
        self.min_insert_size = min_fragment_skip  # Keep internal name for compatibility
        self.fragments = {}  # {chrom: [RestrictionFragment]}
        
        logger.info("=" * 70)
        logger.info("HiChIP PURIFIER INITIALIZATION")
        logger.info("=" * 70)
        logger.info(f"Restriction file: {restriction_file}")
        logger.info(f"Min fragment skip: {min_fragment_skip}")
        
        # Load restriction fragments
        self._load_restriction_fragments()
    
    def _load_restriction_fragments(self):
        """
    Load restriction fragments from restriction site file.
    
    For 0-based BED coordinates: MboI (^GATC) cut position = start.
    The cut occurs after G, which is represented as the 'start' position
    in 0-based coordinate systems.
    
    Fragments are created between consecutive cut positions.
    """
        logger.info("\nLoading restriction sites...")
        
        # Read restriction sites and calculate cut positions
        sites_by_chrom = defaultdict(list)
        
        with open(self.restriction_file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 3:
                    continue
                
                chrom = parts[0]
                start = int(parts[1])
                end = int(parts[2])
                
                # For MboI (^GATC), cut is after first base (G)
                # Site is at positions [start, end), so cut is at start + 1
                # This creates fragments between actual cut positions
                cut_pos = start  # PERSONAL IMPLEMENTATION UPDATE
                sites_by_chrom[chrom].append(cut_pos)
        
        logger.info(f"Loaded sites from {len(sites_by_chrom)} chromosomes")
        
        # Convert cut positions to fragments
        logger.info("\nGenerating restriction fragments...")
        
        total_fragments = 0
        for chrom, cut_positions in sites_by_chrom.items():
            # Sort and deduplicate cut positions
            cut_positions = sorted(set(cut_positions))
            
            # Create fragments between consecutive cut positions
            fragments = []
            
            # Add chromosome start (position 0)
            all_positions = [0] + cut_positions
            
            # Create fragments between consecutive positions
            for i in range(len(all_positions) - 1):
                frag_start = all_positions[i]
                frag_end = all_positions[i + 1]
                frag = RestrictionFragment(chrom, frag_start, frag_end, i)
                fragments.append(frag)
            
            # Last fragment: last cut to end of chromosome
            fragments.append(RestrictionFragment(chrom, all_positions[-1], 10**9, len(all_positions) - 1))
            
            self.fragments[chrom] = fragments
            total_fragments += len(fragments)
        
        logger.info(f"Generated {total_fragments:,} restriction fragments")
        logger.info(f"Chromosomes: {len(self.fragments)}")
        
        # Show sample
        if 'chr1' in self.fragments:
            logger.info(f"\nSample fragments (chr1, first 5):")
            for frag in self.fragments['chr1'][:5]:
                logger.info(f"  {frag}")
    
    def _find_fragment_for_position(self, chrom: str, position: int) -> RestrictionFragment:
        """
        Find which restriction fragment contains a specific position.
        
        CORRECTED: Uses position (read center) instead of region overlap.
        Uses binary search for O(log n) efficiency.
        
        Args:
            chrom: Chromosome name
            position: Genomic position (typically read center)
        
        Returns:
            RestrictionFragment object, or None if not found
        
        Reference: Purifying.java getResSite() (lines 42-104)
        """
        if chrom not in self.fragments:
            return None
        
        fragments = self.fragments[chrom]
        
        # Binary search for fragment containing this position
        left, right = 0, len(fragments) - 1
        
        while left <= right:
            mid = (left + right) // 2
            frag = fragments[mid]
            
            if frag.contains(position):
                return frag
            elif position < frag.start:
                right = mid - 1
            else:
                left = mid + 1
        
        # If not found, return None
        return None
    
    def remove_same_fragment_pets(self,
                                  bedpe_file: str,
                                  output_file: str,
                                  sameres_file: str) -> Dict:
        """
        Remove PETs where both ends are in the same restriction fragment.
        
        Args:
            bedpe_file: Input BEDPE file
            output_file: Output file for valid PETs (different fragments)
            sameres_file: Output file for removed PETs (same fragment)
        
        Returns:
            Statistics dictionary
        
        Reference: Purifying.java removePETinsameblock() (lines 106-172)
        """
        logger.info("=" * 70)
        logger.info("SAME-FRAGMENT PET REMOVAL")
        logger.info("=" * 70)
        logger.info(f"Input BEDPE: {bedpe_file}")
        logger.info(f"Output (valid): {output_file}")
        logger.info(f"Output (removed): {sameres_file}")
        
        stats = {
            'total_pets': 0,
            'same_fragment': 0,
            'different_fragment': 0,
            'invalid': 0,
            'filtered_by_insert_size': 0
        }
        
        with open(bedpe_file, 'r') as in_f, \
             open(output_file, 'w') as out_f, \
             open(sameres_file, 'w') as sameres_f:
            
            for line in in_f:
                line = line.strip()
                if not line:
                    continue
                
                stats['total_pets'] += 1
                
                # Parse BEDPE line
                # Format: chr1 start1 end1 chr2 start2 end2 name score strand1 strand2
                fields = line.split('\t')
                if len(fields) < 10:
                    stats['invalid'] += 1
                    continue
                
                chr1 = fields[0]
                start1 = int(fields[1])
                end1 = int(fields[2])
                chr2 = fields[3]
                start2 = int(fields[4])
                end2 = int(fields[5])
                strand1 = fields[8] if len(fields) > 8 else '+'
                strand2 = fields[9] if len(fields) > 9 else '+'
                
                # CORRECTED: Use read centers for fragment assignment
                r1_center = (start1 + end1) // 2
                r2_center = (start2 + end2) // 2
                
                # Find restriction fragments for R1 and R2 centers
                frag1 = self._find_fragment_for_position(chr1, r1_center)
                frag2 = self._find_fragment_for_position(chr2, r2_center)
                
                # Check if both fragments were found
                if not frag1 or not frag2:
                    stats['invalid'] += 1
                    continue
                
                # Check if same fragment using fragment index (more robust than object identity)
                # Same fragment means same chromosome AND same fragment index
                if chr1 == chr2 and frag1.index == frag2.index:
                    # Same fragment - REMOVE
                    stats['same_fragment'] += 1
                    sameres_f.write(f"{line}\t{frag1.index}\t{frag2.index}\tN\n")
                else:
                    # Different fragments - check fragment skip distance
                    # Fragment skip = number of fragments between the two reads
                    # For same chromosome, this is |frag2.index - frag1.index|
                    # For different chromosomes, skip distance is undefined (set to -1)
                    if chr1 == chr2:
                        fragment_skip = abs(frag2.index - frag1.index)
                    else:
                        fragment_skip = -1  # Trans interaction, no skip distance
                    
                    # Filter by minimum fragment skip (only for cis interactions)
                    # min_insert_size here means minimum fragment skip distance
                    if chr1 == chr2 and fragment_skip < self.min_insert_size:
                        stats['filtered_by_insert_size'] += 1
                        continue
                    
                    # KEEP - different fragments with sufficient skip distance
                    stats['different_fragment'] += 1
                    out_f.write(f"{line}\t{frag1.index}\t{frag2.index}\t{fragment_skip}\n")
                
                # Progress report
                if stats['total_pets'] % 100000 == 0:
                    logger.info(f"Processed {stats['total_pets']:,} PETs...")
        
        # Print summary
        logger.info("=" * 70)
        logger.info("SAME-FRAGMENT REMOVAL COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total PETs: {stats['total_pets']:,}")
        logger.info(f"Same fragment (removed): {stats['same_fragment']:,} ({100*stats['same_fragment']/stats['total_pets']:.1f}%)")
        logger.info(f"Different fragment (kept): {stats['different_fragment']:,} ({100*stats['different_fragment']/stats['total_pets']:.1f}%)")
        logger.info(f"Invalid: {stats['invalid']:,}")
        logger.info(f"Filtered by insert size: {stats['filtered_by_insert_size']:,}")
        logger.info(f"\nOutput files:")
        logger.info(f"  Valid PETs: {output_file}")
        logger.info(f"  Removed PETs: {sameres_file}")
        logger.info("=" * 70)
        
        return stats


def main():
    """
    Example usage of HiChIPPurifier.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Remove same-fragment PETs for HiChIP analysis'
    )
    parser.add_argument('--bedpe', required=True, help='Input BEDPE file')
    parser.add_argument('--restriction', required=True, help='Restriction site BED file')
    parser.add_argument('--output', required=True, help='Output BEDPE file (valid PETs)')
    parser.add_argument('--sameres', required=True, help='Output file for removed PETs')
    parser.add_argument('--min-insert-size', type=int, default=1, help='Minimum insert size (default: 1)')
    
    args = parser.parse_args()
    
    # Create purifier
    purifier = HiChIPPurifier(
        restriction_file=args.restriction,
        min_insert_size=args.min_insert_size
    )
    
    # Remove same-fragment PETs
    stats = purifier.remove_same_fragment_pets(
        bedpe_file=args.bedpe,
        output_file=args.output,
        sameres_file=args.sameres
    )
    
    print(f"\nRemoved {stats['same_fragment']:,} same-fragment PETs")
    print(f"Kept {stats['different_fragment']:,} valid PETs")


if __name__ == '__main__':
    main()
