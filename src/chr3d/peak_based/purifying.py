"""HiChIP PET Purification by Restriction Fragment Overlap."""

import argparse
import bisect
import os
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger(__name__)


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--bedpe", required=True, metavar="FILE",
        help="Input BEDPE file (deduplicated, from mapping step)",
    )
    p.add_argument(
        "--fragments", required=True, metavar="BED",
        help="Restriction fragment BED file (from restriction_sites.py)",
    )
    p.add_argument(
        "--output-dir", required=True, metavar="DIR",
        help="Output directory for purified files",
    )
    p.add_argument(
        "--min-insert-size", type=int, default=100, metavar="INT",
        help="Minimum insert size to keep a PET (default: 100)",
    )
    p.add_argument(
        "--prefix", default=None, metavar="STR",
        help="Output file prefix (default: derived from input BEDPE filename)",
    )
    return p.parse_args()


class FragmentIndex:
    """In-memory index of restriction fragments for fast overlap lookup."""

    def __init__(self, fragment_bed: str):
        """Load a 3-column BED file into sorted arrays."""
        self.starts: Dict[str, np.ndarray] = {}
        self.ends: Dict[str, np.ndarray] = {}
        self._n_frags = 0

        chrom_starts = defaultdict(list)
        chrom_ends = defaultdict(list)

        with open(fragment_bed) as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3:
                    continue
                chrom, start, end = parts[0], int(parts[1]), int(parts[2])
                chrom_starts[chrom].append(start)
                chrom_ends[chrom].append(end)

        for chrom in chrom_starts:
            s = np.array(chrom_starts[chrom], dtype=np.int64)
            e = np.array(chrom_ends[chrom], dtype=np.int64)
            order = np.argsort(s)
            self.starts[chrom] = s[order]
            self.ends[chrom] = e[order]
            self._n_frags += len(s)

        logger.info(f"FragmentIndex loaded: {len(self.starts)} chroms, {self._n_frags:,} fragments")

    @property
    def n_fragments(self) -> int:
        return self._n_frags

    def find_fragment(self, chrom: str, start: int, end: int) -> int:
        """Return the index of the fragment that overlaps [start, end), or -1."""
        if chrom not in self.starts:
            return -1

        frag_starts = self.starts[chrom]
        frag_ends = self.ends[chrom]
        n = len(frag_starts)

        idx = bisect.bisect_right(frag_starts, start) - 1
        for i in range(max(0, idx), min(n, idx + 3)):
            if frag_starts[i] < end and frag_ends[i] > start:
                return i

        for i in range(max(0, idx - 1), -1, -1):
            if frag_starts[i] < end and frag_ends[i] > start:
                return i
            if start - frag_starts[i] > 10_000_000:
                break

        return -1

    def get_fragment_coords(self, chrom: str, frag_idx: int) -> Tuple[int, int]:
        """Return (start, end) of fragment at given index."""
        return int(self.starts[chrom][frag_idx]), int(self.ends[chrom][frag_idx])

def compute_insert_size(
    read_start: int,
    read_end: int,
    strand: str,
    frag_start: int,
    frag_end: int,
) -> int:
    """Compute the fragment-level insert contribution for one read."""
    if strand == "+":
        return frag_end - read_start
    else:
        return read_end - frag_start


def purify_bedpe(
    bedpe_file: str,
    fragment_index: FragmentIndex,
    output_kept: str,
    output_removed: str,
    min_insert_size: int = 100,
) -> Dict:
    """Filter a BEDPE file by restriction fragment overlap."""
    stats = {
        "total": 0,
        "kept": 0,
        "removed_same_fragment": 0,
        "removed_unmappable": 0,
        "removed_short_insert": 0,
    }

    with (
        open(bedpe_file) as fin,
        open(output_kept, "w") as fout_kept,
        open(output_removed, "w") as fout_removed,
    ):
        for line in fin:
            line = line.rstrip("\n")
            if not line:
                continue
            stats["total"] += 1

            fields = line.split("\t")
            if len(fields) < 10:
                stats["removed_unmappable"] += 1
                fout_removed.write(f"{line}\t-1\t-1\tN\n")
                continue

            chr1, s1, e1 = fields[0], int(fields[1]), int(fields[2])
            chr2, s2, e2 = fields[3], int(fields[4]), int(fields[5])
            strand1, strand2 = fields[8], fields[9]
            frag_idx1 = fragment_index.find_fragment(chr1, s1, e1)
            frag_idx2 = fragment_index.find_fragment(chr2, s2, e2)

            if frag_idx1 >= 0 and frag_idx2 >= 0 and (
                chr1 != chr2 or frag_idx1 != frag_idx2
            ):
                f1_start, f1_end = fragment_index.get_fragment_coords(chr1, frag_idx1)
                f2_start, f2_end = fragment_index.get_fragment_coords(chr2, frag_idx2)

                insert_size = (
                    compute_insert_size(s1, e1, strand1, f1_start, f1_end)
                    + compute_insert_size(s2, e2, strand2, f2_start, f2_end)
                )

                if insert_size < min_insert_size:
                    stats["removed_short_insert"] += 1
                    continue
                fout_kept.write(
                    f"{line}\t{frag_idx1}\t{frag_idx2}\t{insert_size}\n"
                )
                stats["kept"] += 1
            else:
                if frag_idx1 < 0 or frag_idx2 < 0:
                    stats["removed_unmappable"] += 1
                else:
                    stats["removed_same_fragment"] += 1
                fout_removed.write(
                    f"{line}\t{frag_idx1}\t{frag_idx2}\tN\n"
                )

    return stats


def main():
    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    prefix = args.prefix
    if prefix is None:
        prefix = os.path.splitext(os.path.basename(args.bedpe))[0]

    output_kept = os.path.join(args.output_dir, f"{prefix}.filter.byres")
    output_removed = os.path.join(args.output_dir, f"{prefix}.insameres")

    print("=" * 70)
    print("HiChIP PET PURIFICATION")
    print("=" * 70)
    print(f"  Input BEDPE      : {args.bedpe}")
    print(f"  Fragment BED     : {args.fragments}")
    print(f"  Min insert size  : {args.min_insert_size}")
    print(f"  Output kept      : {output_kept}")
    print(f"  Output removed   : {output_removed}")
    print("=" * 70)

    t0 = time.time()
    print("\n[1] Loading restriction fragment index...")
    frag_index = FragmentIndex(args.fragments)
    print(f"    {frag_index.n_fragments:,} fragments across "
          f"{len(frag_index.starts)} chromosomes")
    print("\n[2] Purifying BEDPE...")
    stats = purify_bedpe(
        args.bedpe, frag_index, output_kept, output_removed,
        min_insert_size=args.min_insert_size,
    )

    elapsed = time.time() - t0
    total = stats["total"]
    print("\n" + "=" * 70)
    print("PURIFICATION RESULTS")
    print("=" * 70)
    print(f"  Total PETs           : {total:>12,}")
    print(f"  Kept (inter-frag)    : {stats['kept']:>12,}  "
          f"({100*stats['kept']/max(total,1):.1f}%)")
    print(f"  Same fragment        : {stats['removed_same_fragment']:>12,}  "
          f"({100*stats['removed_same_fragment']/max(total,1):.1f}%)")
    print(f"  Unmappable           : {stats['removed_unmappable']:>12,}  "
          f"({100*stats['removed_unmappable']/max(total,1):.1f}%)")
    print(f"  Short insert         : {stats['removed_short_insert']:>12,}  "
          f"({100*stats['removed_short_insert']/max(total,1):.1f}%)")
    print(f"  Time                 : {elapsed:.1f}s")
    print("=" * 70)
    stats_file = os.path.join(args.output_dir, f"{prefix}.purify_stats.txt")
    with open(stats_file, "w") as f:
        f.write(f"total_pets\t{total}\n")
        f.write(f"kept_inter_fragment\t{stats['kept']}\n")
        f.write(f"removed_same_fragment\t{stats['removed_same_fragment']}\n")
        f.write(f"removed_unmappable\t{stats['removed_unmappable']}\n")
        f.write(f"removed_short_insert\t{stats['removed_short_insert']}\n")
        kept_pct = 100 * stats["kept"] / max(total, 1)
        f.write(f"kept_percent\t{kept_pct:.2f}\n")
    print(f"\n  Stats written to: {stats_file}")

    return stats


if __name__ == "__main__":
    main()