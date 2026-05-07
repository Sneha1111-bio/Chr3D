#!/usr/bin/env python3
"""
PET Classification by Peak Overlap

Classify Paired-End Tags (PETs) from a BEDPE file based on whether their
anchors overlap with broad peaks from MACS3 peak calling.

NOTE: We classify PETs directly from BEDPE, NOT loops. Loops are formed
AFTER significance testing. This is the raw PET classification step.

Categories:
  1. P2P (Peak-to-Peak): Both anchors overlap broad peaks
  2. P2D (Peak-to-Distal): One anchor overlaps peak, other doesn't
  3. D2D (Distal-to-Distal): Neither anchor overlaps peaks

Overlap detection: anchor_start < peak_end AND anchor_end > peak_start
"""
import polars as pl
import numpy as np
from pathlib import Path
import logging
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from ...utils.logging import get_logger
logger = get_logger(__name__)

STANDARD_CHROMS = {f'chr{i}' for i in range(1, 23)} | {'chrX', 'chrY'}


def load_cytoband_regions(cytoband_file: str, buffer_size: int = 5_000_000):
    """
    Load problematic regions from cytoband file.
    Returns dict: {chromosome: [(start, end), ...]}
    """
    logger.info(f"Loading cytoband file: {cytoband_file}")
    logger.info(f"  Centromere buffer: {buffer_size / 1e6:.1f} Mb")
    
    problematic_regions = {}
    
    # Load cytoband file
    cyto = pl.read_csv(cytoband_file, separator='\t', has_header=False,
                       new_columns=['chrom', 'start', 'end', 'band', 'stain'])
    
    for chrom in cyto['chrom'].unique().to_list():
        group = cyto.filter(pl.col('chrom') == chrom)
        centromere = group.filter(pl.col('stain') == 'acen')
        if len(centromere) > 0:
            regions = [(
                max(0, centromere['start'].min() - buffer_size),
                centromere['end'].max() + buffer_size
            )]
            problematic_regions[chrom] = regions
    
    logger.info(f"  Loaded problematic regions for {len(problematic_regions)} chromosomes")
    return problematic_regions


def is_peak_in_problematic_region(chrom: str, start: int, end: int, problematic_regions: dict) -> bool:
    """
    Check if a peak overlaps with problematic regions.
    """
    if chrom not in problematic_regions:
        return False
    
    peak_mid = (start + end) // 2
    for region_start, region_end in problematic_regions[chrom]:
        if region_start <= peak_mid <= region_end:
            return True
    
    return False


def load_peaks(peak_file, standard_chroms_only=False, cytoband_file=None, centromere_buffer=5_000_000):
    """
    Load broad peaks into a dictionary organized by chromosome.
    Enables O(1) chromosome lookup and vectorized overlap checking.
    """
    logger.info(f"Loading peaks from: {peak_file}")
    
    # Peak format: chr, start, end, name, score, strand, signalValue, pValue, qValue
    # (broadPeak = 9 cols; narrowPeak = 10 cols — read first 9 only)
    col_names = ['chr', 'start', 'end', 'name', 'score', 'strand', 'signalValue', 'pValue', 'qValue']
    peaks_pl = pl.read_csv(
        peak_file, separator='\t', has_header=False,
        new_columns=col_names,
        n_threads=0,          # use all available threads
        columns=list(range(9))
    )
    
    original_count = len(peaks_pl)
    logger.info(f"  Loaded {original_count:,} broad peaks")
    
    # Apply filters
    if standard_chroms_only:
        before = len(peaks_pl)
        peaks_pl = peaks_pl.filter(pl.col('chr').is_in(list(STANDARD_CHROMS)))
        logger.info(f"  Filtered to standard chromosomes: {before:,} → {len(peaks_pl):,}")
    
    # Load and apply cytoband filtering
    if cytoband_file:
        problematic_regions = load_cytoband_regions(cytoband_file, centromere_buffer)
        before = len(peaks_pl)
        # Build exclusion mask
        keep_mask = pl.lit(True)
        for chrom, regions in problematic_regions.items():
            for rs, re in regions:
                mid_expr = (pl.col('start') + pl.col('end')) // 2
                bad = (
                    (pl.col('chr') == chrom) &
                    (mid_expr >= rs) & (mid_expr <= re)
                )
                keep_mask = keep_mask & (~bad)
        peaks_pl = peaks_pl.filter(keep_mask)
        logger.info(f"  Filtered problematic regions: {before:,} → {len(peaks_pl):,}")
    
    if len(peaks_pl) < original_count:
        logger.info(f"  Total peaks after filtering: {len(peaks_pl):,} (reduced from {original_count:,})")
    
    # Group by chromosome for faster lookup
    peaks_by_chr = {}
    peak_ids_by_chr = {}
    
    for chrom in peaks_pl['chr'].unique().to_list():
        chr_peaks = peaks_pl.filter(pl.col('chr') == chrom).sort('start')
        peaks_by_chr[chrom] = chr_peaks.select(['start', 'end']).to_numpy()
        peak_ids_by_chr[chrom] = chr_peaks['name'].to_list()
    
    logger.info(f"  Peaks across {len(peaks_by_chr)} chromosomes")
    
    # Return as Polars DataFrame
    return peaks_by_chr, peak_ids_by_chr, peaks_pl


def find_peak_id_vectorized(anchor_chr, anchor_pos, peaks_by_chr, peak_ids_by_chr):
    """
    Find which peak ID contains this position (vectorized for speed).
    Returns (peak_index, macs3_peak_id) or (-1, None) if no overlap.
    """
    if anchor_chr not in peaks_by_chr:
        return -1, None
    
    peaks = peaks_by_chr[anchor_chr]
    # Vectorized check: find first peak containing this position
    mask = (peaks[:, 0] <= anchor_pos) & (anchor_pos <= peaks[:, 1])
    indices = np.where(mask)[0]
    
    if len(indices) > 0:
        peak_idx = indices[0]
        peak_id = peak_ids_by_chr[anchor_chr][peak_idx]
        return peak_idx, peak_id
    return -1, None


def check_overlap(anchor_chr, anchor_start, anchor_end, peaks_by_chr):
    """
    Check if an anchor overlaps ANY peak on its chromosome.
    Uses vectorized numpy operations for efficiency.
    """
    if anchor_chr not in peaks_by_chr:
        return False
    
    peaks = peaks_by_chr[anchor_chr]
    
    overlaps = (anchor_start < peaks[:, 1]) & (anchor_end > peaks[:, 0])
    
    return np.any(overlaps)


def classify_pet_chunk(chunk_data):
    """
    Classify a chunk of PETs (for parallel processing).
    Fully vectorized per-chromosome overlap check — no Python row loop.
    Returns arrays of anchor1_overlaps and anchor2_overlaps.
    """
    chunk_df, peaks_by_chr = chunk_data

    n = len(chunk_df)
    anchor1_overlaps = np.zeros(n, dtype=bool)
    anchor2_overlaps = np.zeros(n, dtype=bool)

    chr1_arr = chunk_df['chr1'].values
    start1_arr = chunk_df['start1'].values.astype(np.int64)
    end1_arr   = chunk_df['end1'].values.astype(np.int64)
    chr2_arr = chunk_df['chr2'].values
    start2_arr = chunk_df['start2'].values.astype(np.int64)
    end2_arr   = chunk_df['end2'].values.astype(np.int64)

    for chrom, peaks in peaks_by_chr.items():
        p_starts = peaks[:, 0]
        p_ends   = peaks[:, 1]

        # Anchor 1 rows on this chrom
        mask1 = (chr1_arr == chrom)
        if mask1.any():
            s1 = start1_arr[mask1][:, None]
            e1 = end1_arr[mask1][:, None]
            hits1 = ((s1 < p_ends) & (e1 > p_starts)).any(axis=1)
            anchor1_overlaps[mask1] = hits1

        # Anchor 2 rows on this chrom
        mask2 = (chr2_arr == chrom)
        if mask2.any():
            s2 = start2_arr[mask2][:, None]
            e2 = end2_arr[mask2][:, None]
            hits2 = ((s2 < p_ends) & (e2 > p_starts)).any(axis=1)
            anchor2_overlaps[mask2] = hits2

    return anchor1_overlaps.tolist(), anchor2_overlaps.tolist()


def classify_pets(bedpe_file, peaks_by_chr, peak_ids_by_chr, peaks_df, n_cores=None, include_same_peak=False):
    """
    Classify PETs from BEDPE file based on peak overlap (parallelized).
    """
    logger.info(f"Loading PETs from BEDPE: {bedpe_file}")
    
    # BEDPE format: chr1 start1 end1 chr2 start2 end2 [optional columns]
    pets_pl = pl.read_csv(
        bedpe_file, separator='\t', has_header=False,
        infer_schema_length=10000, n_threads=0
    )
    
    n_cols = len(pets_pl.columns)
    logger.info(f"  Detected {n_cols} columns in BEDPE file")
    
    # Assign column names
    base_cols = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2']
    if n_cols >= 6:
        if n_cols == 6:
            all_cols = base_cols
        elif n_cols == 7:
            all_cols = base_cols + ['name']
        elif n_cols == 8:
            all_cols = base_cols + ['name', 'score']
        elif n_cols == 10:
            all_cols = base_cols + ['name', 'score', 'strand1', 'strand2']
        else:
            all_cols = base_cols + [f'col{i}' for i in range(6, n_cols)]
        pets_pl = pets_pl.rename(dict(zip(pets_pl.columns, all_cols)))
    else:
        raise ValueError(f"BEDPE file must have at least 6 columns, found {n_cols}")
    
    logger.info(f"  Loaded {len(pets_pl):,} PETs from BEDPE")
    
    # Convert to pandas for the numpy parallel overlap kernel
    import pandas as _pd
    pets_df = pets_pl.to_pandas()
    
    # PARALLEL CLASSIFICATION
    if n_cores is None:
        n_cores = cpu_count()

    logger.info(f"Classifying PETs by peak overlap (using {n_cores} cores)...")

    # Use 4x more chunks than cores so workers stay busy (no idle gaps)
    n_chunks = n_cores * 4
    chunk_size = max(1, len(pets_df) // n_chunks)
    chunks = [pets_df.iloc[i:i+chunk_size].copy() for i in range(0, len(pets_df), chunk_size)]

    logger.info(f"  Split {len(pets_df):,} PETs into {len(chunks)} chunks ({chunk_size:,} PETs/chunk)")
    logger.info(f"  Processing in parallel...")

    chunk_data = [(chunk, peaks_by_chr) for chunk in chunks]

    # imap keeps all workers busy while preserving order
    with Pool(processes=n_cores) as pool:
        results = list(pool.imap(
            classify_pet_chunk, chunk_data, chunksize=max(1, len(chunks) // n_cores)
        ))

    # Merge results (in order)
    anchor1_overlaps = []
    anchor2_overlaps = []
    for a1_list, a2_list in results:
        anchor1_overlaps.extend(a1_list)
        anchor2_overlaps.extend(a2_list)

    logger.info(f"  Parallel classification complete!")
    
    # Add overlap results to dataframe
    pets_df['anchor1_in_peak'] = anchor1_overlaps
    pets_df['anchor2_in_peak'] = anchor2_overlaps
    
    # PEAK-PAIR COUNTING: Track P2P interactions (same-peak + cross-peak)
    # AND ADD PEAK INFO TO P2P PETS
    logger.info("Counting peak-to-peak interactions and adding peak info to P2P PETs...")
    peak_pair_data = []  # List of (peak1, peak2, count, type)
    
    # Initialize peak columns for all PETs (will be filled only for P2P)
    pets_df['peak1_index'] = None
    pets_df['peak1_id'] = None
    pets_df['peak2_index'] = None
    pets_df['peak2_id'] = None
    pets_df['type'] = None
    
    p2p_mask = pets_df['anchor1_in_peak'].values & pets_df['anchor2_in_peak'].values
    p2p_pets = pets_df[p2p_mask].copy()
    
    if len(p2p_pets) > 0:
        logger.info(f"  Processing {len(p2p_pets):,} P2P PETs...")
        
        # Midpoint calculation
        p2p_pets['mid1'] = (p2p_pets['start1'].values + p2p_pets['end1'].values) // 2
        p2p_pets['mid2'] = (p2p_pets['start2'].values + p2p_pets['end2'].values) // 2
        
        # Peak-ID lookup per chromosome
        def _lookup_peak_ids_for_chrom(chrom, positions, peaks_by_chr, peak_ids_by_chr):
            """Return (peak_idx_array, peak_id_array) for positions on chrom."""
            if chrom not in peaks_by_chr:
                return np.full(len(positions), -1, dtype=np.int64), np.full(len(positions), None, dtype=object)
            peaks = peaks_by_chr[chrom]
            ids   = peak_ids_by_chr[chrom]
            p_starts = peaks[:, 0]
            p_ends   = peaks[:, 1]
            out_idx = np.full(len(positions), -1, dtype=np.int64)
            out_id  = np.full(len(positions), None, dtype=object)
            for i, pos in enumerate(positions):
                lo = np.searchsorted(p_starts, pos, side='right') - 1
                if lo >= 0 and p_starts[lo] <= pos <= p_ends[lo]:
                    out_idx[i] = lo
                    out_id[i]  = ids[lo]
            return out_idx, out_id

        p2p_pets['peak1_idx_num'] = -1
        p2p_pets['peak1_macs']    = None
        p2p_pets['peak2_idx_num'] = -1
        p2p_pets['peak2_macs']    = None

        for chrom in p2p_pets['chr1'].unique():
            rows_c = p2p_pets['chr1'] == chrom
            idx1, id1 = _lookup_peak_ids_for_chrom(
                chrom, p2p_pets.loc[rows_c, 'mid1'].values, peaks_by_chr, peak_ids_by_chr)
            p2p_pets.loc[rows_c, 'peak1_idx_num'] = idx1
            p2p_pets.loc[rows_c, 'peak1_macs']    = id1

        for chrom in p2p_pets['chr2'].unique():
            rows_c = p2p_pets['chr2'] == chrom
            idx2, id2 = _lookup_peak_ids_for_chrom(
                chrom, p2p_pets.loc[rows_c, 'mid2'].values, peaks_by_chr, peak_ids_by_chr)
            p2p_pets.loc[rows_c, 'peak2_idx_num'] = idx2
            p2p_pets.loc[rows_c, 'peak2_macs']    = id2

        # Keep only rows where both peaks were found
        valid_mask = (p2p_pets['peak1_idx_num'] >= 0) & (p2p_pets['peak2_idx_num'] >= 0)
        p2p_valid  = p2p_pets[valid_mask].copy()

        p2p_valid['peak1_index_id'] = p2p_valid['chr1'].astype(str) + '_' + p2p_valid['peak1_idx_num'].astype(str)
        p2p_valid['peak2_index_id'] = p2p_valid['chr2'].astype(str) + '_' + p2p_valid['peak2_idx_num'].astype(str)
        p2p_valid['pet_type']       = np.where(
            p2p_valid['peak1_index_id'] == p2p_valid['peak2_index_id'], 'same_peak', 'cross_peak')

        # Write back to main dataframe
        pets_df.loc[p2p_valid.index, 'peak1_index'] = p2p_valid['peak1_index_id'].values
        pets_df.loc[p2p_valid.index, 'peak1_id']    = p2p_valid['peak1_macs'].values
        pets_df.loc[p2p_valid.index, 'peak2_index'] = p2p_valid['peak2_index_id'].values
        pets_df.loc[p2p_valid.index, 'peak2_id']    = p2p_valid['peak2_macs'].values
        pets_df.loc[p2p_valid.index, 'type']        = p2p_valid['pet_type'].values

        # Polars groupby for pair counting
        p2p_pl = pl.from_pandas(p2p_valid[[
            'chr1', 'chr2', 'peak1_index_id', 'peak1_macs',
            'peak2_index_id', 'peak2_macs', 'pet_type'
        ]].reset_index(drop=True))

        # Canonical pair key: sort so smaller index is always first
        p2p_pl = p2p_pl.with_columns([
            pl.when(pl.col('peak1_index_id') <= pl.col('peak2_index_id'))
              .then(pl.col('peak1_index_id'))
              .otherwise(pl.col('peak2_index_id'))
              .alias('pair_key1'),
            pl.when(pl.col('peak1_index_id') <= pl.col('peak2_index_id'))
              .then(pl.col('peak2_index_id'))
              .otherwise(pl.col('peak1_index_id'))
              .alias('pair_key2'),
            pl.when(pl.col('peak1_index_id') <= pl.col('peak2_index_id'))
              .then(pl.col('peak1_macs'))
              .otherwise(pl.col('peak2_macs'))
              .alias('canonical_macs1'),
            pl.when(pl.col('peak1_index_id') <= pl.col('peak2_index_id'))
              .then(pl.col('peak2_macs'))
              .otherwise(pl.col('peak1_macs'))
              .alias('canonical_macs2'),
        ])

        # Group and count by (pair_key1, pair_key2, pet_type)
        pair_counts = (
            p2p_pl
            .group_by(['pair_key1', 'pair_key2', 'pet_type'])
            .agg([
                pl.len().alias('count'),
                pl.col('canonical_macs1').first(),
                pl.col('canonical_macs2').first(),
            ])
        )

        for row in pair_counts.iter_rows(named=True):
            ptype = row['pet_type']
            if ptype == 'same_peak' and not include_same_peak:
                continue
            peak_pair_data.append((
                row['pair_key1'], row['canonical_macs1'],
                row['pair_key2'], row['canonical_macs2'],
                row['count'], ptype
            ))
    
    logger.info(f"  Found {len(peak_pair_data):,} peak-pair entries (same + cross)")
    pets_df.peak_pair_data = peak_pair_data
    
    # STEP C: Vectorized category assignment
    pets_df['category'] = 'D2D'  # Default: Distal-to-Distal
    pets_df.loc[pets_df['anchor1_in_peak'] & pets_df['anchor2_in_peak'], 'category'] = 'P2P'
    pets_df.loc[(pets_df['anchor1_in_peak'] ^ pets_df['anchor2_in_peak']), 'category'] = 'P2D'
    
    return pets_df


def summarize_classification(pets_df):
    """
    Print PET classification summary.
    """
    logger.info("=" * 70)
    logger.info("PET CLASSIFICATION SUMMARY")
    logger.info("=" * 70)
    
    total = len(pets_df)
    cat_col = pets_df['category']
    p2p = int((cat_col == 'P2P').sum())
    p2d = int((cat_col == 'P2D').sum())
    d2d = int((cat_col == 'D2D').sum())
    
    logger.info(f"Total PETs: {total:,}")
    logger.info("")
    logger.info(f"Peak-to-Peak (P2P): {p2p:,} ({p2p/total*100:.1f}%)")
    logger.info(f"  Both anchors overlap broad peaks")
    logger.info("")
    logger.info(f"Peak-to-Distal (P2D): {p2d:,} ({p2d/total*100:.1f}%)")
    logger.info(f"  One anchor overlaps peak, other doesn't")
    logger.info("")
    logger.info(f"Distal-to-Distal (D2D): {d2d:,} ({d2d/total*100:.1f}%)")
    logger.info(f"  Neither anchor overlaps peaks")
    logger.info("")
    
    logger.info("=" * 70)
    
    return {
        'total': total,
        'P2P': p2p,
        'P2D': p2d,
        'D2D': d2d
    }


def export_by_category(pets_df, output_prefix):
    """
    Export PETs split by category.

    Output files:
      {prefix}.all_pets.classified.txt   (all PETs + category)
      {prefix}.P2P_pets.txt              (Peak-to-Peak only)
      {prefix}.P2D_pets.txt              (Peak-to-Distal only)
      {prefix}.D2D_pets.txt              (Distal-to-Distal only)
      {prefix}.classification_summary.txt (statistics)
    """
    logger.info("Exporting PETs by category...")
    
    # Convert to Polars for write
    pets_pl = pl.from_pandas(pets_df.reset_index(drop=True))
    
    # Export all PETs with category annotation
    all_file = f"{output_prefix}.all_pets.classified.txt"
    pets_pl.write_csv(all_file, separator='\t')
    logger.info(f"  All PETs with categories: {all_file}")
    
    # Export P2P PETs
    p2p_file = f"{output_prefix}.P2P_pets.txt"
    p2p_pl = pets_pl.filter(pl.col('category') == 'P2P')
    p2p_pl.write_csv(p2p_file, separator='\t')
    logger.info(f"  Peak-to-Peak PETs: {p2p_file} ({len(p2p_pl):,} PETs)")
    
    # Export P2D PETs
    p2d_file = f"{output_prefix}.P2D_pets.txt"
    p2d_pl = pets_pl.filter(pl.col('category') == 'P2D')
    p2d_pl.write_csv(p2d_file, separator='\t')
    logger.info(f"  Peak-to-Distal PETs: {p2d_file} ({len(p2d_pl):,} PETs)")
    
    # Export D2D PETs
    d2d_file = f"{output_prefix}.D2D_pets.txt"
    d2d_pl = pets_pl.filter(pl.col('category') == 'D2D')
    d2d_pl.write_csv(d2d_file, separator='\t')
    logger.info(f"  Distal-to-Distal PETs: {d2d_file} ({len(d2d_pl):,} PETs)")
    
    # Export summary statistics
    total = len(pets_pl)
    summary_file = f"{output_prefix}.classification_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("PET Classification Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total PETs: {total:,}\n\n")
        f.write(f"Peak-to-Peak (P2P): {len(p2p_pl):,} ({len(p2p_pl)/total*100:.1f}%)\n")
        f.write(f"Peak-to-Distal (P2D): {len(p2d_pl):,} ({len(p2d_pl)/total*100:.1f}%)\n")
        f.write(f"Distal-to-Distal (D2D): {len(d2d_pl):,} ({len(d2d_pl)/total*100:.1f}%)\n")
    
    logger.info(f"  Summary statistics: {summary_file}")
    
    # Export peak-pair counts (P2P interaction matrix with type column)
    if hasattr(pets_df, 'peak_pair_data') and pets_df.peak_pair_data:
        peak_pair_file = f"{output_prefix}.peak_pair_counts.csv"
        
        # Sort by PET_Count descending
        peak_pair_pl = pl.DataFrame(
            pets_df.peak_pair_data,
            schema=['Peak1_Index', 'Peak1_ID', 'Peak2_Index', 'Peak2_ID', 'PET_Count', 'Type'],
            orient='row'
        ).sort('PET_Count', descending=True)
        
        peak_pair_pl.write_csv(peak_pair_file)
        
        same_peak_entries = int((peak_pair_pl['Type'] == 'same_peak').sum())
        cross_peak_entries = int((peak_pair_pl['Type'] == 'cross_peak').sum())
        
        logger.info(f"  Peak-pair interaction matrix: {peak_pair_file}")
        logger.info(f"    Same-peak entries: {same_peak_entries:,}")
        logger.info(f"    Cross-peak entries: {cross_peak_entries:,}")
        logger.info(f"    Total entries: {len(peak_pair_pl):,}")


def main():
    """
    Main entry point for PET classification.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Classify PETs from BEDPE file by broad peak overlap',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
PET Classification Categories:
  P2P (Peak-to-Peak):     Both anchors overlap broad peaks
  P2D (Peak-to-Distal):   One anchor overlaps peak, other doesn't
  D2D (Distal-to-Distal): Neither anchor overlaps peaks

Example:
  python3 classify_pets.py \\
      /path/to/mapped.dedup.bedpe \\
      /path/to/broad_peaks.broadPeak \\
      /path/to/output/classified_pets

Output files:
  {prefix}.all_pets.classified.txt    All PETs with category column
  {prefix}.P2P_pets.txt               Peak-to-Peak PETs only
  {prefix}.P2D_pets.txt               Peak-to-Distal PETs only
  {prefix}.D2D_pets.txt               Distal-to-Distal PETs only
  {prefix}.classification_summary.txt Summary statistics
        """
    )
    
    parser.add_argument('bedpe_file', help='Input BEDPE file with PETs')
    parser.add_argument('peak_file', help='Broad peak file (broadPeak format from MACS3)')
    parser.add_argument('output_prefix', help='Output prefix for classified PETs')
    parser.add_argument('--include-same-peak', action='store_true', 
                       help='Include same-peak interactions in processing (default: excluded)')
    parser.add_argument('--standard-chroms-only', action='store_true',
                       help='Include only standard chromosomes (chr1-22, chrX, chrY)')
    parser.add_argument('--cytoband-file', type=str,
                       help='Cytoband file for filtering problematic regions')
    parser.add_argument('--centromere-buffer', type=int, default=5_000_000,
                       help='Buffer size around centromeres in bp (default: 5000000)')
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 70)
        logger.info("PET CLASSIFICATION BY PEAK OVERLAP")
        logger.info("=" * 70)
        logger.info(f"BEDPE file: {args.bedpe_file}")
        logger.info(f"Peak file:  {args.peak_file}")
        logger.info(f"Output:     {args.output_prefix}")
        if args.include_same_peak:
            logger.info("Same-peak interactions: INCLUDED")
        else:
            logger.info("Same-peak interactions: EXCLUDED (default)")
        if args.standard_chroms_only:
            logger.info("Peak filtering: Standard chromosomes only")
        if args.cytoband_file:
            logger.info(f"Peak filtering: Excluding centromeres (±{args.centromere_buffer/1e6:.1f}Mb)")
        logger.info("")
        
        # Load peaks (organized by chromosome)
        peaks_by_chr, peak_ids_by_chr, peaks_df = load_peaks(
            args.peak_file,
            standard_chroms_only=args.standard_chroms_only,
            cytoband_file=args.cytoband_file,
            centromere_buffer=args.centromere_buffer
        )
        
        # Classify PETs from BEDPE
        pets_df = classify_pets(args.bedpe_file, peaks_by_chr, peak_ids_by_chr, peaks_df, include_same_peak=args.include_same_peak)
        
        # Summarize classification
        stats = summarize_classification(pets_df)
        
        # Export by category
        export_by_category(pets_df, args.output_prefix)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("CLASSIFICATION COMPLETE!")
        logger.info("=" * 70)
        return 0
        
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())