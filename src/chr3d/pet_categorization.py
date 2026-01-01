#!/usr/bin/env python3
"""
ChIA-PET Step 4: PET Categorization

This module implements PET categorization logic from the reference Java code
(DividePets.java and PetClassification.java).

Splits chromatin interactions into 3 categories:
- iPET (Inter-ligation) → Used for loop calling
- sPET (Self-ligation) → Used for peak calling
- oPET (Other) → Discarded
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PETCategorizer:
    """
    PET categorization based on distance and strand orientation.
    
    Supports both ChIA-PET and HiChIP modes with appropriate cutoffs.
    
    Reference: PetClassification.java (lines 113-140)
    """
    
    def __init__(self, self_ligation_cutoff: int = None, mode: str = 'chiapet'):
        """
        Initialize PET categorizer.
        
        Args:
            self_ligation_cutoff: Distance cutoff for self-ligation (bp)
                                 If None, uses mode-specific default
            mode: Analysis mode - 'chiapet' or 'hichip'
                 'chiapet': 8000bp cutoff (default)
                 'hichip': 1000bp cutoff
        
        Reference: Path.java (lines 234-238)
        """
        # Set cutoff based on mode if not explicitly provided
        if self_ligation_cutoff is None:
            if mode.lower() == 'hichip':
                self.self_ligation_cutoff = 1000
                logger.info("HiChIP mode: Using 1000bp self-ligation cutoff")
            else:  # chiapet mode (default)
                self.self_ligation_cutoff = 8000
                logger.info("ChIA-PET mode: Using 8000bp self-ligation cutoff")
        else:
            self.self_ligation_cutoff = self_ligation_cutoff
            logger.info(f"Custom cutoff: {self_ligation_cutoff}bp")
        
        self.mode = mode.lower()
        logger.info(f"PET Categorizer initialized: mode={self.mode}, cutoff={self.self_ligation_cutoff}bp")
    
    @staticmethod
    def calculate_distance(row: pd.Series) -> float:
        """
        Calculate distance between two anchors.
        
        CORRECTED: Distance is calculated for ALL same-chromosome PETs,
        regardless of strand orientation.
        
        Reference: HIT2.calculateDistance() in Java code
        Note: The Java code only calculates distance for same strand,
        but we need distance for ALL cis PETs to properly classify sPETs.
        
        Args:
            row: DataFrame row with chr1, chr2, start1, start2
            
        Returns:
            Distance in bp, or float('inf') for trans-chromosomal
        """
        if row['chr1'] == row['chr2']:
            # Calculate distance for ALL same-chromosome PETs
            return abs(row['start2'] - row['start1'])
        else:
            # Different chromosomes
            return float('inf')
    
    @staticmethod
    def is_self_ligation_pattern(strand1: str, pos1: int, 
                                 strand2: str, pos2: int) -> bool:
        """
        Check if the PET has self-ligation pattern (convergent strands).
        
        Self-ligation pattern (reads pointing inward):
        - Forward strand first (+): pos1 > pos2  (<-- -->)
        - Reverse strand first (-): pos1 < pos2  (--> <--)
        
        Reference: PetClassification.classify() in Java code (lines 113-140)
        
        Args:
            strand1: Strand of first anchor ('+' or '-')
            pos1: Position of first anchor
            strand2: Strand of second anchor ('+' or '-')
            pos2: Position of second anchor
            
        Returns:
            True if self-ligation pattern, False otherwise
        """
        if strand1 == strand2:
            return False  # Same strand cannot be self-ligation
        
        if strand1 == '+':
            # Forward strand first: self-ligation when pos1 > pos2
            return pos1 > pos2
        else:  # strand1 == '-'
            # Reverse strand first: self-ligation when pos1 < pos2
            return pos1 < pos2
    
    def classify_pet(self, row: pd.Series) -> Tuple[str, str]:
        """
        Classify a PET into iPET, sPET, or oPET.
        
        Reference: PetClassification.classify() method (lines 113-140)
        
        Classification rules:
        1. Different chromosomes → iPET (trans)
        2. Same chr, distance > cutoff → iPET (cis long-range)
        3. Same chr, distance ≤ cutoff:
           - Same strand → oPET
           - Different strands:
             * Self-ligation pattern → sPET
             * Wrong orientation → oPET
        
        Args:
            row: DataFrame row with chr1, chr2, strand1, strand2, start1, start2, distance
            
        Returns:
            Tuple of (pet_type, subtype)
        """
        chr1, chr2 = row['chr1'], row['chr2']
        strand1, strand2 = row['strand1'], row['strand2']
        pos1, pos2 = row['start1'], row['start2']
        distance = row['distance']
        
        # Rule 1: Different chromosomes → iPET (trans-chromosomal)
        if chr1 != chr2:
            return 'iPET', 'trans'
        
        # Rule 2: Same chromosome, long distance → iPET (cis long-range)
        if distance > self.self_ligation_cutoff:
            return 'iPET', 'cis_long'
        
        # Rule 3: Same chromosome, short distance
        # Check strand orientation
        if strand1 == strand2:
            # Same strand → oPET
            return 'oPET', 'same_strand'
        else:
            # Different strands: check self-ligation pattern
            if self.is_self_ligation_pattern(strand1, pos1, strand2, pos2):
                return 'sPET', 'self_ligation'
            else:
                return 'oPET', 'wrong_orientation'
    
    def categorize_bedpe(self, input_bedpe: str, output_prefix: str) -> Dict:
        """
        Categorize PETs from BEDPE file and write to separate files.
        
        Args:
            input_bedpe: Input BEDPE file path
            output_prefix: Prefix for output files (e.g., "final_merged_1kb")
            
        Returns:
            Dictionary with categorization statistics
        """
        logger.info(f"Loading BEDPE file: {input_bedpe}")
        
        # Read BEDPE file (with optional weight column)
        column_names = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2',
                       'name', 'score', 'strand1', 'strand2', 'weight']
        
        df = pd.read_csv(input_bedpe, sep='\t', comment='#', names=column_names)
        
        logger.info(f"Loaded {len(df):,} chromatin interactions")
        
        # Calculate distances
        logger.info("Calculating distances...")
        df['distance'] = df.apply(self.calculate_distance, axis=1)
        
        # Classify PETs
        logger.info("Classifying PETs...")
        df[['pet_type', 'subtype']] = df.apply(
            self.classify_pet, axis=1, result_type='expand'
        )
        
        # Generate statistics
        stats = self._generate_statistics(df)
        
        # Write output files
        self._write_output_files(df, output_prefix)
        
        # Log summary
        self._log_summary(stats)
        
        return stats
    
    def _generate_statistics(self, df: pd.DataFrame) -> Dict:
        """Generate categorization statistics."""
        total = len(df)
        
        # Count by type
        ipet_count = (df['pet_type'] == 'iPET').sum()
        spet_count = (df['pet_type'] == 'sPET').sum()
        opet_count = (df['pet_type'] == 'oPET').sum()
        
        # Count by subtype
        subtype_counts = df['subtype'].value_counts().to_dict()
        
        # Cis/trans ratios
        cis_count = (df['chr1'] == df['chr2']).sum()
        trans_count = total - cis_count
        
        # Distance statistics for cis PETs
        cis_df = df[df['distance'] != float('inf')]
        
        stats = {
            'total': total,
            'ipet': {
                'count': ipet_count,
                'percentage': ipet_count / total * 100
            },
            'spet': {
                'count': spet_count,
                'percentage': spet_count / total * 100
            },
            'opet': {
                'count': opet_count,
                'percentage': opet_count / total * 100
            },
            'subtypes': subtype_counts,
            'cis': {
                'count': cis_count,
                'percentage': cis_count / total * 100
            },
            'trans': {
                'count': trans_count,
                'percentage': trans_count / total * 100
            },
            'distance_stats': {
                'min': cis_df['distance'].min() if len(cis_df) > 0 else 0,
                'median': cis_df['distance'].median() if len(cis_df) > 0 else 0,
                'max': cis_df['distance'].max() if len(cis_df) > 0 else 0
            }
        }
        
        return stats
    
    def _write_output_files(self, df: pd.DataFrame, output_prefix: str):
        """Write categorized PETs to separate files."""
        output_dir = Path(output_prefix).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # For ChIA-PET, each row represents a unique read pair, so weight should be 1
        # If weight column doesn't exist or is not 1, set it to 1
        if 'weight' not in df.columns or df['weight'].isna().any():
            df = df.copy()
            df['weight'] = 1
        
        # Output columns (BEDPE format with weight for loop calling)
        output_cols = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2',
                      'name', 'score', 'strand1', 'strand2', 'weight']
        
        # Write iPET file
        ipet_file = f"{output_prefix}.ipet"
        ipet_df = df[df['pet_type'] == 'iPET']
        ipet_df[output_cols].to_csv(ipet_file, sep='\t', index=False, header=False)
        logger.info(f"Wrote {len(ipet_df):,} iPETs to: {ipet_file}")
        
        # Write sPET file
        spet_file = f"{output_prefix}.spet"
        spet_df = df[df['pet_type'] == 'sPET']
        spet_df[output_cols].to_csv(spet_file, sep='\t', index=False, header=False)
        logger.info(f"Wrote {len(spet_df):,} sPETs to: {spet_file}")
        
        # Write oPET file
        opet_file = f"{output_prefix}.opet"
        opet_df = df[df['pet_type'] == 'oPET']
        opet_df[output_cols].to_csv(opet_file, sep='\t', index=False, header=False)
        logger.info(f"Wrote {len(opet_df):,} oPETs to: {opet_file}")
    
    def _log_summary(self, stats: Dict):
        """Log categorization summary."""
        logger.info("=" * 70)
        logger.info("PET CATEGORIZATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total PETs: {stats['total']:,}")
        logger.info(f"Self-ligation cutoff: {self.self_ligation_cutoff}bp")
        logger.info("")
        logger.info(f"iPET: {stats['ipet']['count']:,} ({stats['ipet']['percentage']:.1f}%)")
        logger.info(f"sPET: {stats['spet']['count']:,} ({stats['spet']['percentage']:.1f}%)")
        logger.info(f"oPET: {stats['opet']['count']:,} ({stats['opet']['percentage']:.1f}%)")
        logger.info("")
        logger.info(f"Cis: {stats['cis']['count']:,} ({stats['cis']['percentage']:.1f}%)")
        logger.info(f"Trans: {stats['trans']['count']:,} ({stats['trans']['percentage']:.1f}%)")
        logger.info("=" * 70)
        
        # Quality assessment
        ipet_pct = stats['ipet']['percentage']
        spet_pct = stats['spet']['percentage']
        opet_pct = stats['opet']['percentage']
        
        if 67 <= ipet_pct <= 74 and 20 <= spet_pct <= 27 and 7 <= opet_pct <= 13:
            logger.info("✓ EXCELLENT: Distribution matches expected ranges!")
        elif 60 <= ipet_pct <= 80 and 15 <= spet_pct <= 30:
            logger.info("✓ GOOD: Distribution is within acceptable ranges")
        else:
            logger.warning("⚠️  WARNING: Distribution differs from expected ranges")
            logger.warning("   Expected: iPET=67-74%, sPET=20-27%, oPET=7-13%")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ChIA-PET PET Categorization (Step 4)'
    )
    parser.add_argument(
        'input_bedpe',
        help='Input BEDPE file'
    )
    parser.add_argument(
        'output_prefix',
        help='Output prefix for categorized files'
    )
    parser.add_argument(
        '--cutoff',
        type=int,
        default=8000,
        help='Self-ligation cutoff in bp (default: 8000)'
    )
    
    args = parser.parse_args()
    
    # Run categorization
    categorizer = PETCategorizer(self_ligation_cutoff=args.cutoff)
    stats = categorizer.categorize_bedpe(args.input_bedpe, args.output_prefix)
    
    return stats


if __name__ == '__main__':
    main()
