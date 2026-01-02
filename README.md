# Chr3D: A Comprehensive Python Framework for Chromatin Interactions Analysis

A comprehensive Python library for analyzing chromatin interaction data from ChIA-PET, HiChIP, and Hi-C experiments. **Chr3D** provides a complete pipeline from raw FASTQ files to statistically significant chromatin loops and contact matrices.

## ✨ Recent Updates (v3.2.0)

- **🎯 Simplified CLI**: Single `chr3d run` command for complete pipeline execution
- **🔧 Three Analysis Modes**: ChIA-PET, HiChIP, and Hi-C support
- **💾 Smart File Management**: `--keep-intermediates` flag to control disk space usage
- **📦 Conda Package**: Easy installation via conda (coming to Bioconda)
- **🚀 Performance**: SIMD-accelerated linker filtering, parallel processing

## Features

- **Complete Pipeline**: From raw FASTQ to significant chromatin loops/matrices
- **Three Protocol Support**: ChIA-PET, HiChIP, and Hi-C analysis modes
- **Simple CLI**: One command runs the entire pipeline
- **Python API**: Use as a library in your scripts or Jupyter notebooks (see [PYTHON_API.md](PYTHON_API.md))
- **Statistical Rigor**: Hypergeometric test with FDR correction
- **High Performance**: SIMD-accelerated alignment (parasail), parallel processing
- **Modular Design**: Run individual steps or the complete pipeline

## Quick Start

### Installation

**Option 1: Conda (Recommended)**
```bash
# Coming soon to Bioconda
conda install -c bioconda chr3d
```

**Option 2: From Source**
```bash
git clone https://github.com/rudrajoshi2481/Chr3D.git
cd Chr3D
pip install -e .

# Install dependencies
conda install -c bioconda bwa samtools macs3 parasail-python
```

### Run Complete Pipeline

**ChIA-PET Analysis:**
```bash
chr3d run --mode chiapet \
    --fastq-r1 sample_R1.fastq.gz \
    --fastq-r2 sample_R2.fastq.gz \
    --genome-index /path/to/hg38.fa \
    --linker-a GTTGGATAAG \
    --linker-b GTTGGAATGT \
    --output-dir results/ \
    --threads 24
```

**HiChIP Analysis:**
```bash
chr3d run --mode hichip \
    --fastq-r1 sample_R1.fastq.gz \
    --fastq-r2 sample_R2.fastq.gz \
    --genome-index /path/to/hg38.fa \
    --linker-a GTTGGATAAG \
    --restriction-sites /path/to/MboI_sites.bed \
    --output-dir results/ \
    --threads 24
```

**Hi-C Analysis:**
```bash
chr3d run --mode hic \
    --fastq-r1 sample_R1.fastq.gz \
    --fastq-r2 sample_R2.fastq.gz \
    --genome-index /path/to/hg38.fa \
    --chrom-sizes /path/to/hg38.chrom.sizes \
    --output-dir results/ \
    --threads 24 \
    --resolution 1000,5000,10000
```

### Intermediate File Management

By default, Chr3D removes intermediate files to save disk space. Use `--keep-intermediates` to retain all files:

```bash
chr3d run --mode chiapet ... --keep-intermediates
```

**What gets removed by default:**
- Linker-filtered FASTQ files
- SAM files and unsorted BAM files
- Pre-clustering intermediate files

**What's always kept:**
- Final BEDPE files (iPET, sPET, oPET)
- Peak files (.narrowPeak)
- Loop files (FDR-filtered)
- Contact matrices (.cool, .mcool for Hi-C)

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| BWA | >= 0.7.17 | Genomic mapping |
| SAMtools | >= 1.10 | BAM/SAM processing |
| MACS3 | >= 3.0.0 | Peak calling |
| parasail | >= 1.3 | SIMD-accelerated alignment |
| pandas | >= 1.5 | Data manipulation |
| scipy | >= 1.10 | Statistical tests |

---

## Python API

Chr3D can also be used as a Python library for custom workflows. See **[PYTHON_API.md](PYTHON_API.md)** for detailed documentation.

**Quick Example:**
```python
import chr3d as c3d

# Linker filtering
filter = c3d.LinkerFilterV3(linker_a="GTTGGATAAG", n_threads=24)
stats = filter.filter_fastq("R1.fq.gz", "R2.fq.gz", "filtered", "output/")

# Mapping
mapper = c3d.PETMapper("/path/to/hg38.fa", n_threads=24)
mapper.map_linker_filtered_fastq("filtered.R1.fq", "filtered.R2.fq", "mapped", "output/")

# ... and more
```

**Available Classes:**
- `LinkerFilterV3` - SIMD-accelerated linker filtering
- `PETMapper` - BWA-based genomic mapping
- `ChIAPETPurifier` / `HiChIPPurifier` - Protocol-specific purification
- `PETCategorizer` - PET classification (iPET/sPET/oPET)
- `PeakCaller` - MACS3-based peak calling
- `PreClusterer`, `AnchorClusterer`, `StatisticalSignificance` - Loop calling
- `HiCPipeline` - Complete Hi-C analysis
- `RestrictionSiteGenerator` - Generate restriction fragments

---

## Output Files

| File | Description |
|------|-------------|
| `categorized.ipet` | Inter-ligation PETs (for loop calling) |
| `categorized.spet` | Self-ligation PETs (for peak calling) |
| `categorized.opet` | Other PETs (discarded) |
| `peaks_peaks.narrowPeak` | Called peaks (MACS3 format) |
| `loops.cluster.FDRfiltered.txt` | Significant chromatin loops (FDR < 0.05) |
| `sample.filtered.pairs.gz` | Filtered valid pairs (Hi-C) |
| `sample.mcool` | Multi-resolution contact matrix (Hi-C) |

---

## ChIA-PET vs HiChIP vs Hi-C

| Feature | ChIA-PET | HiChIP | Hi-C |
|---------|----------|--------|------|
| **Linker filtering** | ✅ Yes | ✅ Yes | ❌ No |
| **Protein-specific** | ✅ Yes | ✅ Yes | ❌ No |
| **Genome-wide** | ❌ No | ❌ No | ✅ Yes |
| **Self-ligation cutoff** | 8000 bp | 1000 bp | N/A |
| **Requires restriction sites** | ❌ No | ✅ Yes | ❌ No |
| **Output format** | BEDPE/Loops | BEDPE/Loops | .cool/.mcool |
| **Purifier class** | `ChIAPETPurifier` | `HiChIPPurifier` | N/A |

---

## Documentation

- **[PYTHON_API.md](PYTHON_API.md)** - Detailed Python API documentation with examples
- **[CONDA_PACKAGING.md](CONDA_PACKAGING.md)** - Guide for building and publishing conda packages
- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete API reference

---

## Citation

If you use Chr3D in your research, please cite:

```
Chr3D: A Comprehensive Python Framework for Chromatin Interactions Analysis
https://github.com/rudrajoshi2481/Chr3D
```

## License

MIT License

## References

- Li et al. (2010) ChIA-PET tool for comprehensive chromatin interaction analysis
- Fullwood et al. (2009) An oestrogen-receptor-α-bound human chromatin interactome
- Mumbach et al. (2016) HiChIP: efficient and sensitive analysis of protein-directed genome architecture
- Rao et al. (2014) A 3D map of the human genome at kilobase resolution
- 4DN Hi-C Processing Pipeline
