#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   FDR CORRECTION - Multiple Testing Correction for ChIA-PET Results         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PURPOSE:                                                                    ║
║  - Load templates_with_nb_chromspec.csv with p-values                       ║
║  - Apply multiple testing correction methods:                               ║
║    * Bonferroni (most conservative)                                         ║
║    * Benjamini-Hochberg (FDR, standard)                                     ║
║    * Benjamini-Yekutieli (FDR, conservative)                                ║
║    * Holm (step-down method)                                                ║
║  - Add adjusted p-values and significance flags for each method             ║
║  - Generate comprehensive output CSV with all corrections                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import pandas as pd
import numpy as np
from statsmodels.stats.multitest import multipletests
import argparse
from pathlib import Path

from ...utils.logging import get_logger
logger = get_logger(__name__)


def apply_fdr_corrections(input_file: str, output_file: str, alpha: float = 0.05):
    """
    Apply multiple testing corrections to p-values.
    
    Args:
        input_file: Input CSV file with p-values
        output_file: Output CSV file with corrections
        alpha: Significance threshold (default: 0.05)
    """
    logger.info("╔════════════════════════════════════════════════════════════════════╗")
    logger.info("║   FDR CORRECTION - Multiple Testing Correction                    ║")
    logger.info("╚════════════════════════════════════════════════════════════════════╝")
    logger.info(f"  Significance threshold (α): {alpha}")
    
    # Load templates with p-values
    logger.info(f"\n{'='*70}")
    logger.info(f"LOADING TEMPLATES")
    logger.info(f"{'='*70}")
    logger.info(f"  Input file: {input_file}")
    
    templates = pd.read_csv(input_file)
    logger.info(f"  Total templates: {len(templates):,}")
    
    # Get p-values — ensure float dtype so np.isnan works
    p_values = templates['p_value'].astype(float).values
    logger.info(f"  P-values loaded: {len(p_values):,}")

    # Early-exit if no templates
    if len(templates) == 0:
        logger.warning("  No templates to process — writing empty output")
        templates.to_csv(output_file, index=False)
        return

    # Check for NaN or invalid p-values
    valid_p = ~np.isnan(p_values)
    logger.info(f"  Valid p-values: {valid_p.sum():,}")
    logger.info(f"  Invalid p-values: {(~valid_p).sum():,}")
    
    # Apply multiple testing corrections
    logger.info(f"\n{'='*70}")
    logger.info(f"APPLYING MULTIPLE TESTING CORRECTIONS")
    logger.info(f"{'='*70}")
    
    correction_methods = {
        'bonferroni': 'Bonferroni (most conservative)',
        'fdr_bh': 'Benjamini-Hochberg FDR (standard)',
        'fdr_by': 'Benjamini-Yekutieli FDR (conservative)',
        'holm': 'Holm step-down method'
    }
    
    results = {}
    
    for method, description in correction_methods.items():
        logger.info(f"\n  Applying {description}...")
        
        try:
            # Apply correction
            reject, p_adj, alpha_sidak, alpha_bonf = multipletests(
                p_values, 
                alpha=alpha, 
                method=method,
                is_sorted=False,
                returnsorted=False
            )
            
            # Store results
            results[method] = {
                'p_adj': p_adj,
                'reject': reject,
                'n_significant': reject.sum()
            }
            
            logger.info(f"    Adjusted p-values calculated: {len(p_adj):,}")
            logger.info(f"    Significant at α={alpha}: {reject.sum():,} ({reject.sum()/len(reject)*100:.2f}%)")
            
        except Exception as e:
            logger.error(f"    Error applying {method}: {e}")
            results[method] = {
                'p_adj': np.full_like(p_values, np.nan),
                'reject': np.zeros_like(p_values, dtype=bool),
                'n_significant': 0
            }
    
    # Add all corrections to templates DataFrame
    logger.info(f"\n{'='*70}")
    logger.info(f"ADDING CORRECTIONS TO TEMPLATES")
    logger.info(f"{'='*70}")
    
    # Original p-value significance
    templates['significant_raw'] = templates['p_value'] < alpha
    
    # Add each correction method
    for method in correction_methods.keys():
        templates[f'p_adj_{method}'] = results[method]['p_adj']
        templates[f'significant_{method}'] = results[method]['reject']
    
    logger.info(f"  Added columns:")
    logger.info(f"    - significant_raw (original p-value < {alpha})")
    for method in correction_methods.keys():
        logger.info(f"    - p_adj_{method} (adjusted p-value)")
        logger.info(f"    - significant_{method} (adjusted p-value < {alpha})")
    
    # Summary statistics
    logger.info(f"\n{'='*70}")
    logger.info(f"CORRECTION SUMMARY (α = {alpha})")
    logger.info(f"{'='*70}")
    logger.info(f"  Total templates: {len(templates):,}")
    logger.info(f"\n  Significant counts:")
    total_t = len(templates) or 1
    logger.info(f"  Raw p-value:           {templates['significant_raw'].sum():,} ({templates['significant_raw'].sum()/total_t*100:.2f}%)")
    logger.info(f"    Bonferroni:            {results['bonferroni']['n_significant']:,} ({results['bonferroni']['n_significant']/total_t*100:.2f}%)")
    logger.info(f"    Benjamini-Hochberg:    {results['fdr_bh']['n_significant']:,} ({results['fdr_bh']['n_significant']/total_t*100:.2f}%)")
    logger.info(f"    Benjamini-Yekutieli:   {results['fdr_by']['n_significant']:,} ({results['fdr_by']['n_significant']/total_t*100:.2f}%)")
    logger.info(f"    Holm:                  {results['holm']['n_significant']:,} ({results['holm']['n_significant']/total_t*100:.2f}%)")
    
    # P-value distribution for each method
    logger.info(f"\n  P-value distribution (adjusted):")
    for method in correction_methods.keys():
        p_adj = results[method]['p_adj']
        logger.info(f"\n    {method.upper()}:")
        logger.info(f"      p < 0.001:       {(p_adj < 0.001).sum():,}")
        logger.info(f"      0.001 ≤ p < 0.01: {((p_adj >= 0.001) & (p_adj < 0.01)).sum():,}")
        logger.info(f"      0.01 ≤ p < 0.05:  {((p_adj >= 0.01) & (p_adj < 0.05)).sum():,}")
        logger.info(f"      0.05 ≤ p < 0.1:   {((p_adj >= 0.05) & (p_adj < 0.1)).sum():,}")
        logger.info(f"      p ≥ 0.1:          {(p_adj >= 0.1).sum():,}")
    
    # Top 10 interactions by raw p-value
    logger.info(f"\n  Top 10 Interactions (by raw p-value):")
    top10 = templates.nsmallest(10, 'p_value')
    for idx, row in top10.iterrows():
        logger.info(f"    {row['Peak1_Index']} ↔ {row['Peak2_Index']}: "
                   f"PETs={row['PET_Count']}, "
                   f"p={row['p_value']:.6f}, "
                   f"BH_FDR={row['p_adj_fdr_bh']:.6f}")
    
    # Save results
    logger.info(f"\n{'='*70}")
    logger.info(f"SAVING RESULTS")
    logger.info(f"{'='*70}")
    logger.info(f"  Output file: {output_file}")
    
    templates.to_csv(output_file, index=False)
    
    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size:.2f} MB")
    logger.info(f"  Total columns: {len(templates.columns)}")
    
    # Column summary
    logger.info(f"\n  Columns in output file:")
    logger.info(f"    Original columns: {len([c for c in templates.columns if not c.startswith('p_adj_') and not c.startswith('significant_')])}")
    logger.info(f"    Added columns: {len([c for c in templates.columns if c.startswith('p_adj_') or c.startswith('significant_')])}")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"FDR CORRECTION COMPLETE!")
    logger.info(f"{'='*70}")
    logger.info(f"  Results saved to: {output_file}")
    logger.info(f"  Ready for downstream analysis!")


def main():
    parser = argparse.ArgumentParser(
        description='Apply FDR correction to ChIA-PET p-values',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply FDR correction with default threshold (0.05)
  python3 apply_fdr_correction.py templates_with_nb_chromspec.csv templates_with_fdr.csv
  
  # Apply with custom threshold
  python3 apply_fdr_correction.py templates_with_nb_chromspec.csv templates_with_fdr.csv --alpha 0.01
  
Output columns:
  - All original columns from input file
  - significant_raw: Significant by raw p-value
  - p_adj_bonferroni: Bonferroni-adjusted p-value
  - significant_bonferroni: Significant by Bonferroni
  - p_adj_fdr_bh: Benjamini-Hochberg FDR-adjusted p-value
  - significant_fdr_bh: Significant by Benjamini-Hochberg FDR
  - p_adj_fdr_by: Benjamini-Yekutieli FDR-adjusted p-value
  - significant_fdr_by: Significant by Benjamini-Yekutieli FDR
  - p_adj_holm: Holm-adjusted p-value
  - significant_holm: Significant by Holm method
        """
    )
    
    parser.add_argument('input_file', help='Input CSV file with p-values (e.g., templates_with_nb_chromspec.csv)')
    parser.add_argument('output_file', help='Output CSV file with FDR corrections (e.g., templates_with_fdr.csv)')
    parser.add_argument('--alpha', type=float, default=0.05,
                       help='Significance threshold (default: 0.05)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input_file).exists():
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    try:
        apply_fdr_corrections(args.input_file, args.output_file, args.alpha)
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
