"""
Chr3D Utilities Package

Convenience functions for common operations. Each function wraps the
underlying class/module for a simpler, function-call API.

Usage:
    from chr3d.utils import restriction_site_generator, loops_to_beddb

    # Generate restriction fragments
    stats = restriction_site_generator(
        enzyme="MboI",
        genome_fasta="/path/to/hg38.fa",
        output_file="fragments.bed",
    )

    # Convert loops CSV + narrowPeak → bedpedb
    stats = loops_to_beddb(
        loops_csv="significant_loops.csv",
        peaks_path="peaks.narrowPeak",
        output_bedpe="loops.bedpe",
        output_bedpedb="loops.bedpedb",
    )

For more control, import the underlying classes directly:
    from chr3d.utils.restriction_sites import RestrictionSiteGenerator
    from chr3d.utils.loops_to_beddb import csv_to_bedpe, bedpe_to_bedpedb, verify_positions
"""

from .restriction_sites import RestrictionSiteGenerator
from .loops_to_beddb import csv_to_bedpe, bedpe_to_bedpedb, verify_positions
from .detect_restriction_enzyme import detect as detect_restriction_enzyme


# ---------------------------------------------------------------------------
# Convenience functions (snake_case, one-call API)
# ---------------------------------------------------------------------------

def restriction_site_generator(
    enzyme,
    genome_fasta: str,
    output_file: str,
    min_frag_size: int = 20,
    max_frag_size: int = 1_000_000,
):
    """
    Generate restriction fragment BED from a genome FASTA.

    One-call wrapper around :class:`RestrictionSiteGenerator`.

    Args:
        enzyme: Enzyme name (e.g. ``"MboI"``), recognition site
                (e.g. ``"^GATC"``), or a list for multiple enzymes.
        genome_fasta: Path to genome FASTA file (must be indexed with
                     samtools faidx or pyfaidx).
        output_file: Path to output fragment BED file.
        min_frag_size: Minimum fragment length to keep (default: 20 bp).
        max_frag_size: Maximum fragment length to keep (default: 1 Mb).

    Returns:
        dict: Statistics dictionary with fragment counts per chromosome.

    Example::

        from chr3d.utils import restriction_site_generator

        stats = restriction_site_generator(
            enzyme="MboI",
            genome_fasta="/data/genomes/hg38.fa",
            output_file="hg38_MboI_fragments.bed",
        )
    """
    gen = RestrictionSiteGenerator(
        enzyme=enzyme,
        min_frag_size=min_frag_size,
        max_frag_size=max_frag_size,
    )
    return gen.generate_sites(
        genome_fasta=genome_fasta,
        output_file=output_file,
    )


def loops_to_beddb(
    loops_csv: str,
    peaks_path: str,
    output_bedpe: str,
    output_bedpedb: str,
    assembly: str = "hg38",
    p_value_col: str = "p_adj_fdr_bh",
    significant_col: str = "significant_fdr_bh",
    canonical_chroms_only: bool = True,
    max_score: float = 300.0,
    chromsizes_path: str = None,
    skip_verify: bool = False,
):
    """
    Convert significant-loops CSV + narrowPeak → BEDPE → bedpedb (HiGlass).

    One-call wrapper that chains :func:`csv_to_bedpe`,
    :func:`bedpe_to_bedpedb`, and optionally :func:`verify_positions`.

    Args:
        loops_csv: Path to significant loops CSV file.
        peaks_path: Path to narrowPeak file.
        output_bedpe: Path for intermediate BEDPE output.
        output_bedpedb: Path for final bedpedb (HiGlass SQLite) output.
        assembly: Genome assembly name (default: ``"hg38"``).
        p_value_col: Column name for p-values in loops CSV.
        significant_col: Column name for significance flag in loops CSV.
        canonical_chroms_only: Keep only canonical chromosomes.
        max_score: Maximum -log10(p) score (default: 300).
        chromsizes_path: Path to chromosome sizes file (needed for
                         verification).  If *None* and *skip_verify* is
                         ``False``, verification is skipped with a warning.
        skip_verify: Skip position verification step.

    Returns:
        dict: Combined statistics from all conversion steps, plus
              ``"verification_passed"`` key if verification was run.

    Example::

        from chr3d.utils import loops_to_beddb

        stats = loops_to_beddb(
            loops_csv="significant_loops.csv",
            peaks_path="peaks.narrowPeak",
            output_bedpe="loops.bedpe",
            output_bedpedb="loops.bedpedb",
            chromsizes_path="hg38.chrom.sizes",
        )
    """
    bedpe_df, stats = csv_to_bedpe(
        loops_csv=loops_csv,
        peaks_path=peaks_path,
        output_bedpe=output_bedpe,
        p_value_col=p_value_col,
        significant_col=significant_col,
        canonical_chroms_only=canonical_chroms_only,
        max_score=max_score,
    )

    bedpe_to_bedpedb(
        bedpe_path=output_bedpe,
        output_bedpedb=output_bedpedb,
        assembly=assembly,
    )

    if not skip_verify:
        if chromsizes_path is None:
            print("Warning: verification requested but no chromsizes_path "
                  "provided — skipping.", flush=True)
            stats["verification_passed"] = None
        else:
            ok = verify_positions(bedpe_df, output_bedpedb, chromsizes_path)
            stats["verification_passed"] = ok
    else:
        stats["verification_passed"] = None

    return stats


__all__ = [
    # Convenience functions (snake_case)
    "restriction_site_generator",
    "loops_to_beddb",
    "detect_restriction_enzyme",

    # Underlying classes / functions (for advanced use)
    "RestrictionSiteGenerator",
    "csv_to_bedpe",
    "bedpe_to_bedpedb",
    "verify_positions",
]
