#!/usr/bin/env python3
"""
Template Extraction - Generate templates.csv from P2P PETs

Read P2P_pets.txt with peak information, group by peak pairs to create
unique templates, calculate template parameters (width1, width2, distance),
and save templates.csv with all peak information.
"""

import logging
import polars as pl
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
    
    # Load cytoband file with Polars
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
    logger.info("TEMPLATE EXTRACTION FROM P2P PETS")
    
    # Load problematic regions if cytoband file provided
    problematic_regions = {}
    if cytoband_file:
        problematic_regions = load_cytoband_regions(cytoband_file, centromere_buffer)
    
    # Log filtering options
    if standard_chroms_only:
        logger.info(f"Filtering: Standard chromosomes only (chr1-22, chrX, chrY)")
    if cytoband_file:
        logger.info(f"Filtering: Excluding problematic regions (centromeres)")
    
    # Load peak file to get actual peak widths.
    # Handle both broadPeak (9 cols) and narrowPeak (10 cols) by reading the
    # first 9 columns — avoids column misalignment.
    logger.info(f"\nLoading peaks from: {peak_file}")
    peaks_pl = pl.read_csv(
        peak_file, separator='\t', has_header=False,
        new_columns=['chr', 'start', 'end', 'name', 'score', 'strand',
                     'signalValue', 'pValue', 'qValue'],
        columns=list(range(9)),
        n_threads=0
    )

    # Build lookup dicts
    peak_widths    = dict(zip(
        peaks_pl['name'].to_list(),
        (peaks_pl['end'] - peaks_pl['start']).to_list()
    ))
    peak_midpoints = dict(zip(
        peaks_pl['name'].to_list(),
        ((peaks_pl['start'] + peaks_pl['end']) / 2).to_list()
    ))

    widths_arr = (peaks_pl['end'] - peaks_pl['start'])
    logger.info(f"  Loaded {len(peaks_pl):,} peaks")
    logger.info(f"  Peak width range: {widths_arr.min()}-{widths_arr.max()} bp")
    
    # Load P2P PETs with peak information
    logger.info(f"\nLoading P2P PETs from: {p2p_file}")
    p2p_pl = pl.read_csv(p2p_file, separator='\t', n_threads=0, infer_schema_length=10000)
    
    logger.info(f"  Total P2P PETs: {len(p2p_pl):,}")
    logger.info(f"  Columns: {p2p_pl.columns}")
    
    # Filter out PETs without peak information
    p2p_with_peaks = p2p_pl.filter(
        pl.col('peak1_index').is_not_null() &
        pl.col('peak2_index').is_not_null()
    )
    
    logger.info(f"  P2P PETs with peak info: {len(p2p_with_peaks):,}")
    
    # Group by peak pairs to create templates
    logger.info("\nCreating templates by grouping peak pairs...")

    agg = (
        p2p_with_peaks
        .group_by(['peak1_index', 'peak2_index', 'type'])
        .agg([
            pl.col('peak1_id').first(),
            pl.col('peak2_id').first(),
            pl.col('chr1').first().alias('chrom1'),
            pl.col('chr2').first().alias('chrom2'),
            pl.len().alias('PET_Count'),
        ])
    )
    logger.info(f"  Total unique peak pairs: {len(agg):,}")

    # Width + distance lookup
    agg = agg.with_columns([
        pl.col('peak1_id').map_elements(lambda x: peak_widths.get(x, 1), return_dtype=pl.Int64).alias('Width1'),
        pl.col('peak2_id').map_elements(lambda x: peak_widths.get(x, 1), return_dtype=pl.Int64).alias('Width2'),
        pl.col('peak1_id').map_elements(lambda x: peak_midpoints.get(x, 0.0), return_dtype=pl.Float64).alias('mid1'),
        pl.col('peak2_id').map_elements(lambda x: peak_midpoints.get(x, 0.0), return_dtype=pl.Float64).alias('mid2'),
    ])

    # Distance: only for cis cross-peak interactions
    agg = agg.with_columns([
        pl.when(
            (pl.col('chrom1') == pl.col('chrom2')) & (pl.col('type') == 'cross_peak')
        )
        .then((pl.col('mid2') - pl.col('mid1')).abs().cast(pl.Int64))
        .otherwise(pl.lit(0, dtype=pl.Int64))
        .alias('Distance')
    ])

    # Rename and reorder
    agg = agg.rename({
        'peak1_index': 'Peak1_Index',
        'peak2_index': 'Peak2_Index',
        'peak1_id':    'Peak1_ID',
        'peak2_id':    'Peak2_ID',
        'type':        'Type',
        'chrom1':      'Chrom1',
        'chrom2':      'Chrom2',
    })
    agg = agg.with_columns(pl.Series('template_idx', range(1, len(agg) + 1)))

    template_df = agg.select([
        'template_idx', 'Peak1_Index', 'Peak1_ID', 'Peak2_Index', 'Peak2_ID',
        'Type', 'Chrom1', 'Chrom2', 'Width1', 'Width2', 'Distance', 'PET_Count'
    ])
    logger.info(f"\nCreating templates DataFrame...")
    
    # Filter to cis-interactions only (exclude trans-interactions)
    logger.info(f"\nFiltering to cis-interactions only (same chromosome)...")
    logger.info(f"  Before filtering: {len(template_df):,} templates")
    cis_count   = int((template_df['Chrom1'] == template_df['Chrom2']).sum())
    trans_count = int((template_df['Chrom1'] != template_df['Chrom2']).sum())
    logger.info(f"    Cis templates: {cis_count:,}")
    logger.info(f"    Trans templates: {trans_count:,} (will be excluded)")
    
    template_df = template_df.filter(pl.col('Chrom1') == pl.col('Chrom2'))
    template_df = template_df.with_columns(pl.Series('template_idx', range(1, len(template_df) + 1)))
    logger.info(f"  After filtering: {len(template_df):,} templates (cis-only)")
    
    # Apply distance clipping at 30K
    logger.info(f"\nApplying distance clipping (max 30,000 bp)...")
    max_distance = 30000
    template_df = template_df.with_columns([
        pl.col('Distance').alias('Original_Distance'),
        (pl.col('Distance') > max_distance).alias('Distance_Clipped'),
    ])
    
    clipped_count = int(template_df['Distance_Clipped'].sum())
    total_td = len(template_df) or 1
    logger.info(f"  Templates with distance > {max_distance:,} bp: {clipped_count:,} ({clipped_count/total_td*100:.1f}%)")
    
    if clipped_count > 0:
        logger.info(f"  Distance range before clipping: {template_df['Original_Distance'].min():.0f} - {template_df['Original_Distance'].max():.0f} bp")
        template_df = template_df.with_columns(
            pl.col('Distance').clip(upper_bound=max_distance)
        )
        logger.info(f"  Distance range after clipping: {template_df['Distance'].min():.0f} - {template_df['Distance'].max():.0f} bp")
        logger.info(f"  Distance clipped to max {max_distance:,} bp")
    else:
        logger.info(f"  No templates required clipping")
    
    # Summary statistics
    logger.info(f"\n{'='*70}")
    logger.info(f"TEMPLATE SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"  Total templates: {len(template_df):,}")
    logger.info(f"  Same-peak templates: {int((template_df['Type'] == 'same_peak').sum()):,}")
    logger.info(f"  Cross-peak templates: {int((template_df['Type'] == 'cross_peak').sum()):,}")
    logger.info(f"  Total PETs represented: {int(template_df['PET_Count'].sum()):,}")
    logger.info(f"  Average PETs per template: {template_df['PET_Count'].mean():.1f}")
    logger.info(f"  Median PETs per template: {template_df['PET_Count'].median():.0f}")
    logger.info(f"  Max PETs in a template: {int(template_df['PET_Count'].max()):,}")
    
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
        template_df = template_df.filter(
            pl.col('Chrom1').is_in(list(STANDARD_CHROMS)) &
            pl.col('Chrom2').is_in(list(STANDARD_CHROMS))
        )
        logger.info(f"\nFiltered to standard chromosomes: {before:,} → {len(template_df):,}")
    
    # Filter problematic regions using vectorised Polars expressions
    if problematic_regions:
        before = len(template_df)
        peak_midpoints_int = dict(zip(
            peaks_pl['name'].to_list(),
            ((peaks_pl['start'] + peaks_pl['end']) // 2).to_list()
        ))

        template_df = template_df.with_columns([
            pl.col('Peak1_ID').map_elements(lambda x: peak_midpoints_int.get(x, 0), return_dtype=pl.Int64).alias('_mid1'),
            pl.col('Peak2_ID').map_elements(lambda x: peak_midpoints_int.get(x, 0), return_dtype=pl.Int64).alias('_mid2'),
        ])

        keep_mask = pl.lit(True)
        for chrom, regions in problematic_regions.items():
            for rs, re in regions:
                bad1 = (pl.col('Chrom1') == chrom) & (pl.col('_mid1') >= rs) & (pl.col('_mid1') <= re)
                bad2 = (pl.col('Chrom2') == chrom) & (pl.col('_mid2') >= rs) & (pl.col('_mid2') <= re)
                keep_mask = keep_mask & (~bad1) & (~bad2)

        template_df = template_df.filter(keep_mask).drop(['_mid1', '_mid2'])
        logger.info(f"Filtered problematic regions: {before:,} → {len(template_df):,}")
    
    # Re-index templates after filtering
    if len(template_df) < original_count:
        template_df = template_df.with_columns(pl.Series('template_idx', range(1, len(template_df) + 1)))
        logger.info(f"\nTotal templates after filtering: {len(template_df):,} (reduced from {original_count:,})")
    
    # Save to CSV
    logger.info(f"\nSaving templates to: {output_file}")
    template_df.write_csv(output_file)
    logger.info(f"  File size: {Path(output_file).stat().st_size / 1024 / 1024:.2f} MB")
    
    # Show sample templates
    logger.info(f"\nSample Templates (first 5):")
    for row in template_df.head(5).iter_rows(named=True):
        logger.info(f"  Template {row['template_idx']}:")
        logger.info(f"    Peaks: {row['Peak1_Index']} ({row['Peak1_ID']}) <-> {row['Peak2_Index']} ({row['Peak2_ID']})")
        logger.info(f"    Type: {row['Type']}, PETs: {row['PET_Count']}")
        logger.info(f"    Params: W1={row['Width1']}, W2={row['Width2']}, Dist={row['Distance']}")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"TEMPLATE EXTRACTION COMPLETE!")
    logger.info(f"{'='*70}")
    
    return template_df.to_pandas()


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
