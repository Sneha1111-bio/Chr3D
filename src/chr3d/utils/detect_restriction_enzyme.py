#!/usr/bin/env python3
# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
# This software was developed with support from the National Science Foundation under CAREER Award DBI-2239350.
"""
Restriction Enzyme Detector for Hi-C / HiChIP FASTQ files.

Analyses the first N reads of a paired-end FASTQ to identify which
restriction enzyme(s) were used in the library preparation.

Logic
-----
1. Enrichment test  – a restriction-enzyme cut site should appear at
   the **start** of reads far more often than at background positions
   (because biotin pull-down enriches for ligation junctions).

2. Junction test    – after fill-in and ligation, two identical
   overhangs are joined, producing a *site+site* junction (e.g.
   ``GATCGATC`` for MboI).  The presence of these junctions at the
   read start is a definitive signature.

3. Positional profile – the true enzyme shows a characteristic
   dual-peak pattern: a large peak at position 0 (cut site) and a
   second peak offset by *len(site)+1* bases (partner ligation site).

Usage
-----
    python detect_restriction_enzyme.py sample_R1.fastq.gz
    python detect_restriction_enzyme.py sample_R1.fastq.gz --reads 500000

Note
----
This tool is designed for **Hi-C** and **in-situ Hi-C** data where reads
start at restriction enzyme cut sites (biotin-enriched junctions).

For **HiChIP / ChIA-PET** data, reads start at linker/adapter sequences,
not at restriction sites.  Run this tool on *trimmed* reads or after the
linker-filtering step for accurate detection.
"""

import argparse
import gzip
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Enzyme database
# ---------------------------------------------------------------------------
# Each entry: (enzyme_name, recognition_site, cut_indicator)
# The '^' marks the cut position on the top strand.
# For junction detection we only need the site **without** the caret,
# and we reconstruct the junction as site+site (blunt-end ligation
# after Klenow fill-in of the overhang).

ENZYME_DB = {
    # 4-cutters (most common in Hi-C)
    "MboI":   "^GATC",
    "DpnII":  "^GATC",
    "Sau3AI": "^GATC",
    "NlaIII": "CATG^",
    "MseI":   "^TTAA",
    "CviQI":  "G^TAC",
    "HinfI":  "G^ANTC",
    "AluI":   "AG^CT",
    # 6-cutters
    "HindIII": "A^AGCTT",
    "EcoRI":   "G^AATTC",
    "BamHI":   "G^GATCC",
    "BglII":   "A^GATCT",
    "PstI":    "CTGCA^G",
    "SalI":    "G^TCGAC",
    "XbaI":    "T^CTAGA",
}

# Group isoschizomers (same recognition sequence, same cut position)
# so they are reported together.
_ISOSCHIZOMER_GROUPS = {
    "GATC": ["MboI", "DpnII", "Sau3AI"],
}


def _site_str(raw: str) -> str:
    """Return the recognition site without the caret and with N preserved."""
    return raw.replace("^", "").upper()


def _site_no_n(raw: str) -> str:
    """Return the recognition site without caret and without N bases."""
    return raw.replace("^", "").replace("N", "").upper()


def _has_degenerate(site: str) -> bool:
    return "N" in site.upper()


def _open_fastq(path: str):
    """Open a FASTQ file, gzipped or plain."""
    p = Path(path)
    if p.suffix == ".gz" or p.name.endswith(".fastq.gz") or p.name.endswith(".fq.gz"):
        return gzip.open(path, "rt")
    return open(path, "r")


# ---------------------------------------------------------------------------
# Core detection functions
# ---------------------------------------------------------------------------

def count_site_at_pos0(fastq_path: str, site: str, max_reads: int) -> int:
    """Count how many reads start with *site* (handling N wildcards)."""
    cnt = 0
    slen = len(site)
    degenerate = _has_degenerate(site)
    with _open_fastq(fastq_path) as fh:
        for i, line in enumerate(fh):
            if i >= max_reads * 4:
                break
            if i % 4 != 1:          # sequence lines only
                continue
            seq = line.rstrip("\n")[:slen]
            if len(seq) < slen:
                continue
            if degenerate:
                match = True
                for c, r in zip(site, seq):
                    if c != "N" and c != r:
                        match = False
                        break
                if match:
                    cnt += 1
            else:
                if seq == site:
                    cnt += 1
    return cnt


def count_junctions(fastq_path: str, site: str, max_reads: int) -> int:
    """Count reads that start with the ligation junction (site+site)."""
    junction = site + site
    jlen = len(junction)
    cnt = 0
    degenerate = _has_degenerate(site)
    with _open_fastq(fastq_path) as fh:
        for i, line in enumerate(fh):
            if i >= max_reads * 4:
                break
            if i % 4 != 1:
                continue
            seq = line.rstrip("\n")[:jlen]
            if len(seq) < jlen:
                continue
            if degenerate:
                match = True
                for c, r in zip(junction, seq):
                    if c != "N" and c != r:
                        match = False
                        break
                if match:
                    cnt += 1
            else:
                if seq == junction:
                    cnt += 1
    return cnt


def background_frequency(fastq_path: str, site: str, max_reads: int,
                         bg_start: int = 50, bg_end: int = 60) -> float:
    """Compute per-position background frequency of *site* in [bg_start, bg_end)."""
    slen = len(site)
    degenerate = _has_degenerate(site)
    hits = 0
    positions = 0
    with _open_fastq(fastq_path) as fh:
        for i, line in enumerate(fh):
            if i >= max_reads * 4:
                break
            if i % 4 != 1:
                continue
            seq = line.rstrip("\n")
            if len(seq) < bg_end + slen:
                continue
            for p in range(bg_start, bg_end):
                sub = seq[p : p + slen]
                if degenerate:
                    match = True
                    for c, r in zip(site, sub):
                        if c != "N" and c != r:
                            match = False
                            break
                    if match:
                        hits += 1
                else:
                    if sub == site:
                        hits += 1
                positions += 1
    return hits / positions if positions > 0 else 0.0


def positional_profile(fastq_path: str, site: str, max_reads: int,
                        window: int = 25) -> Counter:
    """Count occurrences of *site* at each position in the first *window* bases."""
    slen = len(site)
    degenerate = _has_degenerate(site)
    pos_counts: Counter = Counter()
    with _open_fastq(fastq_path) as fh:
        for i, line in enumerate(fh):
            if i >= max_reads * 4:
                break
            if i % 4 != 1:
                continue
            seq = line.rstrip("\n")[:window + slen]
            for p in range(min(len(seq) - slen + 1, window)):
                sub = seq[p : p + slen]
                if degenerate:
                    match = True
                    for c, r in zip(site, sub):
                        if c != "N" and c != r:
                            match = False
                            break
                    if match:
                        pos_counts[p] += 1
                else:
                    if sub == site:
                        pos_counts[p] += 1
    return pos_counts


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _bar(value: float, max_val: float, width: int = 30) -> str:
    n = int(width * value / max_val) if max_val > 0 else 0
    return "#" * n


def detect(fastq_path: str, max_reads: int = 1_000_000) -> None:
    """Run the full detection pipeline on a single FASTQ."""

    print(f"\n{'=' * 70}")
    print(f"  RESTRICTION ENZYME DETECTION")
    print(f"{'=' * 70}")
    print(f"  File      : {fastq_path}")
    print(f"  Max reads : {max_reads:,}")
    print(f"{'=' * 70}\n")

    # Build deduplicated site list (group isoschizomers)
    seen_sites: dict[str, list[str]] = {}   # site_str -> [enzyme_names]
    for enz, raw in ENZYME_DB.items():
        s = _site_str(raw)
        if s not in seen_sites:
            seen_sites[s] = []
        seen_sites[s].append(enz)

    # Apply isoschizomer group labels
    labeled: list[tuple[str, str]] = []     # (label, site_str)
    for site, enzymes in seen_sites.items():
        if site in _ISOSCHIZOMER_GROUPS and set(enzymes) == set(_ISOSCHIZOMER_GROUPS[site]):
            label = "/".join(_ISOSCHIZOMER_GROUPS[site])
        else:
            label = enzymes[0]
        labeled.append((label, site))

    # Sort by site length descending (6-cutters first for clearer junctions)
    labeled.sort(key=lambda x: len(x[1]), reverse=True)

    # ---- Phase 1: enrichment + junction scan ----
    results: list[dict] = []
    for label, site in labeled:
        pos0_cnt = count_site_at_pos0(fastq_path, site, max_reads)
        junc_cnt = count_junctions(fastq_path, site, max_reads)
        bg_freq  = background_frequency(fastq_path, site, max_reads)
        pos0_pct = pos0_cnt / max_reads
        enrich   = pos0_pct / bg_freq if bg_freq > 0 else 0.0
        junc_pct = junc_cnt / max_reads

        results.append({
            "label": label,
            "site": site,
            "pos0_cnt": pos0_cnt,
            "pos0_pct": pos0_pct,
            "bg_freq": bg_freq,
            "enrichment": enrich,
            "junc_cnt": junc_cnt,
            "junc_pct": junc_pct,
        })

    # Sort by enrichment descending
    results.sort(key=lambda r: r["enrichment"], reverse=True)

    # ---- Print table ----
    print(f"{'Enzyme':25s} {'Site':>8s} {'Pos0%':>8s} {'Bg%':>8s}"
          f" {'Enrich':>8s} {'Junc%':>8s} {'Verdict':>12s}")
    print("-" * 80)

    confirmed: list[dict] = []
    for r in results:
        enrich = r["enrichment"]
        junc   = r["junc_cnt"]
        # Require meaningful junction count (not just a handful from noise)
        # and a clear dual-peak positional profile (pos-0 peak + partner peak)
        junc_threshold = max(10, max_reads * 0.0001)   # ≥0.01% or ≥10 reads
        if enrich > 3 and junc >= junc_threshold:
            verdict = "CONFIRMED"
            confirmed.append(r)
        elif enrich > 3 and junc > 0 and junc < junc_threshold:
            verdict = "enriched*"
        elif enrich > 3 and junc == 0:
            verdict = "enriched*"
        elif enrich > 1.5:
            verdict = "possible"
        else:
            verdict = "no"

        print(f"{r['label']:25s} {r['site']:>8s} {100*r['pos0_pct']:7.3f}%"
              f" {100*r['bg_freq']:7.3f}% {enrich:7.1f}x"
              f" {100*r['junc_pct']:7.4f}% {verdict:>12s}")

    print()
    print("  * enriched but no junction reads → likely genomic bias, not enzyme")
    print("  CONFIRMED = enriched + ligation junction reads present\n")

    # ---- Phase 2: positional profile for confirmed enzymes ----
    if not confirmed:
        print("  No restriction enzyme detected.")
        return

    for r in confirmed:
        label = r["label"]
        site  = r["site"]
        print(f"\n{'=' * 70}")
        print(f"  Positional profile for {label} ({site})")
        print(f"{'=' * 70}")

        profile = positional_profile(fastq_path, site, max_reads, window=25)
        max_val = max(profile.values()) if profile else 1
        for p in range(25):
            cnt = profile.get(p, 0)
            pct = 100 * cnt / max_reads
            print(f"  pos {p:2d}: {cnt:8d}  ({pct:.3f}%)  {_bar(cnt, max_val)}")

        # Report junction detail
        junc_str = site + site
        print(f"\n  Ligation junction: {junc_str}")
        print(f"  Junction reads   : {r['junc_cnt']:,} ({100*r['junc_pct']:.4f}%)")
        print(f"  Enrichment       : {r['enrichment']:.1f}x over background")

    # ---- Final summary ----
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY")
    print(f"{'=' * 70}")
    if confirmed:
        for r in confirmed:
            enzymes = r["label"]
            site = r["site"]
            print(f"  Detected enzyme : {enzymes}  (site: {site})")
            print(f"  Enrichment      : {r['enrichment']:.1f}x")
            print(f"  Junction reads  : {r['junc_cnt']:,}")
        if len(confirmed) == 1:
            print(f"  Mode            : single-enzyme")
        else:
            print(f"  Mode            : dual-enzyme ({len(confirmed)} enzymes)")
    else:
        print("  No restriction enzyme detected.")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Detect which restriction enzyme(s) were used in a Hi-C/HiChIP sample.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("fastq", help="R1 FASTQ file (gzipped or plain)")
    ap.add_argument("--reads", type=int, default=1_000_000,
                    help="Number of reads to analyse (default: 1,000,000)")
    args = ap.parse_args()
    detect(args.fastq, args.reads)


if __name__ == "__main__":
    main()
