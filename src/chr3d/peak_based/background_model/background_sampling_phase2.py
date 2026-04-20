#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   BACKGROUND SAMPLING - PHASE 2: PMF P-Value Calculation                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PURPOSE:                                                                    ║
║  - Load templates_with_nb.csv from Phase 1                                  ║
║  - Calculate p-values using PMF: P(X >= K | NB(r, p))                       ║
║  - For valid NB: Use scipy.stats.nbinom.sf(K-1, r, p)                       ║
║  - For degenerate with PETs > 0: Use p-value = 1/n_samples                  ║
║  - For degenerate with PETs = 0: Use p-value = 1.0                          ║
║  - Add p_value and significance columns                                     ║
║  - Update templates_with_nb.csv with final results                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import polars as pl
import pandas as pd
import numpy as np
from scipy import stats
import argparse
from pathlib import Path

from ...utils.logging import get_logger
logger = get_logger(__name__)


def calculate_pmf_pvalue(pet_count: int, r: float, p: float) -> float:
    """
    Calculate p-value using PMF: P(X >= K | NB(r, p))
    
    Args:
        pet_count: Observed PET count (K)
        r: NB shape parameter
        p: NB probability parameter
    
    Returns:
        p-value: Probability of observing >= K PETs by chance
    """
    try:
        # Use survival function: sf(k-1) = P(X > k-1) = P(X >= k)
        pvalue = stats.nbinom.sf(pet_count - 1, r, p)
        
        # Ensure p-value is in valid range [0, 1]
        pvalue = max(min(float(pvalue), 1.0), 0.0)
        
        return pvalue
    except Exception as e:
        logger.warning(f"Error calculating p-value for K={pet_count}, r={r}, p={p}: {e}")
        return 1.0


def calculate_pvalues(templates_file: str, output_file: str, significance_threshold: float = 0.05):
    """
    Calculate p-values for all templates and add significance column.
    Fully vectorized: processes all valid-NB templates in one scipy call
    instead of row-by-row iteration.

    Args:
        templates_file: Input templates_with_nb.csv from Phase 1
        output_file: Output templates_with_nb.csv with p-values
        significance_threshold: Threshold for significance (default: 0.05)
    """
    logger.info("╔════════════════════════════════════════════════════════════════════╗")
    logger.info("║   BACKGROUND SAMPLING - PHASE 2: PMF P-Value Calculation          ║")
    logger.info("╚════════════════════════════════════════════════════════════════════╝")
    logger.info(f"  Significance threshold: {significance_threshold}")

    logger.info(f"\n{'='*70}")
    logger.info(f"LOADING TEMPLATES FROM PHASE 1")
    logger.info(f"{'='*70}")
    logger.info(f"  File: {templates_file}")

    templates = pl.read_csv(templates_file, n_threads=0).to_pandas()
    logger.info(f"  Total templates: {len(templates):,}")

    # Initialize all p-values to 1.0 (default / non-significant)
    p_values = np.ones(len(templates))

    logger.info(f"\n{'='*70}")
    logger.info(f"CALCULATING P-VALUES (vectorized)")
    logger.info(f"{'='*70}")

    is_deg       = templates['is_degenerate'].values.astype(bool)
    pet_counts   = templates['PET_Count'].values.astype(np.int64)
    n_samples    = templates['n_background_samples'].values.astype(np.int64)
    r_vals       = templates['r'].values.astype(float)
    p_vals       = templates['p'].values.astype(float)

    # ── Case 1: valid NB — batch scipy call on the full subset ───────────
    valid_mask = (~is_deg) & (~np.isnan(r_vals)) & (~np.isnan(p_vals))
    if valid_mask.any():
        k  = pet_counts[valid_mask]
        rv = r_vals[valid_mask]
        pv = p_vals[valid_mask]
        # sf(k-1, r, p) = P(X >= k | NB(r, p))  — vectorized over all valid rows
        raw = stats.nbinom.sf(k - 1, rv, pv).astype(float)
        raw = np.clip(raw, 0.0, 1.0)
        p_values[valid_mask] = raw

    n_valid_nb = int(valid_mask.sum())

    # ── Case 2: degenerate with observed PETs > 0 ────────────────────────
    deg_pets_mask = is_deg & (pet_counts > 0) & (n_samples > 0)
    if deg_pets_mask.any():
        p_values[deg_pets_mask] = 1.0 / n_samples[deg_pets_mask]
    n_degenerate_with_pets = int(deg_pets_mask.sum())

    # ── Case 3 & 4: degenerate/zero-samples — already 1.0 by default ─────
    n_degenerate_no_pets = int((is_deg & (pet_counts == 0)).sum())
    n_zero_samples       = int((n_samples == 0).sum())

    templates['p_value'] = p_values

    logger.info(f"\n  P-Value Calculation Summary:")
    logger.info(f"    Valid NB (PMF calculation): {n_valid_nb:,}")
    logger.info(f"    Degenerate with PETs (p=1/n_samples): {n_degenerate_with_pets:,}")
    logger.info(f"    Degenerate no PETs (p=1.0): {n_degenerate_no_pets:,}")
    logger.info(f"    Zero samples (p=1.0): {n_zero_samples:,}")
    
    # P-value summary
    logger.info(f"\n{'='*70}")
    logger.info(f"P-VALUE SUMMARY")
    logger.info(f"{'='*70}")
    
    significant = templates[templates['p_value'] < significance_threshold]
    not_significant = templates[templates['p_value'] >= significance_threshold]
    
    logger.info(f"  Total templates: {len(templates):,}")
    total_t = len(templates) or 1
    logger.info(f"  p < {significance_threshold}: {len(significant):,} ({len(significant)/total_t*100:.1f}%)")
    logger.info(f"  p >= {significance_threshold}: {len(not_significant):,} ({len(not_significant)/total_t*100:.1f}%)")
    
    # Breakdown by type
    logger.info(f"\n  Templates with p < {significance_threshold} by Type:")
    for ptype in ['same_peak', 'cross_peak']:
        sig_type = significant[significant['Type'] == ptype]
        logger.info(f"    {ptype}: {len(sig_type):,}")
    
    # P-value distribution
    logger.info(f"\n  P-Value Distribution:")
    p_ranges = [
        (0.0, 0.001, "< 0.001"),
        (0.001, 0.01, "0.001-0.01"),
        (0.01, 0.05, "0.01-0.05"),
        (0.05, 0.1, "0.05-0.1"),
        (0.1, 1.0, "> 0.1")
    ]
    
    for low, high, label in p_ranges:
        count = ((templates['p_value'] >= low) & (templates['p_value'] < high)).sum()
        logger.info(f"    {label}: {count:,}")
    
    # Top 10 interactions with lowest p-values
    logger.info(f"\n  Top 10 Interactions with Lowest P-Values:")
    top_sig = templates.nsmallest(10, 'p_value')
    for idx, row in top_sig.iterrows():
        logger.info(f"    {row['Peak1_Index']} ↔ {row['Peak2_Index']} ({row['Type']}): "
                   f"PETs={row['PET_Count']}, p={row['p_value']:.6f}")
    
    # Save updated templates
    logger.info(f"\n{'='*70}")
    logger.info(f"SAVING RESULTS")
    logger.info(f"{'='*70}")
    logger.info(f"  Output file: {output_file}")
    
    pl.from_pandas(templates).write_csv(output_file)
    
    file_size = Path(output_file).stat().st_size / 1024 / 1024
    logger.info(f"  File size: {file_size:.2f} MB")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"PHASE 2 COMPLETE!")
    logger.info(f"{'='*70}")
    logger.info(f"  Templates with p-values saved to: {output_file}")
    logger.info(f"  Ready for downstream analysis and visualization!")


def main():
    parser = argparse.ArgumentParser(
        description='Background Sampling Phase 2: PMF P-Value Calculation'
    )
    parser.add_argument('templates_file', help='Input templates_with_nb.csv from Phase 1')
    parser.add_argument('output_file', help='Output templates_with_nb.csv with p-values')
    parser.add_argument('--threshold', type=float, default=0.05,
                       help='Significance threshold (default: 0.05)')
    
    args = parser.parse_args()
    
    try:
        calculate_pvalues(
            templates_file=args.templates_file,
            output_file=args.output_file,
            significance_threshold=args.threshold
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
