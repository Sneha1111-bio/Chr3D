"""
Generate Cell × Bin matrix at a given resolution from per-cell .cool files.

Pipeline:
1. Load raw contact counts from each per-cell .cool file (no normalization in cool)
2. Aggregate to target resolution (coarsen if needed)
3. Build cell × bin matrix (raw integer counts)
4. Cell-wise normalization (divide by mean of non-zero bins)
5. Multiply by 10 for numerical scaling
6. Coverage filter (remove bins with <5% cell coverage)
7. HVB selection (top N bins by dispersion)
8. Output filtered CSV

Usage:
    python preprocessing.py --cells-dir <dir> --output <file.csv> [options]
    python preprocessing.py --cells-dir /sn-hic/cells --output matrix.csv
    python preprocessing.py --cells-dir /sn-hic/cells --output matrix.csv --resolution 1000000 --n-hvb 1000
"""

import argparse
import glob
import os
import time

import cooler
import numpy as np
import polars as pl


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--cells-dir', required=True, metavar='DIR',
                   help='Directory containing per-cell .cool files '
                        '(searched recursively for *.cool)')
    p.add_argument('--output', required=True, metavar='CSV',
                   help='Output CSV file path')
    p.add_argument('--resolution', type=int, default=1_000_000, metavar='BP',
                   help='Target bin resolution in bp (default: 1000000 = 1Mb). '
                        'If cool files are finer, bins are summed up to this resolution.')
    p.add_argument('--coverage-threshold', type=float, default=0.05, metavar='FLOAT',
                   help='Minimum fraction of cells a bin must be non-zero in '
                        'to pass coverage filter (default: 0.05 = 5%%)')
    p.add_argument('--n-hvb', type=int, default=1000, metavar='INT',
                   help='Number of highly variable bins to select (default: 1000)')
    p.add_argument('--intra-only', action='store_true', default=True,
                   help='Keep only intra-chromosomal contacts (default: True)')
    p.add_argument('--chroms', default=None, metavar='CSV',
                   help='Comma-separated list of chromosomes to include '
                        '(default: all autosomes + chrX)')
    return p.parse_args()


def discover_cool_files(cells_dir):
    """Find all .cool files under cells_dir, sorted by name."""
    pattern = os.path.join(cells_dir, '**', '*.cool')
    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        raise FileNotFoundError(f"No .cool files found under: {cells_dir}")
    return files


def coarsen_pixels(pixels_df, bins_df, cool_binsize, target_res):
    """
    Aggregate pixels from cool_binsize to target_res by summing counts
    within the coarsened bin.  Returns (row_global_bin, col_global_bin, count)
    arrays at target_res.
    """
    factor = target_res // cool_binsize
    coarse_bin1 = pixels_df['bin1_id'].values // factor
    coarse_bin2 = pixels_df['bin2_id'].values // factor
    counts      = pixels_df['count'].values.astype(np.float32)

    # Number of coarse bins per chrom
    chrom_sizes_bp = {row['chrom']: row['end']
                      for _, row in bins_df.drop_duplicates('chrom', keep='last').iterrows()}

    # Build global coarse bin offset per chrom (from the bins table)
    chrom_order = list(dict.fromkeys(bins_df['chrom'].tolist()))
    chrom_n_coarse = {}
    for ch in chrom_order:
        n_fine = (bins_df['chrom'] == ch).sum()
        chrom_n_coarse[ch] = int(np.ceil(n_fine / factor))

    coarse_offset = {}
    off = 0
    for ch in chrom_order:
        coarse_offset[ch] = off
        off += chrom_n_coarse[ch]
    total_coarse_bins = off

    # Map fine bin_id → chrom
    bin_chrom = bins_df['chrom'].values   # index = fine bin_id

    global_bin1 = np.array([coarse_offset[bin_chrom[b]] + (b // factor) for b in pixels_df['bin1_id'].values], dtype=np.int32)
    global_bin2 = np.array([coarse_offset[bin_chrom[b]] + (b // factor) for b in pixels_df['bin2_id'].values], dtype=np.int32)

    col_names = []
    for ch in chrom_order:
        for b in range(chrom_n_coarse[ch]):
            col_names.append(f"{ch}_bin{b:05d}")

    return global_bin1, global_bin2, counts, total_coarse_bins, col_names, chrom_order


def load_cell_matrix(cool_path, target_res, intra_only, valid_chroms,
                     coarse_offset, bin_layout_chroms, total_bins):
    """
    Load one .cool file and return (global_bin1, global_bin2, counts)
    using the shared coarse bin layout (coarse_offset, bin_layout_chroms).
    """
    c = cooler.Cooler(cool_path)
    cool_binsize = c.binsize

    if cool_binsize > target_res:
        raise ValueError(f"{cool_path}: cool binsize {cool_binsize} > target_res {target_res}")

    factor    = target_res // cool_binsize
    bins_df   = c.bins()[:]
    pixels_df = c.pixels()[:]

    # Map every fine bin_id → chrom name
    bin_chrom = bins_df['chrom'].values

    # Filter to valid chroms and intra only
    valid_set = set(valid_chroms) if valid_chroms else None
    b1 = pixels_df['bin1_id'].values
    b2 = pixels_df['bin2_id'].values
    ch1 = bin_chrom[b1]
    ch2 = bin_chrom[b2]

    keep = np.ones(len(pixels_df), dtype=bool)
    if valid_set:
        keep &= np.isin(ch1, list(valid_set)) & np.isin(ch2, list(valid_set))
    if intra_only:
        keep &= (ch1 == ch2)

    b1, b2 = b1[keep], b2[keep]
    ch1, ch2 = ch1[keep], ch2[keep]
    counts = pixels_df['count'].values[keep].astype(np.float32)

    if len(b1) == 0:
        return None, None, None

    # Global coarse bin id = coarse_offset[chrom] + (fine_bin_id // factor)
    # Vectorised: build per-row offset array from chrom name
    def to_global(b_arr, ch_arr):
        offsets = np.array([coarse_offset.get(ch, -1) for ch in ch_arr], dtype=np.int32)
        result  = np.where(offsets >= 0, offsets + (b_arr // factor), -1).astype(np.int32)
        return result

    gb1 = to_global(b1, ch1)
    gb2 = to_global(b2, ch2)

    # Remove any that mapped outside the valid layout
    valid = (gb1 >= 0) & (gb1 < total_bins) & (gb2 >= 0) & (gb2 < total_bins)
    return gb1[valid], gb2[valid], counts[valid]


def build_matrix(cool_files, target_res, intra_only, valid_chroms):
    """Build n_cells × n_bins raw count matrix from list of .cool files."""
    print(f"  Loading {len(cool_files)} cells...")

    # First pass: build shared coarse bin layout from first file
    c0     = cooler.Cooler(cool_files[0])
    bins0  = c0.bins()[:]
    factor = target_res // c0.binsize

    # Only keep chroms that are actually in valid_chroms
    if valid_chroms:
        bins0 = bins0[bins0['chrom'].isin(set(valid_chroms))].reset_index(drop=True)

    chrom_order    = list(dict.fromkeys(bins0['chrom'].tolist()))
    chrom_n_coarse = {}
    for ch in chrom_order:
        n_fine = int((bins0['chrom'] == ch).sum())
        chrom_n_coarse[ch] = int(np.ceil(n_fine / factor))

    coarse_offset = {}
    off = 0
    for ch in chrom_order:
        coarse_offset[ch] = off
        off += chrom_n_coarse[ch]
    total_bins = off

    col_names = []
    for ch in chrom_order:
        for b in range(chrom_n_coarse[ch]):
            col_names.append(f"{ch}_bin{b:05d}")

    print(f"  Bin layout: {len(chrom_order)} chroms, {total_bins:,} bins at {target_res:,} bp")

    cell_ids = [os.path.splitext(os.path.basename(f))[0] for f in cool_files]
    n_cells  = len(cool_files)
    matrix   = np.zeros((n_cells, total_bins), dtype=np.float32)

    for i, (path, cid) in enumerate(zip(cool_files, cell_ids)):
        t = time.time()
        gb1, gb2, counts = load_cell_matrix(
            path, target_res, intra_only, valid_chroms,
            coarse_offset, chrom_order, total_bins)
        if gb1 is None:
            print(f"    [{i+1}/{n_cells}] {cid}: 0 contacts (skipped)")
            continue
        # Upper-triangle only (bin1 <= bin2), avoid double-counting diagonal
        keep = gb1 <= gb2
        gb1c, gb2c, cc = gb1[keep], gb2[keep], counts[keep]
        np.add.at(matrix[i], gb1c, cc)
        off_diag = gb1c != gb2c
        np.add.at(matrix[i], gb2c[off_diag], cc[off_diag])
        print(f"    [{i+1}/{n_cells}] {cid}: {int(cc.sum()):,} contacts  ({time.time()-t:.1f}s)")

    return matrix, col_names, cell_ids


def main():
    args = parse_args()

    t0 = time.time()
    print("=" * 60)
    print("CHR3D  —  sn-Hi-C PREPROCESSING")
    print("=" * 60)
    print(f"  Cells dir  : {args.cells_dir}")
    print(f"  Output     : {args.output}")
    print(f"  Resolution : {args.resolution:,} bp")
    print(f"  Coverage   : >{args.coverage_threshold*100:.0f}%")
    print(f"  HVB count  : {args.n_hvb}")
    print("=" * 60)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    # Discover cool files
    cool_files = discover_cool_files(args.cells_dir)
    print(f"\nFound {len(cool_files)} cool files")

    # Determine valid chromosomes
    if args.chroms:
        valid_chroms = args.chroms.split(',')
    else:
        # Default: all chroms present in first file (autosomes + chrX)
        c0 = cooler.Cooler(cool_files[0])
        valid_chroms = [ch for ch in c0.chromnames
                        if ch.startswith('chr') and ch not in ('chrM', 'chrEBV')]

    print(f"  Chromosomes: {valid_chroms[:5]}{'...' if len(valid_chroms) > 5 else ''}")

    # BUILD RAW MATRIX
    print("\n" + "=" * 60)
    print("BUILDING RAW MATRIX")
    print("=" * 60)
    t1 = time.time()
    matrix, col_names, cell_ids = build_matrix(
        cool_files, args.resolution, args.intra_only, valid_chroms)
    n_cells, total_bins = matrix.shape
    print(f"\n  Raw matrix shape : {n_cells:,} cells × {total_bins:,} bins")
    n_nonzero = np.count_nonzero(matrix)
    print(f"  Sparsity         : {100*(1-n_nonzero/matrix.size):.1f}% zeros")
    print(f"  Built in {time.time()-t1:.1f}s")

    # STEP 1: CELL-WISE NORMALIZATION
    print("\n" + "=" * 60)
    print("STEP 1: CELL-WISE NORMALIZATION")
    print("=" * 60)
    t_norm = time.time()
    cell_sums   = matrix.sum(axis=1)
    cell_counts = np.count_nonzero(matrix, axis=1)
    cell_avgs   = np.divide(cell_sums, cell_counts,
                            out=np.zeros_like(cell_sums), where=cell_counts != 0)
    valid_mask  = cell_counts > 0
    print(f"  Cell averages range : {cell_avgs[valid_mask].min():.2f} – {cell_avgs[valid_mask].max():.2f}")
    print(f"  Mean cell average   : {cell_avgs[valid_mask].mean():.2f}")
    norm_matrix = np.divide(matrix, cell_avgs.reshape(-1, 1),
                            out=np.zeros_like(matrix), where=cell_avgs.reshape(-1, 1) != 0)
    print(f"  ✓ Completed in {time.time()-t_norm:.1f}s")

    # STEP 2: MULTIPLY BY 10
    print("\n" + "=" * 60)
    print("STEP 2: MULTIPLY BY 10")
    print("=" * 60)
    final_matrix = norm_matrix * 10.0
    sample_nz = final_matrix[final_matrix > 0][:5]
    print(f"  Sample values : {sample_nz}")
    print(f"  ✓ Completed")

    # STEP 3: COVERAGE FILTER
    print("\n" + "=" * 60)
    print("STEP 3: COVERAGE FILTER")
    print("=" * 60)
    t_cov = time.time()
    coverage      = (final_matrix > 0).mean(axis=0)
    coverage_mask = coverage > args.coverage_threshold
    print(f"  Threshold : >{args.coverage_threshold*100:.1f}%")
    print(f"  Bins before : {total_bins:,}")
    print(f"  Bins passing: {coverage_mask.sum():,}")
    print(f"  Bins removed: {(~coverage_mask).sum():,}")
    filtered_matrix    = final_matrix[:, coverage_mask]
    filtered_col_names = [col_names[i] for i in range(total_bins) if coverage_mask[i]]
    print(f"  Matrix after filter: {filtered_matrix.shape[0]:,} × {filtered_matrix.shape[1]:,}")
    print(f"  ✓ Completed in {time.time()-t_cov:.1f}s")

    # STEP 4: HVB SELECTION
    print("\n" + "=" * 60)
    print("STEP 4: HVB SELECTION (Highly Variable Bins)")
    print("=" * 60)
    t_hvb  = time.time()
    eps    = 1e-8
    b_mean = filtered_matrix.mean(axis=0)
    b_var  = filtered_matrix.var(axis=0)
    disp   = b_var / (b_mean + eps)
    n_hvb  = min(args.n_hvb, filtered_matrix.shape[1])
    top_idx     = np.argsort(disp)[::-1][:n_hvb]
    hvb_matrix  = filtered_matrix[:, top_idx]
    hvb_cols    = [filtered_col_names[i] for i in top_idx]
    print(f"  Dispersion range  : {disp.min():.4f} – {disp.max():.4f}")
    print(f"  Top-{n_hvb} disp range: {disp[top_idx].min():.4f} – {disp[top_idx].max():.4f}")
    print(f"  Final matrix: {hvb_matrix.shape[0]:,} × {hvb_matrix.shape[1]:,}")
    print(f"  ✓ Completed in {time.time()-t_hvb:.1f}s")

    # SAVE  (polars write_csv is ~4x faster than pandas for wide matrices)
    print(f"\nSaving to: {args.output}")
    t_save = time.time()
    result = pl.DataFrame(
        {'cell_id': cell_ids} |
        {col: hvb_matrix[:, j].tolist() for j, col in enumerate(hvb_cols)}
    )
    result.write_csv(args.output)
    n_rows, n_cols = len(cell_ids), len(hvb_cols)
    print(f"  Saved in {time.time()-t_save:.1f}s  ({os.path.getsize(args.output)/1e6:.1f} MB)")

    print("\n" + "=" * 60)
    print("PREPROCESSING COMPLETE")
    print("=" * 60)
    print(f"  Output file  : {args.output}")
    print(f"  Final shape  : {n_rows:,} cells × {n_cols:,} bins")
    print(f"  Resolution   : {args.resolution:,} bp/bin")
    print(f"  Pipeline     : raw counts → cell-norm → ×10 → coverage → HVB")
    print(f"  Total time   : {time.time()-t0:.1f}s")


if __name__ == '__main__':
    main()
