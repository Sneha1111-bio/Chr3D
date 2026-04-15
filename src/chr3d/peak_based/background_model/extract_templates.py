#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   TEMPLATE EXTRACTION - Generate templates.csv from P2P PETs                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PURPOSE:                                                                    ║
║  - Read P2P_pets.txt with peak information                                  ║
║  - Group by peak pairs to create unique templates                           ║
║  - Calculate template parameters (width1, width2, distance)                 ║
║  - Save templates.csv with all peak information                             ║
║  - Ready for background sampling later                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import pandas as pd
import numpy as np
import argparse
from pathlib import Path

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
    cyto = pd.read_csv(cytoband_file, sep='\t', header=None,
                       names=['chrom', 'start', 'end', 'band', 'stain'])
    
    for chrom, group in cyto.groupby('chrom'):
        regions = []
        
        # Add centromere regions with buffer
        centromere = group[group['stain'] == 'acen']
        if not centromere.empty:
            regions.append((
                max(0, centromere['start'].min() - buffer_size),
                centromere['end'].max() + buffer_size
            ))
        
        if regions:
            problematic_regions[chrom] = regions
    
    logger.info(f"  Loaded problematic regions for {len(problematic_regions)} chromosomes")
    return problematic_regions


def is_in_problematic_region(chrom: str, position: int, problematic_regions: dict) -> bool:
    """
    Check if a position overlaps with problematic regions.
    """
    if chrom not in problematic_regions:
        return False
    
    for region_start, region_end in problematic_regions[chrom]:
        if region_start <= position <= region_end:
            return True
    
    return False


def extract_templates(p2p_file: str, peak_file: str, output_file: str, 
                     standard_chroms_only: bool = False, 
                     cytoband_file: str = None,
                     centromere_buffer: int = 5_000_000):
    """
    Extract templates from P2P PETs with peak information.
    
    Args:
        p2p_file: Path to P2P_pets.txt file
        peak_file: Path to broadPeak file
        output_file: Path to output templates.csv
    """
    logger.info("╔════════════════════════════════════════════════════════════════════╗")
    logger.info("║   TEMPLATE EXTRACTION FROM P2P PETS                                ║")
    logger.info("╚════════════════════════════════════════════════════════════════════╝")
    
    # Load problematic regions if cytoband file provided
    problematic_regions = {}
    if cytoband_file:
        problematic_regions = load_cytoband_regions(cytoband_file, centromere_buffer)
    
    # Log filtering options
    if standard_chroms_only:
        logger.info(f"Filtering: Standard chromosomes only (chr1-22, chrX, chrY)")
    if cytoband_file:
        logger.info(f"Filtering: Excluding problematic regions (centromeres)")
    
    # Load peak file to get actual peak widths
    logger.info(f"\nLoading peaks from: {peak_file}")
    peaks_df = pd.read_csv(peak_file, sep='\t', header=None,
                          names=['chr', 'start', 'end', 'name', 'score', 'strand',
                                'signalValue', 'pValue', 'qValue'])

    # Vectorized lookup dicts built in one pass (no iterrows)
    peak_widths    = dict(zip(peaks_df['name'], peaks_df['end'] - peaks_df['start']))
    peak_midpoints = dict(zip(peaks_df['name'], (peaks_df['start'] + peaks_df['end']) / 2))

    logger.info(f"  Loaded {len(peaks_df):,} peaks")
    logger.info(f"  Peak width range: {peaks_df['end'].sub(peaks_df['start']).min()}-{peaks_df['end'].sub(peaks_df['start']).max()} bp")
    
    # Load P2P PETs with peak information
    logger.info(f"\nLoading P2P PETs from: {p2p_file}")
    p2p_df = pd.read_csv(p2p_file, sep='\t', low_memory=False)
    
    logger.info(f"  Total P2P PETs: {len(p2p_df):,}")
    logger.info(f"  Columns: {list(p2p_df.columns)}")
    
    # Filter out PETs without peak information
    p2p_with_peaks = p2p_df[
        p2p_df['peak1_index'].notna() & 
        p2p_df['peak2_index'].notna()
    ].copy()
    
    logger.info(f"  P2P PETs with peak info: {len(p2p_with_peaks):,}")
    
    # Group by peak pairs to create templates
    logger.info("\nCreating templates by grouping peak pairs...")
    
    # Group by peak1_index, peak2_index, and type — vectorized aggregation
    grouped = p2p_with_peaks.groupby(['peak1_index', 'peak2_index', 'type'], sort=False)
    logger.info(f"  Total unique peak pairs: {len(grouped):,}")

    # Aggregate in one shot using vectorized groupby operations
    agg = grouped.agg(
        peak1_id=('peak1_id', 'first'),
        peak2_id=('peak2_id', 'first'),
        chrom1=('chr1', 'first'),
        chrom2=('chr2', 'first'),
        PET_Count=('chr1', 'size')
    ).reset_index()

    # Vectorized width lookup via map (much faster than per-row get)
    agg['Width1'] = agg['peak1_id'].map(peak_widths).fillna(1).astype(int)
    agg['Width2'] = agg['peak2_id'].map(peak_widths).fillna(1).astype(int)

    # Vectorized distance calculation
    mid1_series = agg['peak1_id'].map(peak_midpoints).fillna(0)
    mid2_series = agg['peak2_id'].map(peak_midpoints).fillna(0)
    cis_mask    = (agg['chrom1'] == agg['chrom2']) & (agg['type'] == 'cross_peak')
    agg['Distance'] = 0
    agg.loc[cis_mask, 'Distance'] = (mid2_series[cis_mask] - mid1_series[cis_mask]).abs().astype(int)

    # Rename and reorder columns to match original schema
    agg = agg.rename(columns={
        'peak1_index': 'Peak1_Index',
        'peak2_index': 'Peak2_Index',
        'peak1_id':    'Peak1_ID',
        'peak2_id':    'Peak2_ID',
        'type':        'Type',
        'chrom1':      'Chrom1',
        'chrom2':      'Chrom2',
    })
    agg['template_idx'] = range(1, len(agg) + 1)

    template_df = agg[['template_idx', 'Peak1_Index', 'Peak1_ID', 'Peak2_Index', 'Peak2_ID',
                        'Type', 'Chrom1', 'Chrom2', 'Width1', 'Width2', 'Distance', 'PET_Count']].copy()
    logger.info(f"\nCreating templates DataFrame...")
    
    # Filter to cis-interactions only (exclude trans-interactions)
    logger.info(f"\nFiltering to cis-interactions only (same chromosome)...")
    logger.info(f"  Before filtering: {len(template_df):,} templates")
    cis_count = (template_df['Chrom1'] == template_df['Chrom2']).sum()
    trans_count = (template_df['Chrom1'] != template_df['Chrom2']).sum()
    logger.info(f"    Cis templates: {cis_count:,}")
    logger.info(f"    Trans templates: {trans_count:,} (will be excluded)")
    
    template_df = template_df[template_df['Chrom1'] == template_df['Chrom2']].copy()
    template_df['template_idx'] = range(1, len(template_df) + 1)
    logger.info(f"  After filtering: {len(template_df):,} templates (cis-only)")
    
    # Apply distance clipping at 30K
    logger.info(f"\nApplying distance clipping (max 30,000 bp)...")
    max_distance = 30000
    template_df['Original_Distance'] = template_df['Distance'].copy()
    template_df['Distance_Clipped'] = template_df['Distance'] > max_distance
    
    clipped_count = template_df['Distance_Clipped'].sum()
    total_td = len(template_df) or 1
    logger.info(f"  Templates with distance > {max_distance:,} bp: {clipped_count:,} ({clipped_count/total_td*100:.1f}%)")
    
    if clipped_count > 0:
        logger.info(f"  Distance range before clipping: {template_df['Original_Distance'].min():.0f} - {template_df['Original_Distance'].max():.0f} bp")
        template_df['Distance'] = template_df['Distance'].clip(upper=max_distance)
        logger.info(f"  Distance range after clipping: {template_df['Distance'].min():.0f} - {template_df['Distance'].max():.0f} bp")
        logger.info(f"  ✅ Distance clipped to max {max_distance:,} bp")
    else:
        logger.info(f"  No templates required clipping")
    
    # Summary statistics
    logger.info(f"\n{'='*70}")
    logger.info(f"TEMPLATE SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"  Total templates: {len(template_df):,}")
    logger.info(f"  Same-peak templates: {(template_df['Type'] == 'same_peak').sum():,}")
    logger.info(f"  Cross-peak templates: {(template_df['Type'] == 'cross_peak').sum():,}")
    logger.info(f"  Total PETs represented: {template_df['PET_Count'].sum():,}")
    logger.info(f"  Average PETs per template: {template_df['PET_Count'].mean():.1f}")
    logger.info(f"  Median PETs per template: {template_df['PET_Count'].median():.0f}")
    logger.info(f"  Max PETs in a template: {template_df['PET_Count'].max():,}")
    
    # Width and distance statistics
    logger.info(f"\nTemplate Parameter Statistics:")
    logger.info(f"  Width1 - Mean: {template_df['Width1'].mean():.0f}, Median: {template_df['Width1'].median():.0f}")
    logger.info(f"  Width2 - Mean: {template_df['Width2'].mean():.0f}, Median: {template_df['Width2'].median():.0f}")
    logger.info(f"  Distance - Mean: {template_df['Distance'].mean():.0f}, Median: {template_df['Distance'].median():.0f}")
    
    # Apply filters before saving
    original_count = len(template_df)
    
    # Filter to standard chromosomes
    if standard_chroms_only:
        before = len(template_df)
        template_df = template_df[
            template_df['Chrom1'].isin(STANDARD_CHROMS) & 
            template_df['Chrom2'].isin(STANDARD_CHROMS)
        ].copy()
        logger.info(f"\nFiltered to standard chromosomes: {before:,} → {len(template_df):,}")
    
    # Filter problematic regions
    if problematic_regions:
        before = len(template_df)
        # peak_midpoints already built above (int version)
        peak_midpoints_int = dict(zip(peaks_df['name'],
                                      ((peaks_df['start'] + peaks_df['end']) // 2).astype(int)))

        # Vectorized filter: check each peak mid against problematic regions
        def _is_bad(chrom_series, peak_id_series):
            mids = peak_id_series.map(peak_midpoints_int).fillna(0).astype(int)
            bad  = np.zeros(len(chrom_series), dtype=bool)
            for chrom, regions in problematic_regions.items():
                chrom_mask = chrom_series.values == chrom
                if not chrom_mask.any():
                    continue
                for rs, re in regions:
                    in_region = (mids.values >= rs) & (mids.values <= re)
                    bad |= (chrom_mask & in_region)
            return bad

        bad1 = _is_bad(template_df['Chrom1'], template_df['Peak1_ID'])
        bad2 = _is_bad(template_df['Chrom2'], template_df['Peak2_ID'])
        template_df = template_df[~(bad1 | bad2)].copy()
        logger.info(f"Filtered problematic regions: {before:,} → {len(template_df):,}")
    
    # Re-index templates after filtering
    if len(template_df) < original_count:
        template_df['template_idx'] = range(1, len(template_df) + 1)
        logger.info(f"\nTotal templates after filtering: {len(template_df):,} (reduced from {original_count:,})")
    
    # Save to CSV
    logger.info(f"\nSaving templates to: {output_file}")
    template_df.to_csv(output_file, index=False)
    logger.info(f"  File size: {Path(output_file).stat().st_size / 1024 / 1024:.2f} MB")
    
    # Show sample templates
    logger.info(f"\nSample Templates (first 5):")
    for idx, row in template_df.head(5).iterrows():
        logger.info(f"  Template {row['template_idx']}:")
        logger.info(f"    Peaks: {row['Peak1_Index']} ({row['Peak1_ID']}) <-> {row['Peak2_Index']} ({row['Peak2_ID']})")
        logger.info(f"    Type: {row['Type']}, PETs: {row['PET_Count']}")
        logger.info(f"    Params: W1={row['Width1']}, W2={row['Width2']}, Dist={row['Distance']}")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"TEMPLATE EXTRACTION COMPLETE!")
    logger.info(f"{'='*70}")
    
    return template_df


def main():
    parser = argparse.ArgumentParser(
        description='Extract templates from P2P PETs with peak information'
    )
    parser.add_argument('p2p_file', help='Input P2P_pets.txt file')
    parser.add_argument('peak_file', help='Input broadPeak file')
    parser.add_argument('output_file', help='Output templates.csv file')
    parser.add_argument('--standard-chroms-only', action='store_true',
                       help='Include only standard chromosomes (chr1-22, chrX, chrY)')
    parser.add_argument('--cytoband-file', type=str,
                       help='Cytoband file for filtering problematic regions')
    parser.add_argument('--centromere-buffer', type=int, default=5_000_000,
                       help='Buffer size around centromeres in bp (default: 5000000)')
    
    args = parser.parse_args()
    
    try:
        extract_templates(args.p2p_file, args.peak_file, args.output_file,
                        standard_chroms_only=args.standard_chroms_only,
                        cytoband_file=args.cytoband_file,
                        centromere_buffer=args.centromere_buffer)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
