# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
"""Fast converter: significant-loops CSV + broadPeak -> BEDPE -> bedpedb (HiGlass)."""
from __future__ import annotations

import argparse
import math
import os
import sqlite3
import subprocess
import sys
import time
from typing import Tuple

import numpy as np
import polars as pl


def load_peaks(peak_path: str) -> pl.DataFrame:
    """Load a broadPeak as polars DataFrame indexed by name (col 4)."""
    return pl.read_csv(
        peak_path,
        separator="\t",
        has_header=False,
        new_columns=[
            "chrom", "start", "end", "name", "score", "strand",
            "signalValue", "pValue", "qValue",
        ],
        schema_overrides={
            "chrom": pl.Utf8, "start": pl.Int64, "end": pl.Int64,
            "name": pl.Utf8,
        },
    ).select(["chrom", "start", "end", "name"])


def csv_to_bedpe(
    loops_csv: str,
    peaks_path: str,
    output_bedpe: str,
    p_value_col: str = "p_adj_fdr_bh",
    significant_col: str = "significant_fdr_bh",
    canonical_chroms_only: bool = True,
    max_score: float = 300.0,
) -> Tuple[pl.DataFrame, dict]:
    """Convert loops CSV -> BEDPE with importance score = -log10(p_value)."""
    stats: dict = {}
    t0 = time.time()

    print(f"[1/4] Reading peaks: {peaks_path}", flush=True)
    peaks = load_peaks(peaks_path)
    stats["n_peaks"] = peaks.height
    print(f"      {peaks.height:,} peaks in {time.time()-t0:.1f}s", flush=True)

    t1 = time.time()
    print(f"[2/4] Reading loops CSV: {loops_csv}", flush=True)
    needed = ["Peak1_ID", "Peak2_ID", "Chrom1", "Chrom2", p_value_col]
    if significant_col:
        needed.append(significant_col)
    loops = pl.read_csv(
        loops_csv,
        columns=needed,
        schema_overrides={
            "Peak1_ID": pl.Utf8, "Peak2_ID": pl.Utf8,
            "Chrom1": pl.Utf8, "Chrom2": pl.Utf8,
            p_value_col: pl.Float64,
        },
    )
    stats["n_loops_raw"] = loops.height
    print(f"      {loops.height:,} rows in {time.time()-t1:.1f}s", flush=True)

    if significant_col:
        before = loops.height
        loops = loops.filter(pl.col(significant_col).cast(pl.Boolean))
        stats["n_loops_significant"] = loops.height
        print(f"      kept {loops.height:,}/{before:,} significant rows",
              flush=True)

    if canonical_chroms_only:
        canonical = [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY", "chrM"]
        before = loops.height
        loops = loops.filter(
            pl.col("Chrom1").is_in(canonical) &
            pl.col("Chrom2").is_in(canonical)
        )
        print(f"      kept {loops.height:,}/{before:,} on canonical chroms",
              flush=True)

    t2 = time.time()
    print("[3/4] Joining peak coordinates (multi-threaded)...", flush=True)
    p1 = peaks.rename({"chrom": "p1_chrom", "start": "p1_start",
                       "end": "p1_end", "name": "Peak1_ID"})
    p2 = peaks.rename({"chrom": "p2_chrom", "start": "p2_start",
                       "end": "p2_end", "name": "Peak2_ID"})
    df = loops.join(p1, on="Peak1_ID", how="left") \
              .join(p2, on="Peak2_ID", how="left")
    before = df.height
    df = df.drop_nulls(["p1_chrom", "p2_chrom"])
    if df.height < before:
        print(f"      WARNING: dropped {before-df.height:,} unknown peak IDs",
              file=sys.stderr)
    stats["n_after_join"] = df.height
    mismatch = df.filter(
        (pl.col("p1_chrom") != pl.col("Chrom1")) |
        (pl.col("p2_chrom") != pl.col("Chrom2"))
    )
    stats["n_chrom_mismatch"] = mismatch.height
    if mismatch.height:
        print(f"      WARNING: {mismatch.height:,} chrom mismatches "
              "(CSV vs broadPeak); these are dropped", file=sys.stderr)
        df = df.filter(
            (pl.col("p1_chrom") == pl.col("Chrom1")) &
            (pl.col("p2_chrom") == pl.col("Chrom2"))
        )
    print(f"      joined to {df.height:,} rows in {time.time()-t2:.1f}s",
          flush=True)

    t3 = time.time()
    print("[4/4] Computing -log10(p) score and writing BEDPE...", flush=True)
    eps = 10 ** (-max_score)
    p_vec = df[p_value_col].to_numpy()
    p_safe = np.clip(p_vec, eps, None)
    score = np.clip(-np.log10(p_safe), 0, max_score).round(4)
    chrom1 = df["p1_chrom"].to_numpy()
    chrom2 = df["p2_chrom"].to_numpy()
    s1 = df["p1_start"].to_numpy().copy()
    e1 = df["p1_end"].to_numpy().copy()
    s2 = df["p2_start"].to_numpy().copy()
    e2 = df["p2_end"].to_numpy().copy()
    pid1 = df["Peak1_ID"].to_numpy()
    pid2 = df["Peak2_ID"].to_numpy()

    swap = (chrom1 == chrom2) & (s1 > s2)
    s1[swap], s2[swap] = s2[swap], s1[swap]
    e1[swap], e2[swap] = e2[swap], e1[swap]
    pid1c, pid2c = pid1.copy(), pid2.copy()
    pid1c[swap], pid2c[swap] = pid2[swap], pid1[swap]
    stats["n_swapped"] = int(swap.sum())

    out = pl.DataFrame({
        "chrom1": chrom1,
        "start1": s1, "end1": e1,
        "chrom2": chrom2,
        "start2": s2, "end2": e2,
        "name":   [f"{a}__{b}" for a, b in zip(pid1c, pid2c)],
        "score":  score,
    })

    os.makedirs(os.path.dirname(os.path.abspath(output_bedpe)) or ".",
                exist_ok=True)
    out.write_csv(output_bedpe, separator="\t", include_header=False)
    sz_mb = os.path.getsize(output_bedpe) / 1e6
    print(f"      wrote {out.height:,} rows -> {output_bedpe} "
          f"({sz_mb:.1f} MB) in {time.time()-t3:.1f}s", flush=True)
    print(f"      score range: {float(score.min()):.3f} .. "
          f"{float(score.max()):.3f}", flush=True)

    stats["n_final"] = out.height
    stats["total_seconds"] = time.time() - t0
    return out, stats


def bedpe_to_bedpedb(
    bedpe_path: str,
    output_bedpedb: str,
    assembly: str = "hg38",
    importance_col: int = 8,
    max_per_tile: int = 100,
    tile_size: int = 1024,
) -> str:
    """Run `clodius aggregate bedpe` to produce a SQLite bedpedb file."""
    print(f"[5/4] clodius aggregate bedpe -> {output_bedpedb}", flush=True)
    if os.path.exists(output_bedpedb):
        os.remove(output_bedpedb)
    cmd = [
        "clodius", "aggregate", "bedpe",
        "--assembly", assembly,
        "--importance-column", str(importance_col),
        "--max-per-tile", str(max_per_tile),
        "--tile-size", str(tile_size),
        "--output-file", output_bedpedb,
        "--chr1-col", "1", "--from1-col", "2", "--to1-col", "3",
        "--chr2-col", "4", "--from2-col", "5", "--to2-col", "6",
        bedpe_path,
    ]
    t0 = time.time()
    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if res.returncode != 0:
        print("STDOUT:", res.stdout, file=sys.stderr)
        print("STDERR:", res.stderr, file=sys.stderr)
        raise RuntimeError(f"clodius aggregate failed: {res.returncode}")
    sz_mb = os.path.getsize(output_bedpedb) / 1e6
    print(f"      bedpedb {sz_mb:.1f} MB in {time.time()-t0:.1f}s",
          flush=True)
    return output_bedpedb


def _bedpe_to_tsv_for_verify(bedpe_df: pl.DataFrame) -> str:
    """Convert BEDPE to TSV for verification."""
    tsv_path = "bedpe_for_verify.tsv"
    bedpe_df.write_csv(tsv_path, separator="\t", include_header=False)
    return tsv_path


def verify_positions(
    bedpe_df: pl.DataFrame,
    bedpedb_path: str,
    chromsizes_path: str,
    n_samples: int = 20,
) -> bool:
    """Verify that bedpedb entries match BEDPE coordinates.
    bedpedb stores coordinates as global genome offsets. We re-derive the
    offset from the chromsizes file and compare to a random sample.
    """
    print(f"\n[VERIFY] checking {n_samples} random entries against bedpedb",
          flush=True)

    tsv_path = _bedpe_to_tsv_for_verify(bedpe_df)
    expected = []
    cum = {}
    total = 0
    with open(chromsizes_path) as fh:
        for line in fh:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                cum[parts[0]] = total
                total += int(parts[1])

    sample = bedpe_df.sort("score", descending=True).head(n_samples)
    for r in sample.iter_rows(named=True):
        if r["chrom1"] not in cum or r["chrom2"] not in cum:
            continue
        gx = cum[r["chrom1"]] + r["start1"]
        gy = cum[r["chrom2"]] + r["start2"]
        expected.append((gx, gy, r["chrom1"], r["start1"],
                         r["chrom2"], r["start2"]))

    conn = sqlite3.connect(bedpedb_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    if "intervals" not in tables:
        print(f"      tables present: {tables}", file=sys.stderr)
        conn.close()
        return False

    cur.execute("SELECT * FROM intervals ORDER BY importance DESC LIMIT ?",
                (n_samples * 4,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()

    # Coordinate columns (defensive: clodius schemas vary)
    fx_col = "fromX" if "fromX" in cols else "from_x"
    fy_col = "fromY" if "fromY" in cols else "from_y"
    fx_idx = cols.index(fx_col)
    fy_idx = cols.index(fy_col)
    found = {(r[fx_idx], r[fy_idx]) for r in rows}

    ok = 0
    for gx, gy, c1, s1, c2, s2 in expected:
        # Allow either order; clodius may reorder fromX < fromY for some records
        if (gx, gy) in found or (gy, gx) in found:
            ok += 1
        else:
            # Find nearest match for diagnostic
            nearest = min(found, key=lambda p: abs(p[0]-gx) + abs(p[1]-gy),
                          default=(None, None))
            print(f"      MISS: BEDPE {c1}:{s1}({gx})  {c2}:{s2}({gy})  "
                  f"nearest_in_db={nearest}", file=sys.stderr)

    print(f"      matched {ok}/{len(expected)} top-importance entries")
    return ok == len(expected)


def convert_loops_to_bedpedb(
    loops_csv: str,
    peaks_broadpeak: str,
    output_bedpedb: str,
    assembly: str = "hg38",
    chromsizes: str = "",
    p_value_col: str = "p_adj_fdr_bh",
    significant_col: str = "significant_fdr_bh",
    verify: bool = True,
) -> dict:
    """Convert significant loops CSV + broadPeak -> BEDPE -> bedpedb (HiGlass).

    Convenience wrapper that chains csv_to_bedpe + bedpe_to_bedpedb + optional
    verification, and cleans up the intermediate BEDPE file.

    Args:
        loops_csv: Path to the significant loops CSV from background model.
        peaks_broadpeak: Path to the MACS3 broadPeak file.
        output_bedpedb: Path for the output bedpedb file.
        assembly: Genome assembly for clodius (default: "hg38").
        chromsizes: Path to chrom.sizes file for verification.
        p_value_col: Column name for p-values in the loops CSV.
        significant_col: Column name for significance flag in the loops CSV.
        verify: Whether to verify coordinates against the bedpedb (default: True).

    Returns:
        Dictionary with conversion statistics.
    """
    bedpe_path = output_bedpedb.replace(".bedpedb", ".bedpe")
    if bedpe_path == output_bedpedb:
        bedpe_path = output_bedpedb + ".bedpe"

    print(f"[1/2] Converting loops to BEDPE using {peaks_broadpeak}...")
    bedpe_df, stats = csv_to_bedpe(
        loops_csv=loops_csv,
        peaks_path=peaks_broadpeak,
        output_bedpe=bedpe_path,
        p_value_col=p_value_col,
        significant_col=significant_col,
    )

    print(f"[2/2] Aggregating to bedpedb -> {output_bedpedb}...")
    bedpe_to_bedpedb(
        bedpe_path=bedpe_path,
        output_bedpedb=output_bedpedb,
        assembly=assembly,
    )

    if verify and chromsizes and os.path.exists(chromsizes):
        print("[VERIFY] Checking coordinates...")
        ok = verify_positions(bedpe_df, output_bedpedb, chromsizes)
        if not ok:
            raise RuntimeError("bedpedb verification failed")

    if os.path.exists(bedpe_path):
        os.remove(bedpe_path)

    print(f"\nDone -> {output_bedpedb}")
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loops_csv", required=True)
    ap.add_argument("--peaks", required=True)
    ap.add_argument("--bedpe_out", required=True,
                    help="Intermediate BEDPE path")
    ap.add_argument("--bedpedb_out", required=True,
                    help="Final bedpedb (HiGlass) path")
    ap.add_argument("--chromsizes",
                    default="/workspace/workdisk3/rudhra/database/main_chroms"
                            "/hg38.chrom.sizes",
                    help="Used for verification + clodius aggregate")
    ap.add_argument("--assembly", default="hg38")
    ap.add_argument("--p_value_col", default="p_adj_fdr_bh")
    ap.add_argument("--significant_col", default="significant_fdr_bh")
    ap.add_argument("--n_threads", type=int, default=0,
                    help="0 = auto (polars uses all cores by default)")
    ap.add_argument("--skip_verify", action="store_true")
    args = ap.parse_args()

    if args.n_threads > 0:
        os.environ["POLARS_MAX_THREADS"] = str(args.n_threads)

    bedpe_df, stats = csv_to_bedpe(
        loops_csv=args.loops_csv,
        peaks_path=args.peaks,
        output_bedpe=args.bedpe_out,
        p_value_col=args.p_value_col,
        significant_col=args.significant_col,
    )

    bedpe_to_bedpedb(
        bedpe_path=args.bedpe_out,
        output_bedpedb=args.bedpedb_out,
        assembly=args.assembly,
    )

    if not args.skip_verify:
        ok = verify_positions(bedpe_df, args.bedpedb_out, args.chromsizes)
        if not ok:
            print("\nVERIFICATION FAILED", file=sys.stderr)
            sys.exit(2)
        print("\nVERIFICATION PASSED")

    print("\n" + "=" * 60)
    print("STATS")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:<22s} = {v}")
    print(f"\nbedpedb ready -> {args.bedpedb_out}")
    print("Use in HiGlass:")
    print("  ts = hg.LocalTileset(  # or InlineTileset on older versions")
    print("       datatype='bedlike',")
    print(f"       tiles=partial(bed2ddb.tiles, '{args.bedpedb_out}'),")
    print(f"       info=partial(bed2ddb.tileset_info, '{args.bedpedb_out}'),"
          ")")


if __name__ == "__main__":
    main()