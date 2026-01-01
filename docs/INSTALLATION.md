# Installation Guide

## Quick Install

```bash
# Clone repository
git clone https://github.com/rudrajoshi2481/Chr3D.git
cd Chr3D

# Install package
pip install -e .
```

## Dependencies

### Python Dependencies

Install via pip:
```bash
pip install parasail pandas scipy numpy tqdm biopython
```

### External Tools

#### For ChIA-PET / HiChIP Analysis

| Tool | Version | Installation |
|------|---------|--------------|
| BWA | >= 0.7.17 | `conda install -c bioconda bwa` |
| SAMtools | >= 1.10 | `conda install -c bioconda samtools` |
| MACS3 | >= 3.0.0 | `conda install -c bioconda macs3` |

#### For Bulk Hi-C Analysis

| Tool | Version | Installation |
|------|---------|--------------|
| BWA | >= 0.7.17 | `conda install -c bioconda bwa` |
| SAMtools | >= 1.10 | `conda install -c bioconda samtools` |
| pairtools | >= 1.0.0 | `conda install -c bioconda pairtools` |
| cooler | >= 0.9.0 | `conda install -c bioconda cooler` |

### Complete Conda Environment

Create a complete environment with all dependencies:

```bash
# Create environment
conda create -n chr3d python=3.10

# Activate
conda activate chr3d

# Install bioconda tools
conda install -c bioconda bwa samtools macs3 pairtools cooler

# Install Python dependencies
pip install parasail pandas scipy numpy tqdm biopython

# Install chr3d
pip install -e .
```

## Verify Installation

```python
import chr3d as c3d

# Check version
print(f"Chr3D version: {c3d.__version__}")

# List available classes
print("Available classes:")
for name in c3d.__all__:
    print(f"  - c3d.{name}")
```

Expected output:
```
Chr3D version: 3.2.0
Available classes:
  - c3d.LinkerFilterV3
  - c3d.PETMapper
  - c3d.ChIAPETPurifier
  - c3d.HiChIPPurifier
  - c3d.PETCategorizer
  - c3d.PeakCaller
  - c3d.PreClusterer
  - c3d.AnchorClusterer
  - c3d.StatisticalSignificance
  - c3d.RestrictionSiteGenerator
  - c3d.HiCPipeline
  - c3d.HiCQCAnalyzer
```

## Verify External Tools

```bash
# Check BWA
bwa 2>&1 | head -3

# Check SAMtools
samtools --version | head -1

# Check MACS3
macs3 --version

# Check pairtools (for Hi-C)
pairtools --version

# Check cooler (for Hi-C)
cooler --version
```

## Troubleshooting

### parasail not found
```bash
pip install parasail
```

### BWA index not found
```bash
# Create BWA index
bwa index -p hg38 hg38.fa
```

### Chromosome sizes file
```bash
# Generate from FASTA
samtools faidx hg38.fa
cut -f1,2 hg38.fa.fai > hg38.chrom.sizes
```
