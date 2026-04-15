# Chr3D: End-to-End 3D Chromatin Analysis Pipeline

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Bioconda](https://img.shields.io/conda/dn/bioconda/chr3d.svg)](https://anaconda.org/bioconda/chr3d)

**Chr3D** is a unified, end-to-end framework for analyzing 3D chromatin architecture data. It supports bulk Hi-C, single-nucleus Hi-C, and ChIA-PET through a single modular CLI with integrated TAD calling, loop detection, A/B compartment analysis, and clustering.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Examples](#examples)
- [Output Structure](#output-structure)
- [Citation](#citation)

## Features

### Core Pipelines
- **`bulk-hic`** - Population-averaged Hi-C from FASTQ to publication-ready results
- **`sn-hic`** - Single-nucleus Hi-C with per-cell processing and clustering
- **`chia-pet`** - Protein-centric chromatin interactions with novel background model

### Built-in Analysis
- **TAD Calling** - Insulation score detection with multi-resolution windows
- **Loop Calling** - FDR-filtered loop detection using cooltools dots
- **Compartment Calling** - A/B compartment eigenvector analysis with phasing
- **Peak Calling** - MACS3 peak calling for ChIA-PET
- **Background Model** - Industry-first template-based null for ChIA-PET FDR correction

### Unique Advantages
- **Single-command execution** from FASTQ to biological insights
- **Resume-safe** processing with automatic checkpointing
- **Multi-modal support** in one unified framework
- **Modular classes** for custom analysis workflows
- **Publication-quality outputs** with proper statistical corrections

## Installation

### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourlab/chr3d.git
cd chr3d

# Run the installation script
bash install.sh
```

### Option 2: Manual Installation

```bash
# Create conda environment
conda create -n chr3d python=3.11 -y
conda activate chr3d

# Configure channels
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge

# Install core tools
conda install -y bwa samtools macs3 pairtools cooler cooltools

# Install Python dependencies
conda install -y numpy pandas scipy biopython pysam tqdm
conda install -c bioconda parasail-python

# Install Chr3D
pip install -e .
```

### Verify Installation

```bash
chr3d --help
```

## Quick Start

### Bulk Hi-C Analysis

```bash
chr3d bulk-hic \
    --r1 sample_R1.fastq.gz \
    --r2 sample_R2.fastq.gz \
    --genome /ref/hg38.fa \
    --chrom-sizes /ref/hg38.chrom.sizes \
    --output-dir ./results \
    --sample-id sample1 \
    --threads 24 \
    --resolutions 1000,5000,10000,25000,50000,100000
```

### Single-Nucleus Hi-C with Clustering

```bash
chr3d sn-hic \
    --manifest cells_manifest.tsv \
    --genome /ref/hg38.fa \
    --chrom-sizes /ref/hg38.chrom.sizes \
    --output-dir ./sn_results \
    --threads 24 \
    --run-clustering \
    --min-contacts 1000
```

### ChIA-PET with Background Model

```bash
chr3d chia-pet \
    --r1 chip_R1.fastq.gz \
    --r2 chip_R2.fastq.gz \
    --genome /ref/hg38.fa \
    --chrom-sizes /ref/hg38.chrom.sizes \
    --linkers ACGCGATATCGCG \
    --output-dir ./chia_results \
    --sample-id ctcf_chip \
    --threads 24
```

## Command Reference

### Global Options

```bash
chr3d --help                    # Show help
chr3d --version                 # Show version
chr3d -v --verbose              # Enable debug logging
chr3d --log-file chr3d.log      # Write log to file
```

---

### bulk-hic

Process bulk Hi-C data from paired-end FASTQ to contact matrices and downstream analysis.

```bash
chr3d bulk-hic [OPTIONS] --r1 FASTQ --r2 FASTQ --genome PATH --chrom-sizes PATH --output-dir DIR
```

#### Required Arguments

| Argument | Description |
|----------|-------------|
| `--r1` | R1 FASTQ file (gzipped or plain) |
| `--r2` | R2 FASTQ file (gzipped or plain) |
| `--genome` | BWA-indexed genome FASTA |
| `--chrom-sizes` | Chromosome sizes file |
| `--output-dir` | Output directory |

#### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--sample-id` | `sample` | Sample identifier for output files |
| `--threads` | `4` | Number of CPU threads |
| `--splits` | `0` | Split FASTQ into N chunks for parallel alignment |
| `--assembly` | `hg38` | Genome assembly name |
| `--min-mapq` | `30` | Minimum BWA mapping quality |
| `--min-distance` | `1000` | Minimum pair distance in bp |
| `--resolutions` | `1000,5000,10000` | Comma-separated matrix resolutions |
| `--keep-intermediates` | `False` | Keep intermediate BAM/pairs files |

#### TAD Calling Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--no-tads` | `False` | Skip TAD calling |
| `--tad-windows` | `None` | Comma-separated insulation window sizes |

#### Loop Calling Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--no-loops` | `False` | Skip loop calling |
| `--loop-fdr` | `0.1` | FDR threshold for loop significance |

#### Compartment Calling Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--no-compartments` | `False` | Skip compartment calling |
| `--compartment-phasing-track` | `None` | BED file for E1 sign orientation |

---

### sn-hic

Process single-nucleus Hi-C data with per-cell processing and optional clustering.

```bash
chr3d sn-hic [OPTIONS] --manifest FILE --genome PATH --chrom-sizes PATH --output-dir DIR
```

#### Required Arguments

| Argument | Description |
|----------|-------------|
| `--manifest` | TSV file: cell_id<TAB>R1<TAB>R2 |
| `--genome` | BWA-indexed genome FASTA |
| `--chrom-sizes` | Chromosome sizes file |
| `--output-dir` | Output directory |

#### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--threads` | `4` | Number of CPU threads |
| `--assembly` | `hg38` | Genome assembly name |
| `--min-mapq` | `30` | Minimum BWA mapping quality |
| `--min-distance` | `1000` | Minimum pair distance in bp |
| `--resolutions` | `10000` | Single-cell matrix resolution |
| `--min-contacts` | `1000` | Minimum contacts per cell |
| `--run-clustering` | `False` | Run GNN-based clustering |
| `--n-clusters` | `None` | Expected number of clusters |

#### Clustering Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--pca-dim` | `50` | PCA dimension before GNN |
| `--k-neighbors` | `15` | k for k-NN graph |
| `--hidden-dim` | `128` | GNN hidden dimension |
| `--epochs` | `200` | Training epochs |
| `--random-state` | `0` | Random seed |

---

### chia-pet

Process ChIA-PET data with peak calling and novel background model.

```bash
chr3d chia-pet [OPTIONS] --r1 FASTQ --r2 FASTQ --genome PATH --linkers SEQ --output-dir DIR
```

#### Required Arguments

| Argument | Description |
|----------|-------------|
| `--r1` | R1 FASTQ file |
| `--r2` | R2 FASTQ file |
| `--genome` | BWA-indexed genome FASTA |
| `--chrom-sizes` | Chromosome sizes file |
| `--linkers` | Linker sequence (e.g., ACGCGATATCGCG) |
| `--output-dir` | Output directory |

#### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--sample-id` | `sample` | Sample identifier |
| `--threads` | `4` | Number of CPU threads |
| `--assembly` | `hg38` | Genome assembly name |
| `--min-mapq` | `30` | Minimum BWA mapping quality |
| `--min-distance` | `1000` | Minimum pair distance |
| `--keep-intermediates` | `False` | Keep intermediate files |

#### Peak Calling Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--no-peaks` | `False` | Skip peak calling |
| `--peak-fdr` | `0.01` | Peak FDR threshold |
| `--peak-ext` | `200` | Peak extension in bp |

#### Background Model Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--no-background` | `False` | Skip background model |
| `--background-fdr` | `0.05` | Interaction FDR threshold |

---

## Examples

### Example 1: Complete Bulk Hi-C Analysis

```bash
chr3d bulk-hic \
    --r1 /data/hic/sample_R1.fastq.gz \
    --r2 /data/hic/sample_R2.fastq.gz \
    --genome /ref/hg38.fa \
    --chrom-sizes /ref/hg38.chrom.sizes \
    --output-dir /results/hic/sample1 \
    --sample-id sample1 \
    --threads 32 \
    --resolutions 1000,5000,10000,25000,50000,100000 \
    --tad-windows 50000,100000,200000 \
    --loop-fdr 0.05 \
    --compartment-phasing-track /ref/gene_density.bed
```

### Example 2: Single-Nucleus Hi-C with Clustering

```bash
# Create manifest file
cat > cells_manifest.tsv << EOF
cell1   /data/sn/cell1_R1.fastq.gz   /data/sn/cell1_R2.fastq.gz
cell2   /data/sn/cell2_R1.fastq.gz   /data/sn/cell2_R2.fastq.gz
cell3   /data/sn/cell3_R1.fastq.gz   /data/sn/cell3_R2.fastq.gz
EOF

# Run pipeline
chr3d sn-hic \
    --manifest cells_manifest.tsv \
    --genome /ref/hg38.fa \
    --chrom-sizes /ref/hg38.chrom.sizes \
    --output-dir /results/sn_hic \
    --threads 24 \
    --run-clustering \
    --n-clusters 5 \
    --min-contacts 2000 \
    --pca-dim 50 \
    --epochs 300
```

### Example 3: ChIA-PET with Background Model

```bash
chr3d chia-pet \
    --r1 /data/chip/ctcf_R1.fastq.gz \
    --r2 /data/chip/ctcf_R2.fastq.gz \
    --genome /ref/hg38.fa \
    --chrom-sizes /ref/hg38.chrom.sizes \
    --linkers ACGCGATATCGCG \
    --output-dir /results/chip/ctcf \
    --sample-id ctcf_rep1 \
    --threads 32 \
    --peak-fdr 0.01 \
    --background-fdr 0.05
```

### Example 4: Resume Failed Pipeline

```bash
# If pipeline failed during TAD calling, resume from that step
chr3d bulk-hic \
    --r1 sample_R1.fastq.gz \
    --r2 sample_R2.fastq.gz \
    --genome /ref/hg38.fa \
    --chrom-sizes /ref/hg38.chrom.sizes \
    --output-dir ./results \
    --sample-id sample1 \
    --threads 24 \
    --resume-from tads
```

## Output Structure

### Bulk Hi-C Output

```
output_dir/
|-- aligned/                    # Alignment outputs
|   |-- sample1_sorted.bam
|   |-- sample1_sorted.bam.bai
|   |-- sample1_flagstat.txt
|-- pairs/                      # Pair processing
|   |-- sample1.sorted.pairs.gz
|   |-- sample1.sorted.pairs.gz.idx
|   |-- sample1.filtered.pairs.gz
|   |-- sample1.dedup.pairs.gz
|-- matrices/                   # Contact matrices
|   |-- sample1.cool
|   |-- sample1.mcool
|   |-- @resolutions/
|       |-- 1000/
|       |-- 5000/
|       |-- 10000/
|-- tads/                       # TAD calling results
|   |-- sample1_res5kb_tad_summary.tsv
|   |-- 5kb/
|   |   |-- sample1_5kb_insulation.tsv
|   |   |-- sample1_5kb_boundaries.bed
|   |-- 10kb/
|   |-- 25kb/
|-- loops/                      # Loop calling results
|   |-- sample1_loop_summary.tsv
|   |-- 5kb_loops.bedpe
|   |-- 10kb_loops.bedpe
|   |-- 25kb_loops.bedpe
|-- compartments/               # Compartment calling
|   |-- sample1_compartment_summary.tsv
|   |-- sample1_res25kb_compartments.tsv
|   |-- sample1_res25kb_A_compartment.bed
|   |-- sample1_res25kb_B_compartment.bed
|-- qc/                         # Quality control
|   |-- sample1_timing.txt
|   |-- sample1_stats.json
```

### Single-Nucleus Hi-C Output

```
output_dir/
|-- per_cell/                   # Individual cell outputs
|   |-- cell1/
|   |   |-- cell1.cool
|   |   |-- cell1_stats.json
|   |-- cell2/
|-- matrices/                   # Pseudobulk matrices
|   |-- pseudobulk.cool
|   |-- pseudobulk.mcool
|-- clustering/                 # Clustering results
|   |-- cell_bin_matrix.csv
|   |-- clustering_results.json
|   |-- umap_plot.png
|   |-- cluster_0_pseudobulk.cool
|   |-- cluster_1_pseudobulk.cool
```

### ChIA-PET Output

```
output_dir/
|-- aligned/                    # Same as bulk Hi-C
|-- pairs/                      # Same as bulk Hi-C
|-- peaks/                      # Peak calling
|   |-- sample_peaks.narrowPeak
|   |-- sample_peaks.summits.bed
|-- interactions/               # Interaction calling
|   |-- sample_interactions.tsv
|   |-- sample_significant_interactions.tsv
|   |-- sample_background_model.pkl
|-- qc/                         # Quality control
```

## Advanced Usage

### Custom TAD Windows

```bash
# Use custom window sizes for different resolution ranges
chr3d bulk-hic \
    ... \
    --tad-windows 25000,50000,100000,250000,500000,1000000
```

### Selective Analysis

```bash
# Run only alignment and matrix generation
chr3d bulk-hic \
    ... \
    --no-tads --no-loops --no-compartments

# Run only TAD calling on existing matrix
chr3d bulk-hic \
    --r1 dummy.fastq \
    --r2 dummy.fastq \
    ... \
    --resume-from tads
```

### Integration with Existing Tools

```python
# Use Chr3D classes in Python scripts
from chr3d.hic.tads import HiCTADCaller
from chr3d.hic.loop_calling import HiCLoopCaller

# TAD calling
tad_caller = HiCTADCaller(windows=[50000, 100000])
tad_results = tad_caller.run(
    mcool_file="sample.mcool",
    output_dir="./tads",
    sample_id="sample1"
)

# Loop calling
loop_caller = HiCLoopCaller(fdr=0.05)
loop_results = loop_caller.run(
    mcool_file="sample.mcool",
    output_dir="./loops",
    sample_id="sample1"
)
```

## Troubleshooting

### Common Issues

1. **Memory errors during matrix generation**
   - Reduce `--threads` to limit memory usage
   - Use larger `--min-distance` to filter more pairs
   - Process smaller chromosomes first

2. **Failed TAD/loop calling**
   - Check matrix quality with `chr3d qc`
   - Increase `--min-distance` if too few contacts
   - Try larger window sizes for TAD calling

3. **Clustering fails**
   - Ensure enough cells (>50) with sufficient contacts
   - Reduce `--min-contacts` to include more cells
   - Try different `--n-clusters` value

### Getting Help

```bash
# Get help for specific command
chr3d bulk-hic --help
chr3d sn-hic --help
chr3d chia-pet --help

# Enable verbose logging for debugging
chr3d bulk-hic --verbose --log-file debug.log ...
```

## Citation

If you use Chr3D in your research, please cite:

```
Chr3D: A Unified Framework for End-to-End 3D Chromatin Analysis
[Your Name], et al.
[Journal] [Year]
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourlab/chr3d/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourlab/chr3d/discussions)
- **Email**: your-email@institution.edu
