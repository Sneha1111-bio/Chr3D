"""Hi-C Loop Calling Module - Chromatin loop calling using cooltools."""

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


# ------------------------------------------------------------------
# Pandas 3.0 compatibility patch for cooltools 0.7.1
# ------------------------------------------------------------------
# cooltools 0.7.1's ``determine_thresholds`` calls ``DataFrame.idxmin()``
# on masked FDR differences.  When no pixels pass the FDR threshold the
# result is all-NaN.  In pandas < 3.0 ``idxmin()`` returns NaN (which
# ``fillna()`` then handles); in pandas >= 3.0 it raises ValueError.
# We monkey-patch the function so that loop calling works with newer
# pandas.
# ------------------------------------------------------------------


def _patch_cooltools_for_pandas3():
    """Apply pandas >= 3.0 compatibility patch to cooltools.dotfinder."""
    try:
        from cooltools.api import dotfinder as _df
        from scipy.stats import poisson
    except ImportError:
        return

    if hasattr(_df, '_chr3d_patched'):
        return

    def _patched_determine_thresholds(gw_hist, fdr):
        """Patched determine_thresholds for pandas >= 3.0 compatibility."""
        qvalues = {}
        threshold_df = {}
        for k, _hist in gw_hist.items():
            rcs_hist = _hist.iloc[::-1].cumsum(axis=0).iloc[::-1]
            norm = rcs_hist.iloc[0, :]
            unit_Poisson = pd.DataFrame().reindex_like(rcs_hist)
            for lbin in rcs_hist.columns:
                _occurances = rcs_hist.index.to_numpy()
                unit_Poisson[lbin] = poisson.sf(_occurances, lbin.right)
            unit_Poisson = norm * unit_Poisson

            _high_value = rcs_hist.index.max() + 1
            fdr_diff = ((fdr * rcs_hist) - unit_Poisson).cummax()
            masked = fdr_diff.mask(fdr_diff < 0)

            try:
                result = masked.idxmin()
            except ValueError:
                result = pd.Series(
                    _high_value, index=masked.columns, dtype=np.int64
                )
            else:
                result = result.fillna(_high_value).astype(np.int64)

            threshold_df[k] = result
            threshold_df[k].index = pd.IntervalIndex(threshold_df[k].index)

            qvalues[k] = (unit_Poisson / rcs_hist).cummin()
            qvalues[k] = qvalues[k].mask(qvalues[k] > 1.0, 1.0)

        return threshold_df, qvalues

    _df.determine_thresholds = _patched_determine_thresholds
    _df._chr3d_patched = True
    logger.debug("Patched cooltools.dotfinder.determine_thresholds for pandas >= 3.0")


_patch_cooltools_for_pandas3()


DEFAULT_LOOP_RESOLUTIONS = [5_000, 10_000, 25_000]


class HiCLoopCaller:
    """Hi-C chromatin loop caller using cooltools."""

    def __init__(
        self,
        resolutions: Optional[List[int]] = None,
        fdr: float = 0.1,
        min_dist: int = 5_000,
        max_dist: int = 10_000_000,
        threads: int = 8,
        ignore_diags: int = 2,
        genome: Optional[str] = "hg38",
        clustering_radius: Optional[int] = 10_000,
        cluster_filtering: bool = True,
    ):
        """Initialize loop caller."""
        self.resolutions = resolutions or DEFAULT_LOOP_RESOLUTIONS
        self.fdr = fdr
        self.min_dist = min_dist
        self.max_dist = max_dist
        self.threads = threads
        self.ignore_diags = ignore_diags
        self.genome = genome
        self.clustering_radius = clustering_radius
        self.cluster_filtering = cluster_filtering

    def run(
        self,
        mcool_file: str,
        output_dir: str,
        sample_id: str,
    ) -> Dict[str, Any]:
        """Call loops on all configured resolutions present in mcool_file."""
        try:
            import cooler
            import cooltools
            import bioframe
        except ImportError as exc:
            raise RuntimeError(
                f"Missing dependency for loop calling: {exc}. "
                "Install with: conda install -c bioconda cooltools cooler bioframe"
            ) from exc

        _patch_cooltools_for_pandas3()

        t0 = time.time()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 70)
        logger.info("STEP 6: LOOP CALLING (cooltools dots)")
        logger.info("=" * 70)
        logger.info(f"  mcool      : {mcool_file}")
        logger.info(f"  output     : {output_dir}")
        logger.info(f"  sample     : {sample_id}")
        logger.info(f"  FDR        : {self.fdr}")
        logger.info(f"  dist range : {self.min_dist} - {self.max_dist} bp")

        avail_res = self._list_resolutions(mcool_file)
        use_res = [r for r in self.resolutions if r in avail_res]
        skipped = [r for r in self.resolutions if r not in avail_res]
        if skipped:
            logger.warning(f"  Resolutions not in mcool (skipped): {skipped}")
        logger.info(f"  Resolutions: {use_res}")

        all_rows: List[dict] = []
        loop_bedpes: List[str] = []
        n_loops: Dict[int, int] = {}
        processed_res: List[int] = []

        for res in use_res:
            row, bedpe = self._call_loops_at_resolution(
                mcool_file, res, output_dir, sample_id,
                cooler=cooler, cooltools=cooltools, bioframe=bioframe,
            )
            all_rows.append(row)
            if bedpe:
                loop_bedpes.append(bedpe)
                n_loops[res] = row.get('n_loops', 0)
                processed_res.append(res)

        summary_df = pd.DataFrame(all_rows)
        summary_tsv = str(output_dir / f"{sample_id}_loop_summary.tsv")
        summary_df.to_csv(summary_tsv, sep='\t', index=False)

        elapsed = round(time.time() - t0, 2)
        total_loops = sum(n_loops.values())
        logger.info(f"  Done — {total_loops} total loops across {len(processed_res)} resolutions  ({elapsed}s)")
        logger.info(f"  Summary : {summary_tsv}")

        return {
            'loop_bedpes':  loop_bedpes,
            'summary_tsv':  summary_tsv,
            'n_loops':      n_loops,
            'resolutions':  processed_res,
            'timing_sec':   elapsed,
        }

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

    def _call_loops_at_resolution(
        self,
        mcool_file: str,
        res: int,
        output_dir: Path,
        sample_id: str,
        cooler, cooltools, bioframe,
    ):
        """Compute expected contacts and call dots/loops at one resolution."""
        bedpe_file = str(output_dir / f"{sample_id}_res{res // 1000}kb_loops.bedpe")
        tsv_file   = str(output_dir / f"{sample_id}_res{res // 1000}kb_loops.tsv")

        if os.path.exists(bedpe_file) and os.path.getsize(bedpe_file) > 50:
            logger.debug(f"  res={res}: cached — skipping")
            try:
                n = sum(1 for _ in open(bedpe_file)) - 1
            except Exception:
                n = 0
            return {'resolution_bp': res, 'n_loops': n, 'status': 'cached',
                    'bedpe': bedpe_file}, bedpe_file

        t0 = time.time()
        try:
            uri = self._cooler_uri(mcool_file, res)
            clr = cooler.Cooler(uri)

            if self.genome is not None:
                chromsizes = bioframe.fetch_chromsizes(self.genome)
                cens = bioframe.fetch_centromeres(self.genome)
                arms = bioframe.make_chromarms(chromsizes, cens)
                std_chroms = [
                    c for c in clr.chromnames
                    if c.startswith('chr') and c.lstrip('chr') in
                    {str(i) for i in range(1, 23)} | {'X', 'Y'}
                ]
                arms = arms[arms['chrom'].isin(std_chroms)].copy()
            else:
                cs = clr.chromsizes
                std = cs[
                    cs.index.str.match(r'^chr[0-9XY]+$')
                    & (cs >= self.min_dist * 10)
                ]
                arms = bioframe.make_viewframe(std)

            if len(arms) == 0:
                raise ValueError("No chromosomes large enough for loop calling")

            chrom_order = {c: i for i, c in enumerate(clr.chromnames)}
            arms['_sort'] = arms['chrom'].map(chrom_order)
            arms = arms.sort_values(['_sort', 'start']).drop(
                columns=['_sort']
            ).reset_index(drop=True)

            view_df = arms

            expected = cooltools.expected_cis(
                clr,
                view_df=view_df,
                ignore_diags=self.ignore_diags,
                nproc=self.threads,
            )

            dots = cooltools.dots(
                clr,
                expected=expected,
                view_df=view_df,
                max_loci_separation=self.max_dist,
                clustering_radius=self.clustering_radius,
                cluster_filtering=self.cluster_filtering
                    if self.clustering_radius is not None else None,
                nproc=self.threads,
            )

            if dots is None or len(dots) == 0:
                logger.info(f"  res={res // 1000}kb: 0 loops found")
                pd.DataFrame(columns=['chrom1', 'start1', 'end1', 'chrom2', 'start2', 'end2']
                             ).to_csv(bedpe_file, sep='\t', index=False)
                dots_df = pd.DataFrame()
                dots_df.to_csv(tsv_file, sep='\t', index=False)
                elapsed = round(time.time() - t0, 2)
                return {'resolution_bp': res, 'n_loops': 0, 'status': 'success',
                        'bedpe': bedpe_file, 'timing_sec': elapsed}, bedpe_file

            if 'dist' in dots.columns:
                dots = dots[
                    (dots['dist'] >= self.min_dist // res) &
                    (dots['dist'] <= self.max_dist // res)
                ].copy()

            fdr_col = next((c for c in ['fdr', 'FDR', 'q_value', 'pvalue'] if c in dots.columns), None)
            if fdr_col:
                dots = dots[dots[fdr_col] <= self.fdr].copy()

            dots.to_csv(tsv_file, sep='\t', index=False)

            bedpe_cols = []
            for pair in [('chrom1', 'start1', 'end1'), ('chrom2', 'start2', 'end2')]:
                for c in pair:
                    if c in dots.columns:
                        bedpe_cols.append(c)
            if len(bedpe_cols) == 6:
                score_col = next((c for c in ['score', 'la_exp.donut.value', 'count'] if c in dots.columns), None)
                if score_col:
                    bedpe_cols.append(score_col)
                dots[bedpe_cols].to_csv(bedpe_file, sep='\t', index=False)
            else:
                dots.to_csv(bedpe_file, sep='\t', index=False)

            n_loops = len(dots)
            elapsed = round(time.time() - t0, 2)
            logger.info(f"  res={res // 1000}kb  loops={n_loops}  ({elapsed}s)")

            return {
                'resolution_bp': res,
                'n_loops':       n_loops,
                'timing_sec':    elapsed,
                'status':        'success',
                'bedpe':         bedpe_file,
            }, bedpe_file

        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            err = str(e)[:200]
            logger.warning(f"  res={res // 1000}kb: loop calling FAILED — {err}")
            return {
                'resolution_bp': res,
                'timing_sec':    elapsed,
                'status':        f'failed: {err}',
            }, None
