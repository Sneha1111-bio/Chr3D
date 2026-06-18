# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
# This software was developed with support from the National Science Foundation under CAREER Award DBI-2239350.
"""
Parameter sweep driver for gnn_clustering.py.

Runs gnn_clustering on a single feature matrix while varying one parameter at a
time around a baseline (pca-dim=50, k-graph=20, n-clusters=5):

    --pca-dim   : 10, 20, 30, 50, 75, 100
    --k-graph   : 5, 10, 15, 20, 25, 30, 35
    --n-clusters: 4, 5, 6

Each run writes its own output sub-directory (the usual gnn_clustering outputs).
After every run the metrics (NMI, ARI, silhouette) and the configuration are
read back from that run's ``gnn_clustering_results.csv`` and appended to a single
summary CSV (default: ``<output-dir>/pca_sweep_summary.csv``).

NMI and ARI are only produced by gnn_clustering when labels are supplied, so pass
``--labels`` / ``--label_pkl`` through if you want supervised metrics; otherwise
those columns are left empty.

Usage:
    python -m chr3d.hic.clustering.pca_sweep \
        --data matrix.csv --output-dir sweep_results/

    python -m chr3d.hic.clustering.pca_sweep \
        --data matrix.csv --output-dir sweep_results/ --labels labels.csv

    # forward extra args straight to gnn_clustering (after a literal --):
    python -m chr3d.hic.clustering.pca_sweep \
        --data matrix.csv --output-dir sweep_results/ -- --epochs 50
"""

import argparse
import math
import os
import subprocess
import sys

import pandas as pd

# Baseline configuration that every sweep varies around.
BASELINE_PCA_DIM = 50
BASELINE_K_GRAPH = 20
BASELINE_N_CLUSTERS = 5

# Values swept, one parameter at a time.
PCA_DIM_VALUES = [10, 20, 30, 50, 75, 100]
K_GRAPH_VALUES = [5, 10, 15, 20, 25, 30, 35]
N_CLUSTERS_VALUES = [4, 5, 6]

GNN_MODULE = 'chr3d.hic.clustering.gnn_clustering'
RESULTS_FILENAME = 'gnn_clustering_results.csv'


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--data', required=True, metavar='CSV',
                   help='Cell × bin feature matrix CSV (passed to gnn_clustering)')
    p.add_argument('--output-dir', required=True, metavar='DIR',
                   help='Base directory; each run gets its own sub-directory here')
    p.add_argument('--labels', default=None, metavar='CSV',
                   help='Optional CSV [cell_id, label] forwarded to gnn_clustering '
                        '(needed for NMI/ARI)')
    p.add_argument('--label_pkl', default=None, metavar='PKL',
                   help='Optional Higashi-style label pickle forwarded to gnn_clustering')
    p.add_argument('--seed', type=int, default=0, metavar='INT',
                   help='Seed forwarded to every run (default: 0)')
    p.add_argument('--summary-csv', default=None, metavar='CSV',
                   help='Where to write the combined summary '
                        '(default: <output-dir>/pca_sweep_summary.csv)')
    p.add_argument('--python', default=sys.executable, metavar='EXE',
                   help='Python interpreter used to launch gnn_clustering '
                        '(default: current interpreter)')
    p.add_argument('--dry-run', action='store_true',
                   help='Print the runs that would execute, then exit')
    p.add_argument('extra', nargs=argparse.REMAINDER,
                   help='Extra args forwarded verbatim to gnn_clustering '
                        '(everything after a literal --)')
    return p.parse_args()


def build_run_plan():
    """Return ordered list of unique runs as dicts.

    Each run is varied one parameter at a time around the baseline.  The baseline
    point is shared by all three sweeps, so it is emitted once and its
    ``sweep`` field records every group it belongs to.
    """
    plan = {}  # (pca_dim, k_graph, n_clusters) -> sweep tags

    def add(pca_dim, k_graph, n_clusters, tag):
        key = (pca_dim, k_graph, n_clusters)
        plan.setdefault(key, [])
        if tag not in plan[key]:
            plan[key].append(tag)

    for v in PCA_DIM_VALUES:
        add(v, BASELINE_K_GRAPH, BASELINE_N_CLUSTERS, 'pca_dim')
    for v in K_GRAPH_VALUES:
        add(BASELINE_PCA_DIM, v, BASELINE_N_CLUSTERS, 'k_graph')
    for v in N_CLUSTERS_VALUES:
        add(BASELINE_PCA_DIM, BASELINE_K_GRAPH, v, 'n_clusters')

    runs = []
    for (pca_dim, k_graph, n_clusters), tags in plan.items():
        runs.append({
            'sweep': '+'.join(tags),
            'pca_dim': pca_dim,
            'k_graph': k_graph,
            'n_clusters': n_clusters,
        })
    return runs


def run_label(run):
    return f"pcadim{run['pca_dim']}_kgraph{run['k_graph']}_nclust{run['n_clusters']}"


def build_command(python_exe, run, args, run_dir):
    cmd = [
        python_exe, '-m', GNN_MODULE,
        '--data', args.data,
        '--output-dir', run_dir,
        '--pca-dim', str(run['pca_dim']),
        '--k-graph', str(run['k_graph']),
        '--n-clusters', str(run['n_clusters']),
        '--seed', str(args.seed),
    ]
    if args.labels:
        cmd += ['--labels', args.labels]
    if args.label_pkl:
        cmd += ['--label_pkl', args.label_pkl]
    # argparse.REMAINDER keeps a leading '--'; drop it before forwarding.
    extra = list(args.extra)
    if extra and extra[0] == '--':
        extra = extra[1:]
    cmd += extra
    return cmd


def read_metrics(run_dir):
    """Read NMI/ARI/silhouette/config from a finished run's results CSV."""
    metrics = {'silhouette': math.nan, 'nmi': math.nan, 'ari': math.nan,
               'n_clusters_found': math.nan, 'best_config': ''}
    results_path = os.path.join(run_dir, RESULTS_FILENAME)
    if not os.path.exists(results_path):
        return metrics
    df = pd.read_csv(results_path)
    if df.empty:
        return metrics
    row = df.iloc[0]
    if 'silhouette' in df.columns:
        metrics['silhouette'] = row['silhouette']
    if 'nmi' in df.columns:
        metrics['nmi'] = row['nmi']
    if 'ari' in df.columns:
        metrics['ari'] = row['ari']
    if 'n_clusters' in df.columns:
        metrics['n_clusters_found'] = row['n_clusters']
    if 'config' in df.columns:
        metrics['best_config'] = row['config']
    return metrics


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    summary_csv = args.summary_csv or os.path.join(args.output_dir,
                                                   'pca_sweep_summary.csv')

    runs = build_run_plan()

    print('=' * 70)
    print('CHR3D  —  PCA / GNN PARAMETER SWEEP')
    print('=' * 70)
    print(f'  Data        : {args.data}')
    print(f'  Output dir  : {args.output_dir}')
    print(f'  Labels      : {args.labels or args.label_pkl or "none (no NMI/ARI)"}')
    print(f'  Baseline    : pca-dim={BASELINE_PCA_DIM}, '
          f'k-graph={BASELINE_K_GRAPH}, n-clusters={BASELINE_N_CLUSTERS}')
    print(f'  Total runs  : {len(runs)}')
    print(f'  Summary CSV : {summary_csv}')
    print('=' * 70)

    if args.dry_run:
        for i, run in enumerate(runs, 1):
            run_dir = os.path.join(args.output_dir, run_label(run))
            cmd = build_command(args.python, run, args, run_dir)
            print(f'[{i}/{len(runs)}] ({run["sweep"]}) {" ".join(cmd)}')
        return

    summary_rows = []
    for i, run in enumerate(runs, 1):
        run_dir = os.path.join(args.output_dir, run_label(run))
        os.makedirs(run_dir, exist_ok=True)
        cmd = build_command(args.python, run, args, run_dir)

        print(f'\n[{i}/{len(runs)}] sweep={run["sweep"]}  '
              f'pca-dim={run["pca_dim"]}  k-graph={run["k_graph"]}  '
              f'n-clusters={run["n_clusters"]}')
        print(f'  $ {" ".join(cmd)}')

        proc = subprocess.run(cmd)
        status = 'ok' if proc.returncode == 0 else f'failed(rc={proc.returncode})'
        if proc.returncode != 0:
            print(f'  WARNING: run returned non-zero exit code {proc.returncode}')

        metrics = read_metrics(run_dir)
        if status == 'ok' and not os.path.exists(
                os.path.join(run_dir, RESULTS_FILENAME)):
            status = 'no_results_csv'

        summary_rows.append({
            'sweep_param':      run['sweep'],
            'pca_dim':          run['pca_dim'],
            'k_graph':          run['k_graph'],
            'n_clusters_target': run['n_clusters'],
            'seed':             args.seed,
            'nmi':              metrics['nmi'],
            'ari':              metrics['ari'],
            'silhouette':       metrics['silhouette'],
            'n_clusters_found': metrics['n_clusters_found'],
            'best_config':      metrics['best_config'],
            'status':           status,
            'output_subdir':    run_dir,
        })

        # Write after every run so partial progress is never lost.
        pd.DataFrame(summary_rows).to_csv(summary_csv, index=False)
        print(f'  -> nmi={metrics["nmi"]}  ari={metrics["ari"]}  '
              f'silhouette={metrics["silhouette"]}  status={status}')

    print('\n' + '=' * 70)
    print(f'Sweep complete — {len(summary_rows)} runs')
    print(f'Summary written to: {summary_csv}')
    print('=' * 70)


if __name__ == '__main__':
    main()
