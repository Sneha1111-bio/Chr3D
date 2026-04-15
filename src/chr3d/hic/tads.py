"""
TAD / Compartment Calling Module
=================================
Insulation score / TAD boundary detection and A/B compartment calling
using cooltools.

Classes:
    HiCTADCaller:          Insulation scoring across all resolutions.
    HiCCompartmentCaller:  A/B compartment eigenvector (eigs_cis) calling.
"""

import os
import time
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

from ..utils.logging import get_logger

warnings.filterwarnings('ignore')
logger = get_logger(__name__)


# Default window sizes (bp). Valid windows per resolution are those that are
# multiples of the resolution AND within the per-resolution cap below.
DEFAULT_WINDOWS = [
    30_000, 50_000, 100_000, 200_000, 500_000, 1_000_000,
]

# Cap maximum window per resolution to avoid biologically meaningless and
# extremely slow combos (e.g. 1 Mb window at 5 kb resolution).
DEFAULT_MAX_WINDOW_PER_RES: Dict[int, int] = {
    5_000:   250_000,
    10_000:  500_000,
    25_000: 1_000_000,
    50_000: 1_000_000,
    100_000: 1_000_000,
}


class HiCTADCaller:
    """
    Insulation score and TAD boundary caller for Hi-C contact matrices.

    Operates on a single .mcool file (or plain .cool) and produces:
      - Per-resolution/per-window insulation score TSV files
      - TAD boundary BED files
      - A summary TSV across all resolution x window combinations

    Example::

        caller = HiCTADCaller(threads=16)
        stats = caller.run(
            mcool_file="sample.mcool",
            output_dir="results/tads",
            sample_id="sample1",
        )
    """

    def __init__(
        self,
        windows: Optional[List[int]] = None,
        max_window_per_res: Optional[Dict[int, int]] = None,
        threads: int = 1,
        ignore_diags: int = 2,
    ):
        """
        Args:
            windows: Window sizes in bp to test (default: DEFAULT_WINDOWS).
            max_window_per_res: Per-resolution window cap dict
                                (default: DEFAULT_MAX_WINDOW_PER_RES).
            threads: Threads available (used for progress only; cooltools is
                     single-threaded per call).
            ignore_diags: Diagonals to ignore in insulation calculation
                          (default: 2).
        """
        self.windows = windows or DEFAULT_WINDOWS
        self.max_window_per_res = max_window_per_res or DEFAULT_MAX_WINDOW_PER_RES
        self.threads = threads
        self.ignore_diags = ignore_diags

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        mcool_file: str,
        output_dir: str,
        sample_id: str,
        resolutions: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Run TAD calling on all resolutions present in *mcool_file*.

        Args:
            mcool_file: Path to .mcool (or .cool) file.
            output_dir: Directory where outputs are written.
            sample_id:  Sample identifier used in file names.
            resolutions: Explicit list of resolutions to process.
                         If None, all resolutions in the mcool are used.

        Returns:
            Dict with keys:
              - ``summary_tsv``   path to the summary file
              - ``boundary_beds`` list of BED file paths
              - ``n_success``     number of successful (res, window) combos
              - ``n_failed``      number of failed combos
              - ``resolutions``   list of resolutions processed
              - ``timing_sec``    wall-clock seconds
        """
        try:
            import cooler
            import cooltools
            import bioframe
        except ImportError as exc:
            raise RuntimeError(
                f"Missing dependency for TAD calling: {exc}. "
                "Install with: conda install -c bioconda cooltools cooler bioframe"
            ) from exc

        t0 = time.time()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 70)
        logger.info("STEP 5: TAD CALLING (insulation score)")
        logger.info("=" * 70)
        logger.info(f"  mcool    : {mcool_file}")
        logger.info(f"  output   : {output_dir}")
        logger.info(f"  sample   : {sample_id}")

        # --- Discover resolutions ---
        avail_res = self._list_resolutions(mcool_file)
        if resolutions:
            use_res = [r for r in resolutions if r in avail_res]
            skipped = [r for r in resolutions if r not in avail_res]
            if skipped:
                logger.warning(f"  Resolutions not in mcool (skipped): {skipped}")
        else:
            use_res = avail_res

        logger.info(f"  Resolutions: {use_res}")

        all_rows: List[dict] = []
        boundary_beds: List[str] = []

        for res in use_res:
            rows, beds = self._process_resolution(
                mcool_file, res, output_dir, sample_id,
                cooler=cooler, cooltools=cooltools, bioframe=bioframe,
            )
            all_rows.extend(rows)
            boundary_beds.extend(beds)

        # --- Write summary ---
        summary_df = pd.DataFrame(all_rows)
        summary_tsv = str(output_dir / f"{sample_id}_tad_summary.tsv")
        summary_df.to_csv(summary_tsv, sep='\t', index=False)

        n_success = int((summary_df['status'] == 'success').sum()) if len(summary_df) else 0
        n_failed  = int((summary_df['status'] != 'success').sum()) if len(summary_df) else 0

        elapsed = round(time.time() - t0, 2)
        logger.info(f"  Done — {n_success} combos OK, {n_failed} failed  ({elapsed}s)")
        logger.info(f"  Summary : {summary_tsv}")

        return {
            'summary_tsv':   summary_tsv,
            'boundary_beds': boundary_beds,
            'n_success':     n_success,
            'n_failed':      n_failed,
            'resolutions':   use_res,
            'timing_sec':    elapsed,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _list_resolutions(self, mcool_file: str) -> List[int]:
        """Return sorted list of resolutions stored in an mcool file."""
        import cooler
        try:
            paths = cooler.fileops.list_coolers(mcool_file)
            res = sorted(
                int(p.split('/')[-1])
                for p in paths
                if p.startswith('/resolutions/')
            )
            if res:
                return res
        except Exception:
            pass
        # Plain .cool — single resolution
        try:
            c = cooler.Cooler(mcool_file)
            return [c.binsize]
        except Exception:
            return []

    def _cooler_uri(self, mcool_file: str, res: int) -> str:
        import cooler
        paths = cooler.fileops.list_coolers(mcool_file)
        if any(p.startswith('/resolutions/') for p in paths):
            return f"{mcool_file}::/resolutions/{res}"
        return mcool_file

    def _valid_windows(self, res: int) -> List[int]:
        max_w = self.max_window_per_res.get(res, 1_000_000)
        return [w for w in self.windows if w >= res and w % res == 0 and w <= max_w]

    def _process_resolution(
        self,
        mcool_file: str,
        res: int,
        output_dir: Path,
        sample_id: str,
        cooler, cooltools, bioframe,
    ):
        """Run insulation scoring for all valid windows at one resolution."""
        windows = self._valid_windows(res)
        if not windows:
            logger.warning(f"  res={res}: no valid windows — skipping")
            return [], []

        res_dir = output_dir / f"res_{res // 1000}kb"
        res_dir.mkdir(parents=True, exist_ok=True)

        uri = self._cooler_uri(mcool_file, res)
        try:
            clr = cooler.Cooler(uri)
        except Exception as e:
            logger.error(f"  res={res}: cannot open cooler — {e}")
            return [{'resolution_bp': res, 'window_bp': w, 'status': f'failed: {e}'}
                    for w in windows], []

        # Build view excluding tiny chromosomes
        chromsizes = clr.chromsizes

        rows: List[dict] = []
        bed_files: List[str] = []

        for window in windows:
            row, bed = self._run_window(
                clr, res, window, chromsizes, res_dir, sample_id,
                cooltools, bioframe,
            )
            rows.append(row)
            if bed:
                bed_files.append(bed)

        return rows, bed_files

    def _run_window(
        self,
        clr,
        res: int,
        window: int,
        chromsizes,
        res_dir: Path,
        sample_id: str,
        cooltools,
        bioframe,
    ):
        """Compute insulation for a single (resolution, window) pair."""
        import bioframe as bf

        insulation_tsv = str(res_dir / f"win_{window // 1000}kb_insulation.tsv")
        boundary_bed   = str(res_dir / f"win_{window // 1000}kb_boundaries.bed")

        # Resume-safe
        if (os.path.exists(insulation_tsv) and os.path.getsize(insulation_tsv) > 100 and
                os.path.exists(boundary_bed)):
            logger.debug(f"  res={res} win={window}: cached — skipping")
            return {
                'resolution_bp': res, 'window_bp': window,
                'status': 'cached',
                'insulation_tsv': insulation_tsv,
                'boundary_bed': boundary_bed,
            }, boundary_bed

        t0 = time.time()
        try:
            min_chrom_size = window * 3
            safe_chroms = chromsizes[chromsizes >= min_chrom_size]
            if len(safe_chroms) == 0:
                raise ValueError(f"No chromosomes >= {min_chrom_size} bp")

            view_df = bf.make_viewframe(safe_chroms)

            ins = cooltools.insulation(
                clr,
                window_bp=[window],
                view_df=view_df,
                ignore_diags=self.ignore_diags,
                verbose=False,
            )

            if ins is None or len(ins) == 0:
                raise ValueError("cooltools.insulation returned empty result")

            # Save insulation scores
            ins.to_csv(insulation_tsv, sep='\t', index=False)

            # Extract boundaries and write BED
            boundary_col   = f'is_boundary_{window}'
            insulation_col = f'log2_insulation_score_{window}'
            strength_col   = f'boundary_strength_{window}'

            if boundary_col in ins.columns:
                bounds = ins[ins[boundary_col] == True].copy()
            else:
                bounds = ins.head(0).copy()

            bed_cols = ['chrom', 'start', 'end']
            extra = [c for c in [insulation_col, strength_col] if c in bounds.columns]
            bed_df = bounds[bed_cols + extra].copy()
            bed_df.to_csv(boundary_bed, sep='\t', index=False, header=True)

            n_boundaries = len(bounds)
            n_tads = max(0, n_boundaries - 1)
            mean_ins = ins[insulation_col].mean() if insulation_col in ins.columns else float('nan')

            elapsed = round(time.time() - t0, 2)
            logger.info(
                f"  res={res // 1000}kb  win={window // 1000}kb  "
                f"boundaries={n_boundaries}  TADs={n_tads}  ({elapsed}s)"
            )

            return {
                'resolution_bp':   res,
                'window_bp':       window,
                'n_boundaries':    n_boundaries,
                'n_tads':          n_tads,
                'mean_insulation': round(mean_ins, 4) if not np.isnan(mean_ins) else None,
                'chroms_used':     len(safe_chroms),
                'timing_sec':      elapsed,
                'status':          'success',
                'insulation_tsv':  insulation_tsv,
                'boundary_bed':    boundary_bed,
            }, boundary_bed

        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            err = str(e)[:200]
            logger.warning(f"  res={res} win={window}: FAILED — {err}")
            return {
                'resolution_bp': res,
                'window_bp':     window,
                'timing_sec':    elapsed,
                'status':        f'failed: {err}',
            }, None


# =============================================================================
# A/B Compartment Calling
# =============================================================================

# Resolutions well-suited for compartment calling.  Compartments are
# megabase-scale features; fine resolutions (< 25 kb) are noisy and slow.
DEFAULT_COMPARTMENT_RESOLUTIONS = [25_000, 50_000, 100_000]


class HiCCompartmentCaller:
    """
    A/B chromatin compartment caller using cooltools eigenvector decomposition.

    Uses ``cooltools.eigs_cis`` to compute the first N eigenvectors of the
    observed-over-expected (OE) contact matrix for each chromosome.  The first
    eigenvector (E1) reflects the compartment signal: positive values → A
    compartment (active / euchromatin), negative values → B compartment
    (inactive / heterochromatin).

    .. note::
        Sign of E1 is arbitrary without a phasing track (e.g. gene density or
        GC content).  If a phasing track BED/bigWig is supplied the sign is
        flipped so that A-compartment bins have positive E1.

    Outputs per resolution:
        - ``<res>kb_compartments.tsv``  — per-bin eigenvector table
        - ``<res>kb_A_compartment.bed`` — bins with E1 > 0  (A compartment)
        - ``<res>kb_B_compartment.bed`` — bins with E1 < 0  (B compartment)
        - ``<res>kb_eigvals.tsv``       — eigenvalue table

    Example::

        caller = HiCCompartmentCaller()
        stats = caller.run(
            mcool_file="sample.mcool",
            output_dir="results/compartments",
            sample_id="sample1",
        )
    """

    def __init__(
        self,
        resolutions: Optional[List[int]] = None,
        n_eigs: int = 3,
        phasing_track: Optional[str] = None,
        ignore_diags: Optional[int] = None,
        clip_percentile: float = 99.9,
    ):
        """
        Args:
            resolutions: Resolutions (bp) to call compartments at.
                         Default: [25000, 50000, 100000].
            n_eigs: Number of eigenvectors to compute (default: 3).
                    E1 is the primary compartment signal; E2/E3 can capture
                    sub-compartment structure.
            phasing_track: Path to a BED file (chrom, start, end, value) used
                           to orient E1 sign (e.g. gene density track).
                           If None, sign is left as returned by cooltools.
            ignore_diags: Diagonals to ignore (default: cooltools decides from
                          the cooler's stored metadata).
            clip_percentile: Percentile at which to clip extreme contact values
                             before eigenvector decomposition (default: 99.9).
        """
        self.resolutions = resolutions or DEFAULT_COMPARTMENT_RESOLUTIONS
        self.n_eigs = n_eigs
        self.phasing_track = phasing_track
        self.ignore_diags = ignore_diags
        self.clip_percentile = clip_percentile

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        mcool_file: str,
        output_dir: str,
        sample_id: str,
    ) -> Dict[str, Any]:
        """
        Compute A/B compartment eigenvectors for all configured resolutions.

        Args:
            mcool_file: Path to .mcool (or .cool) file.
            output_dir: Directory where outputs are written.
            sample_id:  Sample identifier used in file names.

        Returns:
            Dict with keys:
              - ``compartment_tsvs``  list of per-bin eigenvector TSV paths
              - ``summary_tsv``       combined summary across resolutions
              - ``resolutions``       resolutions successfully processed
              - ``timing_sec``        wall-clock seconds
        """
        try:
            import cooler
            import cooltools
            import bioframe
        except ImportError as exc:
            raise RuntimeError(
                f"Missing dependency for compartment calling: {exc}. "
                "Install with: conda install -c bioconda cooltools cooler bioframe"
            ) from exc

        t0 = time.time()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 70)
        logger.info("STEP 7: A/B COMPARTMENT CALLING (eigs_cis)")
        logger.info("=" * 70)
        logger.info(f"  mcool        : {mcool_file}")
        logger.info(f"  output       : {output_dir}")
        logger.info(f"  sample       : {sample_id}")
        logger.info(f"  n_eigs       : {self.n_eigs}")
        logger.info(f"  phasing_track: {self.phasing_track or 'None (sign unoriented)'}")

        avail_res = self._list_resolutions(mcool_file)
        use_res = [r for r in self.resolutions if r in avail_res]
        skipped = [r for r in self.resolutions if r not in avail_res]
        if skipped:
            logger.warning(f"  Resolutions not in mcool (skipped): {skipped}")
        logger.info(f"  Resolutions  : {use_res}")

        # Load phasing track once
        phasing_df = self._load_phasing_track(self.phasing_track)

        all_rows: List[dict] = []
        compartment_tsvs: List[str] = []
        processed_res: List[int] = []

        for res in use_res:
            row, tsv = self._call_compartments_at_resolution(
                mcool_file, res, output_dir, sample_id, phasing_df,
                cooler=cooler, cooltools=cooltools, bioframe=bioframe,
            )
            all_rows.append(row)
            if tsv:
                compartment_tsvs.append(tsv)
                processed_res.append(res)

        summary_df = pd.DataFrame(all_rows)
        summary_tsv = str(output_dir / f"{sample_id}_compartment_summary.tsv")
        summary_df.to_csv(summary_tsv, sep='\t', index=False)

        elapsed = round(time.time() - t0, 2)
        logger.info(f"  Done — {len(processed_res)} resolutions completed  ({elapsed}s)")
        logger.info(f"  Summary : {summary_tsv}")

        return {
            'compartment_tsvs': compartment_tsvs,
            'summary_tsv':      summary_tsv,
            'resolutions':      processed_res,
            'timing_sec':       elapsed,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _list_resolutions(self, mcool_file: str) -> List[int]:
        import cooler
        try:
            paths = cooler.fileops.list_coolers(mcool_file)
            res = sorted(
                int(p.split('/')[-1])
                for p in paths
                if p.startswith('/resolutions/')
            )
            if res:
                return res
        except Exception:
            pass
        try:
            c = cooler.Cooler(mcool_file)
            return [c.binsize]
        except Exception:
            return []

    def _cooler_uri(self, mcool_file: str, res: int) -> str:
        import cooler
        try:
            paths = cooler.fileops.list_coolers(mcool_file)
            if any(p.startswith('/resolutions/') for p in paths):
                return f"{mcool_file}::/resolutions/{res}"
        except Exception:
            pass
        return mcool_file

    def _load_phasing_track(self, path: Optional[str]) -> Optional[pd.DataFrame]:
        """Load a phasing track BED (chrom, start, end, value) if provided."""
        if not path:
            return None
        try:
            df = pd.read_csv(path, sep='\t', header=None,
                             names=['chrom', 'start', 'end', 'value'])
            logger.info(f"  Loaded phasing track: {path}  ({len(df)} bins)")
            return df
        except Exception as e:
            logger.warning(f"  Could not load phasing track {path}: {e} — proceeding without")
            return None

    def _call_compartments_at_resolution(
        self,
        mcool_file: str,
        res: int,
        output_dir: Path,
        sample_id: str,
        phasing_df: Optional[pd.DataFrame],
        cooler, cooltools, bioframe,
    ):
        """Run eigs_cis compartment calling at one resolution."""
        eig_tsv    = str(output_dir / f"{sample_id}_res{res // 1000}kb_compartments.tsv")
        eigval_tsv = str(output_dir / f"{sample_id}_res{res // 1000}kb_eigvals.tsv")
        a_bed      = str(output_dir / f"{sample_id}_res{res // 1000}kb_A_compartment.bed")
        b_bed      = str(output_dir / f"{sample_id}_res{res // 1000}kb_B_compartment.bed")

        # Resume-safe
        if os.path.exists(eig_tsv) and os.path.getsize(eig_tsv) > 100:
            logger.debug(f"  res={res}: compartments cached — skipping")
            return {'resolution_bp': res, 'status': 'cached', 'eig_tsv': eig_tsv}, eig_tsv

        t0 = time.time()
        try:
            uri = self._cooler_uri(mcool_file, res)
            clr = cooler.Cooler(uri)

            # Build view — exclude tiny chromosomes (< 3 bins)
            chromsizes = clr.chromsizes
            safe_chroms = chromsizes[chromsizes >= res * 3]
            if len(safe_chroms) == 0:
                raise ValueError(f"No chromosomes with >= 3 bins at {res}bp resolution")
            view_df = bioframe.make_viewframe(safe_chroms)

            # Build per-chromosome phasing track aligned to cooler bins
            phasing_track = None
            if phasing_df is not None:
                phasing_track = self._align_phasing_track(clr, phasing_df, view_df)

            # Keyword args for eigs_cis
            kwargs: Dict[str, Any] = {
                'n_eigs':          self.n_eigs,
                'view_df':         view_df,
                'clr_weight_name': 'weight',
                'clip_percentile': self.clip_percentile,
            }
            if self.ignore_diags is not None:
                kwargs['ignore_diags'] = self.ignore_diags
            if phasing_track is not None:
                kwargs['phasing_track'] = phasing_track

            eigvals, eigvecs = cooltools.eigs_cis(clr, **kwargs)

            # eigvecs: DataFrame with columns [chrom, start, end, E1, E2, ...]
            # eigvals: DataFrame with columns [chrom, eig, val]

            eigvecs.to_csv(eig_tsv, sep='\t', index=False)
            eigvals.to_csv(eigval_tsv, sep='\t', index=False)

            # Write A (E1 > 0) and B (E1 < 0) compartment BEDs
            e1_col = 'E1' if 'E1' in eigvecs.columns else eigvecs.columns[3]
            valid = eigvecs[eigvecs[e1_col].notna()].copy()

            a_bins = valid[valid[e1_col] > 0][['chrom', 'start', 'end', e1_col]]
            b_bins = valid[valid[e1_col] < 0][['chrom', 'start', 'end', e1_col]]
            a_bins.to_csv(a_bed, sep='\t', index=False, header=True)
            b_bins.to_csv(b_bed, sep='\t', index=False, header=True)

            n_a = len(a_bins)
            n_b = len(b_bins)
            n_nan = int(eigvecs[e1_col].isna().sum())

            elapsed = round(time.time() - t0, 2)
            logger.info(
                f"  res={res // 1000}kb  A-bins={n_a}  B-bins={n_b}  "
                f"unassigned={n_nan}  ({elapsed}s)"
            )

            return {
                'resolution_bp': res,
                'n_a_bins':      n_a,
                'n_b_bins':      n_b,
                'n_unassigned':  n_nan,
                'timing_sec':    elapsed,
                'status':        'success',
                'eig_tsv':       eig_tsv,
                'eigval_tsv':    eigval_tsv,
                'a_bed':         a_bed,
                'b_bed':         b_bed,
            }, eig_tsv

        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            err = str(e)[:200]
            logger.warning(f"  res={res // 1000}kb: compartment calling FAILED — {err}")
            return {
                'resolution_bp': res,
                'timing_sec':    elapsed,
                'status':        f'failed: {err}',
            }, None

    def _align_phasing_track(
        self,
        clr,
        phasing_df: pd.DataFrame,
        view_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Aggregate the phasing track (e.g. gene density) into cooler bins.

        Computes the mean phasing value per cooler bin using overlap.
        Returns a DataFrame with columns [chrom, start, end, value] aligned
        to the cooler's bin table.
        """
        try:
            import bioframe as bf
            bins = clr.bins()[:][['chrom', 'start', 'end']]

            # Filter bins to chroms in view
            view_chroms = set(view_df['chrom'])
            bins = bins[bins['chrom'].isin(view_chroms)].copy()
            phasing_df = phasing_df[phasing_df['chrom'].isin(view_chroms)].copy()

            # Overlap-based mean using bioframe
            overlapped = bf.overlap(bins, phasing_df, suffixes=('', '_p'))
            if 'value_p' not in overlapped.columns:
                raise ValueError("Overlap produced no 'value_p' column")

            agg = (
                overlapped
                .groupby(['chrom', 'start', 'end'], sort=False)['value_p']
                .mean()
                .reset_index()
                .rename(columns={'value_p': 'value'})
            )
            # Merge back to preserve bin order and fill gaps with NaN
            result = bins.merge(agg, on=['chrom', 'start', 'end'], how='left')
            return result[['chrom', 'start', 'end', 'value']]

        except Exception as e:
            logger.warning(f"  Phasing track alignment failed ({e}); proceeding without")
            return None