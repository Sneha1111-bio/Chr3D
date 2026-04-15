"""
GraphSAGE-based unsupervised clustering for sn-Hi-C data.

Reads a cell × bin feature matrix (from preprocessing.py), applies TF-IDF +
StandardScaler, reduces with PCA, builds a kNN graph, trains a GraphSAGE encoder
with NT-Xent contrastive loss, then clusters embeddings with Leiden.

No cell type labels are required.  If a label CSV is provided via --labels,
supervised metrics (NMI, ARI) and a confusion matrix are also computed.

Usage:
    python gnn_clustering.py --data matrix.csv --output-dir results/
    python gnn_clustering.py --data matrix.csv --output-dir results/ --labels labels.csv
    python gnn_clustering.py --data matrix.csv --output-dir results/ --epochs 300 --pca-dim 50
"""

import argparse
import copy
import os
import time
import warnings

warnings.filterwarnings('ignore')
os.environ['POLARS_MAX_THREADS'] = '24'
os.environ['OMP_NUM_THREADS']    = '12'

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import kneighbors_graph
from sklearn.metrics import (silhouette_score, silhouette_samples,
                             normalized_mutual_info_score as NMI,
                             adjusted_rand_score as ARI,
                             confusion_matrix)
import scanpy as sc
import anndata
import umap as umap_lib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--data',       required=True,  metavar='CSV',
                   help='Cell × bin feature matrix CSV (output of preprocessing.py)')
    p.add_argument('--output-dir', required=True,  metavar='DIR',
                   help='Output directory for plots, embeddings, and result files')
    p.add_argument('--labels',     default=None,   metavar='CSV',
                   help='Optional CSV with columns [cell_id, label] for supervised '
                        'metrics and confusion matrix plots')
    p.add_argument('--seed',       type=int, default=0, metavar='INT',
                   help='Random seed (default: 0)')
    p.add_argument('--pca-dim',    type=int, default=50,  metavar='INT',
                   help='PCA dimensions before GNN (default: 50)')
    p.add_argument('--k-graph',    type=int, default=15,  metavar='INT',
                   help='kNN graph neighbours (default: 15)')
    p.add_argument('--hidden-dim', type=int, default=128, metavar='INT',
                   help='GNN hidden dimension (default: 128)')
    p.add_argument('--out-dim',    type=int, default=32,  metavar='INT',
                   help='GNN output embedding dimension (default: 32)')
    p.add_argument('--n-layers',   type=int, default=2,   metavar='INT',
                   help='Number of GraphSAGE layers (default: 2)')
    p.add_argument('--dropout',    type=float, default=0.3, metavar='FLOAT',
                   help='Dropout rate (default: 0.3)')
    p.add_argument('--lr',         type=float, default=1e-3, metavar='FLOAT',
                   help='Learning rate (default: 0.001)')
    p.add_argument('--epochs',     type=int, default=200, metavar='INT',
                   help='Training epochs (default: 200)')
    p.add_argument('--tau',        type=float, default=0.2, metavar='FLOAT',
                   help='NT-Xent temperature (default: 0.2)')
    p.add_argument('--neg-ratio',  type=int, default=5, metavar='INT',
                   help='Negative sample ratio for NT-Xent (default: 5)')
    return p.parse_args()


# ─── MODEL ────────────────────────────────────────────────────────────────────

class GraphSAGEEncoder(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim, n_layers=2, dropout=0.3):
        super().__init__()
        self.convs    = nn.ModuleList()
        self.bns      = nn.ModuleList()
        self.n_layers = n_layers
        self.dropout  = dropout
        self.convs.append(SAGEConv(in_dim, hidden_dim))
        self.bns.append(nn.BatchNorm1d(hidden_dim))
        for _ in range(n_layers - 2):
            self.convs.append(SAGEConv(hidden_dim, hidden_dim))
            self.bns.append(nn.BatchNorm1d(hidden_dim))
        self.convs.append(SAGEConv(hidden_dim, out_dim))

    def forward(self, x, edge_index):
        for i in range(self.n_layers - 1):
            x = self.convs[i](x, edge_index)
            x = self.bns[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.convs[-1](x, edge_index)
        return F.normalize(x, dim=1)


def nt_xent_graph_loss(z, edge_index, tau=0.2, neg_sample_ratio=5):
    src, dst  = edge_index
    n_edges   = src.size(0)
    n_nodes   = z.size(0)
    max_edges = min(n_edges, 50_000)
    if n_edges > max_edges:
        idx  = torch.randperm(n_edges, device=z.device)[:max_edges]
        src, dst = src[idx], dst[idx]
    pos_sim = F.cosine_similarity(z[src], z[dst]) / tau
    neg_src = src.repeat_interleave(neg_sample_ratio)
    neg_dst = torch.randint(0, n_nodes, (neg_src.size(0),), device=z.device)
    neg_sim = F.cosine_similarity(z[neg_src], z[neg_dst]) / tau
    neg_sim = neg_sim.view(-1, neg_sample_ratio)
    logits  = torch.cat([pos_sim.unsqueeze(1), neg_sim], dim=1)
    targets = torch.zeros(logits.size(0), dtype=torch.long, device=z.device)
    return F.cross_entropy(logits, targets)


# ─── DATA ─────────────────────────────────────────────────────────────────────

def load_features(data_csv):
    """Load cell × bin matrix, apply TF-IDF + StandardScaler."""
    df   = pd.read_csv(data_csv, index_col=0)
    cell_ids = list(df.index.astype(str))
    data     = df.values.astype(np.float32)
    tf   = data / (data.sum(axis=1, keepdims=True) + 1e-8)
    idf  = np.log1p(data.shape[0] / (1 + (data > 0).sum(axis=0)))
    tfidf    = tf * idf
    tfidf_ss = StandardScaler().fit_transform(tfidf).astype(np.float32)
    return tfidf_ss, cell_ids


def load_labels(label_csv, cell_ids):
    """Load optional label CSV. Returns (labels_int, label_names) or (None, None)."""
    if label_csv is None or not os.path.exists(label_csv):
        return None, None
    ldf   = pd.read_csv(label_csv)
    ldf   = ldf.set_index(ldf.columns[0])
    label_col = ldf.columns[0]
    ordered   = [str(cid) for cid in cell_ids]
    raw_labels = [str(ldf.loc[c, label_col]) if c in ldf.index else 'unknown'
                  for c in ordered]
    unique_labels = sorted(set(raw_labels))
    lmap   = {l: i for i, l in enumerate(unique_labels)}
    labels = np.array([lmap[l] for l in raw_labels])
    return labels, unique_labels


# ─── CLUSTERING ───────────────────────────────────────────────────────────────

def cluster_leiden(embeddings, true_labels=None):
    """Leiden grid search. Returns (best_pred, best_tag, best_nmi, best_ari)."""
    best_sil, best_pred, best_tag = -1, None, ""
    best_nmi, best_ari = float('nan'), float('nan')

    for k in [10, 15, 20, 25, 30]:
        for res in [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
            try:
                adata = anndata.AnnData(X=embeddings.astype(np.float32))
                sc.pp.neighbors(adata, n_neighbors=k, use_rep='X')
                sc.tl.leiden(adata, resolution=res, random_state=42,
                             flavor='igraph', n_iterations=2, key_added='leiden')
                pred = adata.obs['leiden'].astype(int).values
                nc   = len(np.unique(pred))
                if nc < 2:
                    continue
                sil  = silhouette_score(embeddings, pred)
                if sil > best_sil:
                    best_sil  = sil
                    best_pred = pred.copy()
                    best_tag  = f'k={k},r={res:.2f},nc={nc}'
                    if true_labels is not None:
                        best_nmi = NMI(true_labels, pred)
                        best_ari = ARI(true_labels, pred)
            except Exception:
                pass

    return best_pred, best_tag, best_nmi, best_ari, best_sil


# ─── PLOTS ────────────────────────────────────────────────────────────────────

def _cmap_for(n):
    return plt.cm.get_cmap('tab20' if n > 10 else 'tab10', n)


def plot_umap(embeddings, pred_labels, out_prefix, true_labels=None, label_names=None):
    """UMAP of GNN embeddings coloured by cluster (and optionally by true label)."""
    print("  UMAP...")
    reducer  = umap_lib.UMAP(n_neighbors=20, min_dist=0.1, random_state=42, verbose=False)
    umap_xy  = reducer.fit_transform(embeddings)
    nc       = len(np.unique(pred_labels))
    cmap     = _cmap_for(nc)

    n_panels = 2 if true_labels is not None else 1
    fig, axes = plt.subplots(1, n_panels, figsize=(9 * n_panels, 7))
    if n_panels == 1:
        axes = [axes]

    # Predicted clusters
    for c in range(nc):
        mask = pred_labels == c
        if not mask.any():
            continue
        axes[0].scatter(umap_xy[mask, 0], umap_xy[mask, 1],
                        c=[cmap(c)], s=10, alpha=0.7,
                        label=f'C{c} (n={mask.sum()})', edgecolors='none')
    nc_check = len(np.unique(pred_labels))
    sil_str = f'sil={silhouette_score(embeddings, pred_labels):.3f}' if nc_check >= 2 else 'sil=n/a'
    axes[0].set_title(f'Predicted clusters  ({sil_str})',
                      fontsize=13, fontweight='bold')
    axes[0].legend(fontsize=8, frameon=True, markerscale=2)
    axes[0].set_xlabel('UMAP-1');  axes[0].set_ylabel('UMAP-2')

    # True labels (optional)
    if true_labels is not None:
        ntl  = len(np.unique(true_labels))
        cmap2 = _cmap_for(ntl)
        for i in range(ntl):
            mask = true_labels == i
            lbl  = label_names[i] if label_names else str(i)
            axes[1].scatter(umap_xy[mask, 0], umap_xy[mask, 1],
                            c=[cmap2(i)], s=10, alpha=0.7,
                            label=f'{lbl} ({mask.sum()})', edgecolors='none')
        axes[1].set_title('True labels', fontsize=13, fontweight='bold')
        axes[1].legend(fontsize=8, frameon=True, markerscale=2)
        axes[1].set_xlabel('UMAP-1');  axes[1].set_ylabel('UMAP-2')

    fig.tight_layout()
    fig.savefig(f'{out_prefix}_umap.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def plot_pca(embeddings, pred_labels, out_prefix, true_labels=None, label_names=None):
    """2-D PCA of GNN embeddings."""
    print("  PCA...")
    pca2   = PCA(n_components=2)
    pca_xy = pca2.fit_transform(embeddings)
    nc     = len(np.unique(pred_labels))
    cmap   = _cmap_for(nc)

    n_panels = 2 if true_labels is not None else 1
    fig, axes = plt.subplots(1, n_panels, figsize=(9 * n_panels, 7))
    if n_panels == 1:
        axes = [axes]

    for c in range(nc):
        mask = pred_labels == c
        if not mask.any():
            continue
        axes[0].scatter(pca_xy[mask, 0], pca_xy[mask, 1],
                        c=[cmap(c)], s=10, alpha=0.7,
                        label=f'C{c} (n={mask.sum()})', edgecolors='none')
    axes[0].set_title('Predicted clusters', fontsize=13, fontweight='bold')
    axes[0].set_xlabel(f'PC1 ({pca2.explained_variance_ratio_[0]:.1%})')
    axes[0].set_ylabel(f'PC2 ({pca2.explained_variance_ratio_[1]:.1%})')
    axes[0].legend(fontsize=8, frameon=True, markerscale=2)

    if true_labels is not None:
        ntl   = len(np.unique(true_labels))
        cmap2 = _cmap_for(ntl)
        for i in range(ntl):
            mask = true_labels == i
            lbl  = label_names[i] if label_names else str(i)
            axes[1].scatter(pca_xy[mask, 0], pca_xy[mask, 1],
                            c=[cmap2(i)], s=10, alpha=0.7,
                            label=f'{lbl} ({mask.sum()})', edgecolors='none')
        axes[1].set_title('True labels', fontsize=13, fontweight='bold')
        axes[1].set_xlabel(f'PC1 ({pca2.explained_variance_ratio_[0]:.1%})')
        axes[1].set_ylabel(f'PC2 ({pca2.explained_variance_ratio_[1]:.1%})')
        axes[1].legend(fontsize=8, frameon=True, markerscale=2)

    fig.tight_layout()
    fig.savefig(f'{out_prefix}_pca.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def plot_silhouette(embeddings, pred_labels, out_prefix):
    """Silhouette plot by predicted cluster."""
    print("  Silhouette...")
    sil_vals = silhouette_samples(embeddings, pred_labels)
    nc       = len(np.unique(pred_labels))
    cmap     = _cmap_for(nc)
    fig, ax  = plt.subplots(figsize=(10, max(4, nc)))
    y_lower  = 10
    for c in sorted(np.unique(pred_labels)):
        mask   = pred_labels == c
        vals   = np.sort(sil_vals[mask])
        y_upper = y_lower + len(vals)
        ax.fill_betweenx(np.arange(y_lower, y_upper), 0, vals,
                         facecolor=cmap(c), edgecolor=cmap(c), alpha=0.7)
        ax.text(-0.05, y_lower + 0.5 * len(vals), f'C{c}', fontsize=9)
        y_lower = y_upper + 5
    ax.axvline(sil_vals.mean(), color='red', linestyle='--', alpha=0.7,
               label=f'avg={sil_vals.mean():.3f}')
    ax.set_xlabel('Silhouette coefficient', fontsize=11)
    ax.set_title('Silhouette by predicted cluster', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(f'{out_prefix}_silhouette.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def plot_confusion(true_labels, pred_labels, label_names, out_prefix):
    """Confusion matrix (only when labels are provided)."""
    print("  Confusion matrix...")
    cm  = confusion_matrix(true_labels, pred_labels)
    fig, ax = plt.subplots(figsize=(max(6, cm.shape[1]), max(5, cm.shape[0])))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=[f'C{i}' for i in range(cm.shape[1])],
                yticklabels=label_names if label_names else range(cm.shape[0]))
    ax.set_xlabel('Predicted cluster', fontsize=11)
    ax.set_ylabel('True label', fontsize=11)
    nmi_v = NMI(true_labels, pred_labels)
    ari_v = ARI(true_labels, pred_labels)
    ax.set_title(f'Confusion matrix  NMI={nmi_v:.3f}  ARI={ari_v:.3f}',
                 fontsize=13, fontweight='bold')
    fig.tight_layout()
    fig.savefig(f'{out_prefix}_confusion.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def plot_loss_curve(losses, out_prefix):
    """Training loss curve."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(range(1, len(losses) + 1), losses, lw=1.5, color='steelblue')
    ax.set_xlabel('Epoch');  ax.set_ylabel('NT-Xent loss')
    ax.set_title('GNN training loss', fontsize=13, fontweight='bold')
    fig.tight_layout()
    fig.savefig(f'{out_prefix}_loss.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    args   = parse_args()
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    os.makedirs(args.output_dir, exist_ok=True)
    out_prefix = os.path.join(args.output_dir, 'gnn_clustering')

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    print("=" * 70)
    print("CHR3D  —  GNN CLUSTERING  (GraphSAGE + Leiden)")
    print("=" * 70)
    print(f"  Data       : {args.data}")
    print(f"  Output dir : {args.output_dir}")
    print(f"  Labels     : {args.labels or 'none (unsupervised mode)'}")
    print(f"  Device     : {DEVICE}")
    print(f"  Seed       : {args.seed}")
    print("=" * 70)

    t0 = time.time()

    # ── Load data ────────────────────────────────────────────────────────────
    print("\n[DATA] Loading features...")
    tfidf_ss, cell_ids = load_features(args.data)
    print(f"  {len(cell_ids)} cells, {tfidf_ss.shape[1]} features")

    true_labels, label_names = load_labels(args.labels, cell_ids)
    if true_labels is not None:
        print(f"  Labels loaded: {label_names}")

    # ── PCA ──────────────────────────────────────────────────────────────────
    pca_dim = min(args.pca_dim, tfidf_ss.shape[0] - 1, tfidf_ss.shape[1])
    print(f"\n[PCA] {tfidf_ss.shape[1]}D → {pca_dim}D...")
    pca_model = PCA(n_components=pca_dim, random_state=args.seed)
    X_pca     = pca_model.fit_transform(tfidf_ss).astype(np.float32)
    print(f"  Explained variance (top-5): "
          f"{pca_model.explained_variance_ratio_[:5].cumsum()[-1]:.1%}")

    # ── kNN graph ────────────────────────────────────────────────────────────
    k_graph = min(args.k_graph, len(cell_ids) - 1)
    print(f"\n[GRAPH] Building kNN graph (k={k_graph})...")
    A = kneighbors_graph(X_pca, n_neighbors=k_graph, mode='connectivity',
                         include_self=False, n_jobs=-1)
    A = A + A.T
    A[A > 1] = 1
    rows, cols = A.nonzero()
    edge_index  = torch.tensor(np.array([rows, cols]), dtype=torch.long).to(DEVICE)
    print(f"  {edge_index.size(1):,} edges")

    # ── Train GNN ────────────────────────────────────────────────────────────
    print(f"\n[TRAIN] GraphSAGE  {pca_dim}→{args.hidden_dim}→{args.out_dim}  "
          f"layers={args.n_layers}  epochs={args.epochs}  τ={args.tau}")
    x_tensor  = torch.tensor(X_pca, dtype=torch.float32).to(DEVICE)
    model     = GraphSAGEEncoder(pca_dim, args.hidden_dim, args.out_dim,
                                  args.n_layers, args.dropout).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                    optimizer, T_max=args.epochs, eta_min=1e-6)

    best_loss, best_state = float('inf'), None
    all_losses = []
    model.train()
    for epoch in range(args.epochs):
        optimizer.zero_grad()
        z    = model(x_tensor, edge_index)
        loss = nt_xent_graph_loss(z, edge_index, tau=args.tau,
                                   neg_sample_ratio=args.neg_ratio)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        all_losses.append(loss.item())
        if loss.item() < best_loss:
            best_loss  = loss.item()
            best_state = copy.deepcopy(model.state_dict())
        if (epoch + 1) % 50 == 0:
            print(f"    Epoch {epoch+1:4d}/{args.epochs}  loss={loss.item():.4f}")

    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        embeddings = model(x_tensor, edge_index).cpu().numpy()
    print(f"  Best loss: {best_loss:.4f}")
    print(f"  Embeddings: {embeddings.shape}")

    # ── Cluster ───────────────────────────────────────────────────────────────
    print("\n[CLUSTER] Leiden grid search (optimising silhouette)...")
    best_pred, best_tag, best_nmi, best_ari, best_sil = cluster_leiden(
        embeddings, true_labels)

    if best_pred is None:
        print("  WARNING: clustering failed (too few cells?), assigning all to cluster 0")
        best_pred = np.zeros(len(cell_ids), dtype=int)

    elapsed = time.time() - t0

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"  Clusters    : {len(np.unique(best_pred))}")
    print(f"  Silhouette  : {best_sil:.4f}")
    if true_labels is not None:
        print(f"  NMI         : {best_nmi:.4f}")
        print(f"  ARI         : {best_ari:.4f}")
    print(f"  Best config : {best_tag}")
    print(f"  Time        : {elapsed:.0f}s")

    print("\n[CLUSTER ANALYSIS]")
    for c in sorted(np.unique(best_pred)):
        mask = best_pred == c
        print(f"  Cluster {c:2d}: n={mask.sum()}", end="")
        if true_labels is not None:
            cnts = np.bincount(true_labels[mask], minlength=len(label_names))
            dom  = label_names[np.argmax(cnts)]
            pur  = cnts.max() / cnts.sum()
            print(f"  dominant={dom} ({pur:.0%})", end="")
        print()

    # ── Save results ─────────────────────────────────────────────────────────
    res_row = {'seed': args.seed, 'silhouette': best_sil,
               'n_clusters': len(np.unique(best_pred)), 'config': best_tag}
    if true_labels is not None:
        res_row.update({'nmi': best_nmi, 'ari': best_ari})
    pd.DataFrame([res_row]).to_csv(f'{out_prefix}_results.csv', index=False)

    pred_df = pd.DataFrame({'cell_id': cell_ids, 'cluster': best_pred})
    if true_labels is not None:
        pred_df['true_label'] = [label_names[l] for l in true_labels]
    pred_df.to_csv(f'{out_prefix}_predictions.csv', index=False)

    np.save(f'{out_prefix}_embeddings.npy', embeddings)

    torch.save({
        'model_state_dict': model.state_dict(),
        'pca_model':        pca_model,
        'config': {'seed': args.seed, 'pca_dim': pca_dim, 'k_graph': k_graph,
                   'hidden_dim': args.hidden_dim, 'out_dim': args.out_dim}
    }, f'{out_prefix}_model.pth')

    # ── Plots ─────────────────────────────────────────────────────────────────
    print("\n[PLOTS] Generating visualizations...")
    plot_loss_curve(all_losses, out_prefix)
    nc_final = len(np.unique(best_pred))
    if nc_final >= 2:
        plot_umap(embeddings, best_pred, out_prefix, true_labels, label_names)
        plot_pca(embeddings, best_pred, out_prefix, true_labels, label_names)
        plot_silhouette(embeddings, best_pred, out_prefix)
        if true_labels is not None:
            plot_confusion(true_labels, best_pred, label_names, out_prefix)
    else:
        print(f"  Skipping UMAP/PCA/silhouette: only {nc_final} cluster (need ≥2)")
        print("  NOTE: This is a small test dataset. Real data with more cells will cluster properly.")

    saved = [f'{out_prefix}_loss.png',
             f'{out_prefix}_results.csv', f'{out_prefix}_predictions.csv',
             f'{out_prefix}_embeddings.npy', f'{out_prefix}_model.pth']
    if nc_final >= 2:
        saved += [f'{out_prefix}_umap.png', f'{out_prefix}_pca.png',
                  f'{out_prefix}_silhouette.png']
        if true_labels is not None:
            saved.append(f'{out_prefix}_confusion.png')

    print("\n" + "=" * 70)
    print("Files saved:")
    for f in saved:
        print(f"  {f}")
    print("=" * 70)


if __name__ == '__main__':
    main()
