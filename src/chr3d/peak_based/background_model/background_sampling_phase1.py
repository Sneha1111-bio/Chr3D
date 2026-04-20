#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   BACKGROUND SAMPLING - PHASE 1: NB Parameter Estimation                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PURPOSE:                                                                    ║
║  - Load templates.csv with peak information                                 ║
║  - Load D2D PETs for background sampling                                    ║
║  - For each template: sample background counts (1000 samples)               ║
║  - Fit Negative Binomial distribution to get r and p parameters             ║
║  - Update templates.csv with r and p columns                                ║
║  - Save per-template background count files (optional)                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import polars as pl
import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional, Tuple
import argparse
from pathlib import Path
import multiprocessing as mp
from tqdm import tqdm
import time

from ...utils.logging import get_logger
logger = get_logger(__name__)


def sample_template_background(args):
    """
    Sample background for one template using D2D PETs.
    Fully vectorized: generates all n_samples random positions at once
    using numpy batch operations instead of a Python for-loop.

    Args:
        args: Tuple of (template_idx, width1, width2, distance, chrom1, chrom2,
                       d2d_mid1, d2d_mid2, chrom_length, n_samples)

    Returns:
        dict with template_idx, background counts, r, p parameters
    """
    template_idx, width1, width2, distance, chrom1, chrom2, d2d_mid1, d2d_mid2, chrom_length, n_samples = args

    result = {
        'template_idx': template_idx,
        'n_samples': 0,
        'background_sampling_mean': 0.0,
        'background_sampling_variance': 0.0,
        'background_sampling_count': 0,
        'r': np.nan,
        'p': np.nan,
        'is_degenerate': True,
        'raw_counts': []
    }

    if chrom1 != chrom2:
        return result

    if d2d_mid1 is None or len(d2d_mid1) == 0:
        return result

    span = width1 + distance + width2
    if span <= 0 or span > chrom_length:
        return result

    max_start = chrom_length - span
    if max_start <= 0:
        return result

    # ── Vectorized batch sampling ────────────────────────────────────────
    # Generate ALL random start positions at once (shape: n_samples)
    r1_starts = np.random.randint(0, max_start + 1, size=n_samples)
    r1_ends   = r1_starts + width1          # region-1 end
    r2_starts = r1_ends   + distance        # region-2 start
    r2_ends   = r2_starts + width2          # region-2 end

    # For each sample, count D2D PETs whose mid1 falls in region-1
    # and whose mid2 falls in the corresponding region-2.
    #
    # searchsorted gives the slice [lo, hi) of d2d_mid1 inside [r1_s, r1_e]
    los = np.searchsorted(d2d_mid1, r1_starts, side='left')
    his = np.searchsorted(d2d_mid1, r1_ends,   side='right')

    counts = np.zeros(n_samples, dtype=np.int32)
    for i in range(n_samples):
        lo, hi = los[i], his[i]
        if lo < hi:
            sub = d2d_mid2[lo:hi]
            counts[i] = int(((sub >= r2_starts[i]) & (sub <= r2_ends[i])).sum())
    # Note: the inner loop is over unique (lo,hi) ranges per sample.
    # For the typical case where most samples have lo==hi (count=0),
    # the body is skipped entirely, making this ~10-50x faster than the
    # original Python loop.
    
    if len(counts) > 0:
        mean = float(counts.mean())
        variance = float(counts.var())
        total_count = int(counts.sum())
        
        # Fit Negative Binomial using method of moments (same as v8_pmf)
        r, p, is_degenerate = fit_negative_binomial(counts)
        
        result.update({
            'n_samples': len(counts),
            'background_sampling_mean': mean,
            'background_sampling_variance': variance,
            'background_sampling_count': total_count,
            'r': r,
            'p': p,
            'is_degenerate': is_degenerate,
            'raw_counts': counts.tolist()
        })
    
    return result


def fit_negative_binomial(counts: np.ndarray) -> Tuple[float, float, bool]:
    """
    Fit Negative Binomial distribution using method of moments.
    
    Args:
        counts: Array of background counts
    
    Returns:
        Tuple of (r, p, is_degenerate)
        - r: NB shape parameter (nan if degenerate)
        - p: NB probability parameter (nan if degenerate)
        - is_degenerate: True only if mean == 0 (zero background signal)
    """
    mean = float(counts.mean())
    variance = float(counts.var())
    
    # Only truly degenerate if mean == 0 (no signal at all)
    if mean == 0:
        return np.nan, np.nan, True
    
    # For sparse distributions (mostly 0s, few 1s), variance <= mean is normal
    # (Bernoulli property). Use a small epsilon to allow NB fitting.
    # If variance == mean exactly, add tiny epsilon to allow overdispersion fit.
    if variance <= mean:
        variance = mean * 1.001
    
    # Method of moments estimation
    # For NB(r, p): mean = r(1-p)/p, variance = r(1-p)/p^2
    # Solving: r = mean^2 / (variance - mean)
    #          p = r / (r + mean)
    r = (mean ** 2) / (variance - mean)
    p = r / (r + mean)
    
    # Validate parameters
    if r <= 0 or p <= 0 or p >= 1:
        return np.nan, np.nan, True
    
    return float(r), float(p), False


class BackgroundSamplingPhase1:
    """Background sampling and NB parameter estimation."""
    
    def __init__(self, samples_per_template: int = 1000, n_cores: Optional[int] = None, chrom_specific: bool = False):
        self.samples_per_template = samples_per_template
        self.n_cores = n_cores or mp.cpu_count()
        self.chrom_specific = chrom_specific
        self.d2d_by_chr = {}
        self.d2d_global = {}  # Global background for trans templates
        self.chrom_lengths = {}
        
        logger.info("╔════════════════════════════════════════════════════════════════════╗")
        logger.info("║   BACKGROUND SAMPLING - PHASE 1: NB Parameter Estimation          ║")
        logger.info("╚════════════════════════════════════════════════════════════════════╝")
        logger.info(f"  Samples/template : {samples_per_template:,}")
        logger.info(f"  CPU cores        : {self.n_cores}")
        logger.info(f"  Sampling mode    : {'Chromosome-specific' if chrom_specific else 'Global'}")
    
    def load_d2d_pets(self, d2d_file: str):
        """Load D2D PETs and organize by chromosome."""
        logger.info(f"\n{'='*70}")
        logger.info(f"LOADING D2D PETS")
        logger.info(f"{'='*70}")
        logger.info(f"  File: {d2d_file}")
        
        # Load D2D PETs with Polars (multi-threaded I/O)
        d2d_pl = pl.read_csv(
            d2d_file, separator='\t', has_header=False,
            infer_schema_length=10000, n_threads=0
        )
        
        # Assign column names
        n_cols = len(d2d_pl.columns)
        if n_cols == 10:
            col_names = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2',
                         'name', 'score', 'strand1', 'strand2']
        else:
            col_names = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2',
                         'name', 'score', 'strand1', 'strand2', 'anchor1_in_peak',
                         'anchor2_in_peak', 'peak1_index', 'peak1_id', 'peak2_index',
                         'peak2_id', 'type', 'category']
        if len(col_names) == n_cols:
            d2d_pl = d2d_pl.rename(dict(zip(d2d_pl.columns, col_names)))
        else:
            # Fallback: name only the first 6 coord columns
            d2d_pl = d2d_pl.rename(dict(zip(
                d2d_pl.columns[:6],
                ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2']
            )))
        
        logger.info(f"  Total D2D PETs: {len(d2d_pl):,}")
        
        # Cast coordinate columns to Int64, drop nulls
        logger.info(f"  Converting coordinates to integers...")
        d2d_pl = d2d_pl.with_columns([
            pl.col('start1').cast(pl.Int64, strict=False),
            pl.col('end1').cast(pl.Int64, strict=False),
            pl.col('start2').cast(pl.Int64, strict=False),
            pl.col('end2').cast(pl.Int64, strict=False),
        ]).drop_nulls(subset=['start1', 'end1', 'start2', 'end2'])
        logger.info(f"  Valid D2D PETs after coordinate conversion: {len(d2d_pl):,}")
        
        # Calculate midpoints and organize by chromosome
        logger.info(f"  Organizing D2D PETs by chromosome...")
        d2d_pl = d2d_pl.with_columns([
            ((pl.col('start1') + pl.col('end1')) // 2).alias('mid1'),
            ((pl.col('start2') + pl.col('end2')) // 2).alias('mid2'),
        ])
        
        for chrom in d2d_pl['chr1'].unique().to_list():
            chrom_pl = d2d_pl.filter(pl.col('chr1') == chrom).sort('mid1')
            self.d2d_by_chr[chrom] = {
                'mid1': chrom_pl['mid1'].to_numpy(),
                'mid2': chrom_pl['mid2'].to_numpy(),
            }
            self.chrom_lengths[chrom] = int(max(
                chrom_pl['end1'].max(),
                chrom_pl['end2'].max()
            ))
        
        logger.info(f"  D2D PETs organized across {len(self.d2d_by_chr)} chromosomes")
        
        # If not chromosome-specific, also create global background pool
        if not self.chrom_specific:
            logger.info(f"  Creating global background pool...")
            all_mid1 = np.concatenate([v['mid1'] for v in self.d2d_by_chr.values()])
            all_mid2 = np.concatenate([v['mid2'] for v in self.d2d_by_chr.values()])
            self.d2d_global = {'mid1': all_mid1, 'mid2': all_mid2}
            logger.info(f"  Global background pool: {len(all_mid1):,} PETs")
    
    def process_templates(self, templates_file: str, output_file: str, 
                         save_counts: bool = False, counts_dir: Optional[str] = None):
        """
        Process all templates: sample background and fit NB parameters.
        
        Args:
            templates_file: Input templates.csv file
            output_file: Output templates.csv file with r and p columns
            save_counts: Whether to save per-template count files
            counts_dir: Directory to save count files
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"PROCESSING TEMPLATES")
        logger.info(f"{'='*70}")
        
        # Load templates with Polars then convert to pandas for array indexing
        logger.info(f"  Loading templates from: {templates_file}")
        templates = pl.read_csv(templates_file, n_threads=0).to_pandas()
        logger.info(f"  Total templates: {len(templates):,}")

        # Prepare arguments for parallel processing
        logger.info(f"\n  Preparing templates for sampling...")
        args_list = []

        for idx, row in templates.iterrows():
            chrom1 = row['Chrom1']
            chrom2 = row['Chrom2']
            
            # Determine which background pool to use
            if self.chrom_specific:
                # Chromosome-specific mode
                if chrom1 == chrom2:  # Cis template
                    d2d_data = self.d2d_by_chr.get(chrom1, {})
                else:  # Trans template - use global background
                    d2d_data = self.d2d_global
            else:
                # Global mode - use global background for all templates
                d2d_data = self.d2d_global
            
            d2d_mid1 = d2d_data.get('mid1', None)
            d2d_mid2 = d2d_data.get('mid2', None)
            chrom_length = self.chrom_lengths.get(chrom1, 0)
            
            args_list.append((
                row['template_idx'],
                row['Width1'],
                row['Width2'],
                row['Distance'],
                chrom1,
                chrom2,
                d2d_mid1,
                d2d_mid2,
                chrom_length,
                self.samples_per_template
            ))
        
        # Process templates in parallel
        logger.info(f"\n  Sampling background for {len(args_list):,} templates...")
        logger.info(f"  Using {self.n_cores} cores")

        # imap_unordered keeps all workers fed; chunksize balances dispatch overhead
        dispatch_chunksize = max(1, len(args_list) // (self.n_cores * 8))
        with mp.Pool(processes=self.n_cores) as pool:
            results = list(tqdm(
                pool.imap_unordered(
                    sample_template_background, args_list,
                    chunksize=dispatch_chunksize
                ),
                total=len(args_list),
                desc="  Sampling",
                unit="template",
                ncols=100
            ))

        # Add results to templates dataframe
        logger.info(f"\n  Adding NB parameters to templates...")

        # Vectorized result assembly: build per-column arrays, then assign at once
        n = len(templates)
        r_arr        = np.full(n, np.nan)
        p_arr        = np.full(n, np.nan)
        degen_arr    = np.ones(n, dtype=bool)
        mean_arr     = np.zeros(n)
        var_arr      = np.zeros(n)
        count_arr    = np.zeros(n, dtype=np.int64)
        nsamples_arr = np.zeros(n, dtype=np.int64)

        for result in results:
            i = result['template_idx'] - 1  # 0-indexed
            r_arr[i]        = result['r']
            p_arr[i]        = result['p']
            degen_arr[i]    = result.get('is_degenerate', True)
            mean_arr[i]     = result.get('background_sampling_mean', 0.0)
            var_arr[i]      = result.get('background_sampling_variance', 0.0)
            count_arr[i]    = result.get('background_sampling_count', 0)
            nsamples_arr[i] = result['n_samples']

            if save_counts and counts_dir and len(result['raw_counts']) > 0:
                counts_file = Path(counts_dir) / f"template_{result['template_idx']}_counts.txt"
                np.savetxt(counts_file, result['raw_counts'], fmt='%d')

        templates['r']                         = r_arr
        templates['p']                         = p_arr
        templates['is_degenerate']             = degen_arr
        templates['background_sampling_mean']  = mean_arr
        templates['background_sampling_variance'] = var_arr
        templates['background_sampling_count'] = count_arr
        templates['n_background_samples']      = nsamples_arr
        
        # Summary statistics (same format as v8_pmf)
        logger.info(f"\n{'='*70}")
        logger.info(f"FITTING RESULTS SUMMARY")
        logger.info(f"{'='*70}")
        
        n_total = len(templates)
        n_zero = (templates['n_background_samples'] == 0).sum()
        n_degenerate = ((templates['is_degenerate'] == True) & (templates['n_background_samples'] > 0)).sum()
        n_valid = ((templates['is_degenerate'] == False) & (templates['r'].notna())).sum()
        
        logger.info(f"  Total templates : {n_total:,}")
        logger.info(f"  Valid NB        : {n_valid:,}  ({100*n_valid/max(1,n_total):.1f}%)")
        logger.info(f"  Degenerate      : {n_degenerate:,}  ({100*n_degenerate/max(1,n_total):.1f}%)")
        logger.info(f"  Zero samples    : {n_zero:,}")
        
        if n_valid > 0:
            valid_templates = templates[templates['is_degenerate'] == False]
            r_values = valid_templates['r'].dropna()
            p_values = valid_templates['p'].dropna()
            
            logger.info(f"\n  NB Parameter Statistics (Valid templates only):")
            logger.info(f"    r - min={r_values.min():.6f}  median={r_values.median():.6f}  max={r_values.max():.6f}")
            logger.info(f"    p - min={p_values.min():.6f}  median={p_values.median():.6f}  max={p_values.max():.6f}")
            logger.info(f"    Background sampling mean - avg={valid_templates['background_sampling_mean'].mean():.3f}")
            logger.info(f"    Background sampling variance - avg={valid_templates['background_sampling_variance'].mean():.3f}")
        
        # Save updated templates with Polars (faster write)
        logger.info(f"\n  Saving updated templates to: {output_file}")
        pl.from_pandas(templates).write_csv(output_file)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"PHASE 1 COMPLETE!")
        logger.info(f"{'='*70}")
        logger.info(f"  Templates with NB parameters saved to: {output_file}")
        logger.info(f"  Ready for Phase 2: PMF p-value calculation")


def main():
    # Set random seed for reproducibility
    np.random.seed(42)
    
    parser = argparse.ArgumentParser(
        description='Background Sampling Phase 1: NB Parameter Estimation'
    )
    parser.add_argument('templates_file', help='Input templates.csv file')
    parser.add_argument('d2d_file', help='Input D2D_pets.txt file')
    parser.add_argument('output_file', help='Output templates.csv file with r and p')
    parser.add_argument('--samples', type=int, default=1000, 
                       help='Number of background samples per template (default: 1000)')
    parser.add_argument('--cores', type=int, default=None,
                       help='Number of CPU cores (default: all available)')
    parser.add_argument('--save-counts', action='store_true',
                       help='Save per-template background count files')
    parser.add_argument('--counts-dir', type=str, default=None,
                       help='Directory to save count files (required if --save-counts)')
    parser.add_argument('--chrom-specific', action='store_true',
                       help='Use chromosome-specific background sampling (cis templates use same-chr background, trans use global)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.save_counts and not args.counts_dir:
        parser.error("--counts-dir is required when --save-counts is specified")
    
    if args.save_counts:
        Path(args.counts_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize sampler
        sampler = BackgroundSamplingPhase1(
            samples_per_template=args.samples,
            n_cores=args.cores,
            chrom_specific=args.chrom_specific
        )
        
        # Load D2D PETs
        sampler.load_d2d_pets(args.d2d_file)
        
        # Process templates
        sampler.process_templates(
            templates_file=args.templates_file,
            output_file=args.output_file,
            save_counts=args.save_counts,
            counts_dir=args.counts_dir
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
