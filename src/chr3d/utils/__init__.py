"""Chr3D Utilities Package."""

from .restriction_sites import RestrictionSiteGenerator
from .loops_to_beddb import csv_to_bedpe, bedpe_to_bedpedb, verify_positions
from .detect_restriction_enzyme import detect as detect_restriction_enzyme



def restriction_site_generator(
    enzyme,
    genome_fasta: str,
    output_file: str,
    min_frag_size: int = 20,
    max_frag_size: int = 1_000_000,
):
    """Generate restriction fragment BED from a genome FASTA."""
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
    """Convert significant-loops CSV + narrowPeak → BEDPE → bedpedb (HiGlass)."""
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
    "restriction_site_generator",
    "loops_to_beddb",
    "detect_restriction_enzyme",
    "RestrictionSiteGenerator",
    "csv_to_bedpe",
    "bedpe_to_bedpedb",
    "verify_positions",
]
