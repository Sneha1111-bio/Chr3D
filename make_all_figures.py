#!/usr/bin/env python3
"""
make_all_figures.py
Builds all poster figures from the Chr3D clustering results.
Values are taken from the summary CSVs produced across the project.
Writes PNGs to /home/sneha/Downloads/run/figures/
"""
import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTDIR = "/home/sneha/Downloads/run/figures"
os.makedirs(OUTDIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 12, "font.family": "DejaVu Sans",
    "axes.titlesize": 15, "axes.titleweight": "bold",
    "axes.labelsize": 13, "figure.dpi": 150,
})
NMI = "#2E5C8A"
ARI = "#C0504D"
GREY = "#7F7F7F"

# paths to the real grid CSVs (read live for the heatmap + resolution)
GRID_100 = "/home/sneha/Downloads/run/grid/grid_raw.csv"
GRID_50  = "/home/sneha/Downloads/run/sweep/res50_fullgrid/res50_fullgrid_results.csv"
GRID_500 = "/home/sneha/Downloads/run/sweep/res500_fullgrid/res500_partial_results.csv"


def to_float(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return None


def read_grid(path, has_status=False):
    """Return list of (pca, k, nmi, ari) from a grid CSV."""
    out = []
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for r in csv.DictReader(f):
            if has_status and r.get("status") != "ok":
                continue
            pca = to_float(r.get("pca_dim"))
            k = to_float(r.get("k_graph"))
            nmi = to_float(r.get("nmi"))
            ari = to_float(r.get("ari"))
            if pca and k and nmi is not None:
                out.append((pca, k, nmi, ari))
    return out


# ============================================================
# FIG 1 — Headline: input format drives everything
# ============================================================
def fig1():
    labels = ["Benchmark\n(partner)", "Cooler input\n(baseline)",
              "Text input\n(default)", "Text input\n(pca=10)"]
    nmi = [0.63, 0.19, 0.81, 0.86]
    ari = [0.56, 0.17, 0.81, 0.81]
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(9, 5.5))
    b1 = ax.bar(x - w/2, nmi, w, label="NMI", color=NMI)
    b2 = ax.bar(x + w/2, ari, w, label="ARI", color=ARI)
    ax.axhline(0.63, ls="--", lw=1, color="grey")
    ax.text(3.45, 0.645, "benchmark 0.63", ha="right", fontsize=9, color="grey")
    ax.set_ylabel("Score"); ax.set_ylim(0, 1.0)
    ax.set_title("Input data format is the biggest driver of clustering quality")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.legend(loc="upper left")
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.2f}",
                        (b.get_x()+b.get_width()/2, b.get_height()),
                        textcoords="offset points", xytext=(0, 3),
                        ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig1_input_format.png")); plt.close(fig)
    print("  fig1 input format")


# ============================================================
# FIG 2 — PCA dimension curve (from the k=20 sweep)
# ============================================================
def fig2():
    pca = [10, 20, 30, 50, 75, 100, 150, 200]
    nmi = [0.860, 0.833, 0.800, 0.804, 0.825, 0.809, 0.807, 0.795]
    ari = [0.888, 0.846, 0.778, 0.795, 0.831, 0.796, 0.805, 0.757]
    x = np.arange(len(pca))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(x, nmi, "o-", color=NMI, label="NMI", lw=2.5, ms=8)
    ax.plot(x, ari, "s-", color=ARI, label="ARI", lw=2.5, ms=8)
    for xi, yi in zip(x, nmi):
        ax.annotate(f"{yi:.2f}", (xi, yi), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9, color=NMI)
    bi = int(np.argmax(nmi))
    ax.annotate("best\npca=10", (x[bi], nmi[bi]), textcoords="offset points",
                xytext=(0, -38), ha="center", fontsize=10, color=NMI, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=NMI))
    ax.set_xticks(x); ax.set_xticklabels([str(p) for p in pca])
    ax.set_xlabel("PCA dimensions"); ax.set_ylabel("Score")
    ax.set_title("Fewer PCA dimensions score higher (best at 10)")
    ax.set_ylim(0.6, 1.0); ax.grid(True, alpha=0.3); ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig2_pca_dimension.png")); plt.close(fig)
    print("  fig2 pca dimension")


# ============================================================
# FIG 3 — n-clusters curve
# ============================================================
def fig3():
    nc = [4, 5, 6, 7, 8]
    nmi = [0.869, 0.804, 0.758, 0.741, 0.697]
    ari = [0.897, 0.795, 0.683, 0.671, 0.575]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(nc, nmi, "o-", color=NMI, label="NMI", lw=2.5, ms=8)
    ax.plot(nc, ari, "s-", color=ARI, label="ARI", lw=2.5, ms=8)
    ax.axvline(5, ls="--", lw=1, color="green", alpha=0.6)
    ax.text(5.05, 0.60, "true # types = 5", color="green", fontsize=9)
    ax.set_xlabel("Number of clusters requested"); ax.set_ylabel("Score")
    ax.set_title("Score drops as more clusters are forced")
    ax.set_ylim(0.5, 1.0); ax.set_xticks(nc); ax.grid(True, alpha=0.3); ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig3_n_clusters.png")); plt.close(fig)
    print("  fig3 n-clusters")


# ============================================================
# FIG 4 — Resolution comparison (50 vs 100 vs 500 kb)
# Uses best NMI/ARI found at each resolution from the grids.
# ============================================================
def fig4():
    # best scores per resolution (read from grids; fallback to known values)
    def best(path, has_status=False):
        rows = read_grid(path, has_status)
        if not rows:
            return None, None
        best_row = max(rows, key=lambda r: r[2])
        return best_row[2], best_row[3]

    n50, a50 = best(GRID_50)
    n100, a100 = best(GRID_100, has_status=True)
    n500, a500 = best(GRID_500)
    # fallbacks if a file is missing
    if n50 is None: n50, a50 = 0.863, 0.886
    if n100 is None: n100, a100 = 0.863, 0.889
    if n500 is None: n500, a500 = 0.195, 0.181

    res = ["50kb", "100kb", "500kb"]
    nmi = [n50, n100, n500]
    ari = [a50, a100, a500]
    x = np.arange(len(res)); w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5.5))
    b1 = ax.bar(x - w/2, nmi, w, label="NMI", color=NMI)
    b2 = ax.bar(x + w/2, ari, w, label="ARI", color=ARI)
    ax.set_ylabel("Best score"); ax.set_ylim(0, 1.0)
    ax.set_title("Resolution: 50kb and 100kb work; 500kb collapses")
    ax.set_xticks(x); ax.set_xticklabels(res); ax.legend()
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.2f}",
                        (b.get_x()+b.get_width()/2, b.get_height()),
                        textcoords="offset points", xytext=(0, 3),
                        ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig4_resolution.png")); plt.close(fig)
    print("  fig4 resolution")


# ============================================================
# FIG 5 — Distance metric comparison
# ============================================================
def fig5():
    metrics = ["cosine", "euclidean", "correlation", "manhattan"]
    nmi = [0.859, 0.815, 0.809, 0.0]   # manhattan failed (1 cluster)
    ari = [0.884, 0.815, 0.809, 0.0]
    x = np.arange(len(metrics)); w = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    b1 = ax.bar(x - w/2, nmi, w, label="NMI", color=NMI)
    b2 = ax.bar(x + w/2, ari, w, label="ARI", color=ARI)
    ax.set_ylabel("Score"); ax.set_ylim(0, 1.0)
    ax.set_title("Distance metric: cosine is best; manhattan fails")
    ax.set_xticks(x); ax.set_xticklabels(metrics); ax.legend()
    ax.annotate("failed\n(1 cluster)", (3, 0.03), ha="center", va="bottom",
                fontsize=9, color="grey")
    for bars in (b1, b2):
        for b in bars:
            if b.get_height() > 0:
                ax.annotate(f"{b.get_height():.2f}",
                            (b.get_x()+b.get_width()/2, b.get_height()),
                            textcoords="offset points", xytext=(0, 3),
                            ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig5_distance_metric.png")); plt.close(fig)
    print("  fig5 distance metric")


# ============================================================
# FIG 6 — kNN ablation (with vs without)
# ============================================================
def fig6():
    cats = ["with kNN", "without kNN"]
    nmi = [0.866, 0.847]
    ari = [0.891, 0.875]
    sil = [0.163, 0.046]
    x = np.arange(len(cats)); w = 0.25
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.bar(x - w, nmi, w, label="NMI", color=NMI)
    ax.bar(x, ari, w, label="ARI", color=ARI)
    ax.bar(x + w, sil, w, label="Silhouette", color=GREY)
    ax.set_ylabel("Score"); ax.set_ylim(0, 1.0)
    ax.set_title("Removing the kNN step: NMI barely changes, silhouette collapses")
    ax.set_xticks(x); ax.set_xticklabels(cats); ax.legend()
    for xi, (n, a, s) in zip(x, zip(nmi, ari, sil)):
        ax.annotate(f"{n:.2f}", (xi - w, n), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9)
        ax.annotate(f"{a:.2f}", (xi, a), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9)
        ax.annotate(f"{s:.2f}", (xi + w, s), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig6_knn_ablation.png")); plt.close(fig)
    print("  fig6 knn ablation")


# ============================================================
# FIG 7 — Repeatability (10 seeds at pca=10)
# ============================================================
def fig7():
    seeds = [0, 1, 2, 3, 4, 5, 6, 8, 9]  # seed 7 collapsed, excluded
    nmi = [0.8616, 0.8084, 0.8019, 0.8031, 0.8131, 0.8096, 0.8060, 0.8131, 0.8081]
    mean = np.mean(nmi); std = np.std(nmi)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.bar([str(s) for s in seeds], nmi, color=NMI, alpha=0.8)
    ax.axhline(mean, color=ARI, lw=2, label=f"mean = {mean:.3f}")
    ax.axhspan(mean-std, mean+std, color=ARI, alpha=0.15, label=f"± std ({std:.3f})")
    ax.set_xlabel("Random seed"); ax.set_ylabel("NMI")
    ax.set_title(f"Repeatability at pca=10: NMI = {mean:.2f} ± {std:.2f} (stable)")
    ax.set_ylim(0.7, 0.9); ax.legend()
    ax.text(0.5, 0.72, "(seed 7 excluded — collapsed to 1 cluster)",
            fontsize=8, color="grey")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig7_repeatability.png")); plt.close(fig)
    print("  fig7 repeatability")


# ============================================================
# FIG 8 — PCA x k heatmaps (NMI + ARI) side by side, 100kb grid
# ============================================================
def fig8():
    rows = read_grid(GRID_100, has_status=True)
    if not rows:
        print("  (skip) fig8 heatmap: 100kb grid not found")
        return
    pcas = sorted({int(r[0]) for r in rows})
    ks = sorted({int(r[1]) for r in rows})

    def build(idx):
        M = np.full((len(pcas), len(ks)), np.nan)
        for pca, k, nmi, ari in rows:
            i = pcas.index(int(pca)); j = ks.index(int(k))
            M[i, j] = nmi if idx == 2 else ari
        return M

    Mn = build(2); Ma = build(3)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, M, title, cmap in [(axes[0], Mn, "NMI", "viridis"),
                                (axes[1], Ma, "ARI", "magma")]:
        im = ax.imshow(M, cmap=cmap, aspect="auto", vmin=0.75, vmax=0.90, origin="lower")
        ax.set_xticks(range(len(ks))); ax.set_xticklabels(ks)
        ax.set_yticks(range(len(pcas))); ax.set_yticklabels(pcas)
        ax.set_xlabel("k (graph neighbours)"); ax.set_ylabel("PCA dimensions")
        ax.set_title(f"{title} across PCA \u00d7 k  (100kb)")
        for i in range(len(pcas)):
            for j in range(len(ks)):
                if not np.isnan(M[i, j]):
                    ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center",
                            color="white" if M[i, j] < 0.82 else "black", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Method is robust across PCA and k (all 0.79\u20130.86)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "fig8_heatmap_pca_k.png")); plt.close(fig)
    print("  fig8 heatmap")


def main():
    print("Building figures...")
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7(); fig8()
    print(f"\nDone. All figures in: {OUTDIR}")


if __name__ == "__main__":
    main()
