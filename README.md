# Chr3D: End-to-End 3D Chromatin Analysis Pipeline


**Chr3D** is a unified, end-to-end framework for analyzing 3D chromatin architecture data. It supports bulk Hi-C, single-nucleus Hi-C, HiChIP and ChIA-PET through a single modular CLI & Python API.

**Note:** TUI Interface is also in development

# Supports

- ChiaPET
- HiChIP
- Hic
- snHIC
- HiGlass
- Restriction Site Generation & Detection
- File converters

# Docs

Check out the docs at [Chr3D Docs](https://chr3d.rudhrajoshi.me/)

# Install

Get the Chr3D pipeline running locally.

## Prerequisites

- **Conda** (Miniconda or Anaconda)
- **Git**

## 1. Clone the repository

```bash filename="Terminal"
git clone https://github.com/rudrajoshi2481/Chr3D.git
cd Chr3D
```

## 2. Run the install script

The repository includes an automated install script that sets up everything.

```bash filename="Terminal"
chmod +x install.sh
./install.sh
```

## 3. Activate and use

or check out the docs at [Chr3D Docs](https://chr3d.rudhrajoshi.me/)    

```bash filename="Terminal"
conda activate chr3d
chr3d --help
```

Or use the Python API:

```python filename="Python"
import chr3d as c3d
print(c3d.__version__)
```

---

## Quick Start

Chr3D provides unified CLI commands for all major chromatin conformation assays. Below are concise examples for each supported protocol.

### Bulk Hi-C

```bash
chr3d bulk-hic \
    --r1 sample_R1.fastq.gz \
    --r2 sample_R2.fastq.gz \
    --genome /data/genomes/hg38.fa \
    --chrom-sizes /data/genomes/hg38.chrom.sizes \
    --output-dir ./results/my_sample \
    --sample-id my_sample
```

### Single-Nucleus Hi-C

```bash
chr3d sn-hic \
    --manifest cells.tsv \
    --genome /data/genomes/hg38.fa \
    --chrom-sizes /data/genomes/hg38.chrom.sizes \
    --output-dir ./results/sn_hic \
    --threads 24
```

### ChIA-PET

```bash
chr3d chia-pet \
    --r1 sample_R1.fastq.gz \
    --r2 sample_R2.fastq.gz \
    --genome /data/genomes/hg38.fa \
    --linkers ACGCGATATCGCG \
    --output-dir ./results/chiapet \
    --sample-id my_sample
```

### HiChIP

First generate restriction fragments, then run the pipeline:

```bash
# Generate MboI fragment map
chr3d digest -e MboI -o hg38_MboI.bed /data/genomes/hg38.fa

# Run HiChIP
chr3d hichip \
    --r1 sample_R1.fastq.gz \
    --r2 sample_R2.fastq.gz \
    --genome /data/genomes/hg38.fa \
    --fragments hg38_MboI.bed \
    --output-dir ./results/hichip \
    --sample-id my_sample
```

### scHi-C Clustering (Python API)

Chr3D provides unsupervised GraphSAGE-based clustering for single-cell Hi-C data. For large datasets (e.g., 16k cells), organize files as follows:

**Option 1: Directory of .mcool files (one per cell)**
```bash
cells/
├── cell_001.mcool
├── cell_002.mcool
└── ...  # 16,000 individual .mcool files
```

```python
from chr3d.hic.clustering import Chr3DCluster

model = Chr3DCluster(
    resolution=100_000,       # bin size (100 kb)
    k_neighbors=15,
    leiden_resolution=0.15,
    n_clusters=5,            # expected number of cell types
)

# Pass the directory containing all .mcool files
labels = model.fit_predict("cells/")
```

**Option 2: Higashi-format text file (all cells in one file)**
```python
# Tab-delimited: cell_id, chrom1, chrom2, pos1, pos2, count
labels = model.fit_predict("data.txt")
```

**Option 3: Preprocess first, then cluster**

For 16k cells, you may want to precompute the feature matrix:

```bash
python -m chr3d.hic.clustering.preprocessing \
    --mode mcool \
    --mcool_dir cells/ \
    --chrom_sizes hg38.chrom.sizes \
    --resolution 100kb \
    --output_dir ./preprocessed
```

Then cluster the resulting matrix:

```bash
python -m chr3d.hic.clustering.gnn_clustering \
    --data ./preprocessed/cell_bin_matrix_100000_coverage_log10int.csv \
    --output-dir ./clustering_results \
    --n-clusters 5 \
    --k-graph 15
```

### Additional Utilities

```bash
# Generate restriction enzyme fragment maps
chr3d digest -e HindIII -o hg38_HindIII.bed /data/genomes/hg38.fa

# Convert loops to HiGlass-compatible format
chr3d loops-to-beddb loops.csv -o loops.beddb

# Display all available commands
chr3d --help
```

---

## Future Plans & Fixes

- [ ] Removing counting before splitting files
- [ ] Update API make it even more flexible
- [ ] Add TUI based interface
- [ ] Add config file as input in Command & TUI
- [ ] Update Logging make it even more flexible
- [ ] Update file Conversion scripts


