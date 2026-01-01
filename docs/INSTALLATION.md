# Installation Guide

## Quick Install

```bash
# Clone repository
git clone https://github.com/rowan-pet/rowan-pet.git
cd rowan-pet

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
conda create -n rowan-pet python=3.10

# Activate
conda activate rowan-pet

# Install bioconda tools
conda install -c bioconda bwa samtools macs3 pairtools cooler

# Install Python dependencies
pip install parasail pandas scipy numpy tqdm biopython

# Install rowan-pet
pip install -e .
```

## Verify Installation

```python
import rowan_pet as rp

# Check version
print(f"Rowan-PET version: {rp.__version__}")

# List available classes
print("Available classes:")
for name in rp.__all__:
    print(f"  - rp.{name}")
```

Expected output:
```
Rowan-PET version: 3.1.0
Available classes:
  - rp.LinkerFilterV3
  - rp.PETMapper
  - rp.ChIAPETPurifier
  - rp.HiChIPPurifier
  - rp.PETCategorizer
  - rp.PeakCaller
  - rp.PreClusterer
  - rp.AnchorClusterer
  - rp.StatisticalSignificance
  - rp.RestrictionSiteGenerator
  - rp.BulkHiCPipeline
  - rp.HiCQCAnalyzer
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
