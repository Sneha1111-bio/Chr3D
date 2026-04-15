# Chr3D Command Reference

## Installation (after bioconda submission)

```bash
# Install with all dependencies (recommended)
conda install -c bioconda -c conda-forge chr3d

# Create new environment with chr3d
conda create -n chr3d-env -c bioconda -c conda-forge chr3d
conda activate chr3d-env

# Install into current environment
conda install -c bioconda -c conda-forge chr3d
```

---

## 1. Bulk Hi-C Pipeline (single sample)

### Basic command
```bash
chr3d bulk-hic \
  --r1 sample_R1.fastq.gz \
  --r2 sample_R2.fastq.gz \
  --genome /path/to/hg38.fa \
  --chrom-sizes /path/to/hg38.chrom.sizes \
  --output-dir ./results/my_sample \
  --sample-id my_sample
```

### All parameters with descriptions
```bash
chr3d bulk-hic \
  --r1 sample_R1.fastq.gz \              # R1 FASTQ file (required)
  --r2 sample_R2.fastq.gz \              # R2 FASTQ file (required)
  --genome /path/to/hg38.fa \             # BWA-indexed genome FASTA (required)
  --chrom-sizes /path/to/hg38.chrom.sizes \ # Chromosome sizes file (required)
  --output-dir ./results/my_sample \      # Output directory (required)
  --sample-id my_sample \                 # Sample identifier (default: sample)
  --threads 24 \                          # Total CPU threads (default: 24)
  --splits 6 \                            # Number of parallel chunks (default: 6)
  --assembly hg38 \                       # Genome assembly name (default: hg38)
  --min-mapq 30 \                         # Minimum MAPQ quality (default: 30)
  --min-distance 1000 \                   # Minimum insert distance bp (default: 1000)
  --resolutions 5000,10000,25000,50000,100000,250000,500000 \ # Matrix resolutions
  --loop-fdr 0.1 \                        # Loop FDR threshold (default: 0.1)
  --tad-windows 500000,1000000,2000000 \  # TAD window sizes (default: auto)
  --no-tads \                             # SKIP: TAD calling
  --no-loops \                            # SKIP: Loop calling
  --no-compartments \                     # SKIP: A/B compartment analysis
  --keep-intermediates \                  # Keep intermediate files
  --enzyme HindIII \                      # Restriction enzyme for fragment analysis
  --fragment-bed /path/to/fragments.bed \ # Pre-computed fragment BED
  --compartment-phasing-track /path/to/phasing.bed \ # Phasing track for compartments
  -v \                                   # Verbose logging
  --log-file analysis.log                 # Log file path
```

### Parameters you can skip (optional)
```bash
# Sample metadata (can use defaults)
--sample-id my_sample                     # Default: sample
--assembly hg38                          # Default: hg38

# Performance tuning (can use defaults)
--threads 24                            # Default: 24
--splits 6                              # Default: 6
--min-mapq 30                           # Default: 30
--min-distance 1000                     # Default: 1000

# Analysis options (can use defaults)
--resolutions 5000,10000,25000,50000,100000,250000,500000  # Default set
--loop-fdr 0.1                          # Default: 0.1
--tad-windows 500000,1000000,2000000    # Default: auto

# Skip specific analyses (optional flags)
--no-tads                               # Skip TAD calling
--no-loops                              # Skip loop calling
--no-compartments                       # Skip compartment analysis

# Advanced options (optional)
--keep-intermediates                    # Keep temporary files
--enzyme HindIII                        # For fragment analysis
--fragment-bed /path/to/fragments.bed  # Pre-computed fragments
--compartment-phasing-track /path/to/phasing.bed  # For compartment orientation

# Logging (optional)
-v                                      # Verbose output
--log-file analysis.log                 # Write log to file
```

---

## 2. Single-Nucleus Hi-C Pipeline (multiple cells)

### Basic command
```bash
chr3d sn-hic \
  --manifest cells.tsv \
  --genome /path/to/hg38.fa \
  --chrom-sizes /path/to/hg38.chrom.sizes \
  --output-dir ./results/sn_hic
```

### All parameters with descriptions
```bash
chr3d sn-hic \
  --manifest cells.tsv \                 # Cell manifest file (required)
  --genome /path/to/hg38.fa \            # BWA-indexed genome FASTA (required)
  --chrom-sizes /path/to/hg38.chrom.sizes \ # Chromosome sizes file (required)
  --output-dir ./results/sn_hic \        # Output directory (required)
  --threads 24 \                         # Total CPU threads (default: 24)
  --min-contacts 1000 \                   # Min contacts per cell (default: 1000)
  --loop-fdr 0.1 \                        # Loop FDR threshold (default: 0.1)
  --keep-intermediates \                  # Keep intermediate files
  -v \                                   # Verbose logging
  --log-file sn_hic.log                  # Log file path
```

### Parameters you can skip (optional)
```bash
--threads 24                            # Default: 24
--min-contacts 1000                     # Default: 1000
--loop-fdr 0.1                          # Default: 0.1
--keep-intermediates                    # Keep temporary files
-v                                      # Verbose output
--log-file sn_hic.log                   # Write log to file
```

---

## 3. ChIA-PET Pipeline

### Basic command
```bash
chr3d chia-pet \
  --r1 sample_R1.fastq.gz \
  --r2 sample_R2.fastq.gz \
  --genome /path/to/hg38.fa \
  --linkers ACGCGATATCGCG \
  --output-dir ./results/chiapet \
  --sample-id my_sample
```

### All parameters with descriptions
```bash
chr3d chia-pet \
  --r1 sample_R1.fastq.gz \              # R1 FASTQ file (required)
  --r2 sample_R2.fastq.gz \              # R2 FASTQ file (required)
  --genome /path/to/hg38.fa \             # BWA-indexed genome FASTA (required)
  --linkers ACGCGATATCGCG \               # Linker sequences (required)
  --output-dir ./results/chiapet \       # Output directory (required)
  --sample-id my_sample \                 # Sample identifier (default: sample)
  --min-score 30 \                        # Minimum linker score (default: 30)
  --min-tag 5 \                           # Minimum tag count (default: 5)
  --max-tag 100000 \                      # Maximum tag count (default: 100000)
  --mapq 30 \                             # Minimum MAPQ quality (default: 30)
  --threads 24 \                          # Total CPU threads (default: 24)
  --genome-size 2920000000 \              # Genome size for peak calling (default: hg)
  --qvalue 0.01 \                         # Peak calling q-value (default: 0.01)
  --alpha 0.05 \                          # Loop calling alpha (default: 0.05)
  --standard-chroms \                     # Use standard chromosomes only
  -v \                                   # Verbose logging
  --log-file chiapet.log                  # Log file path
```

### Parameters you can skip (optional)
```bash
--sample-id my_sample                    # Default: sample
--min-score 30                          # Default: 30
--min-tag 5                             # Default: 5
--max-tag 100000                        # Default: 100000
--mapq 30                               # Default: 30
--threads 24                           # Default: 24
--genome-size 2920000000                # Default: human genome
--qvalue 0.01                           # Default: 0.01
--alpha 0.05                            # Default: 0.05
--standard-chroms                       # Use standard chromosomes only
-v                                      # Verbose output
--log-file chiapet.log                  # Write log to file
```

---

## 4. HiChIP Pipeline

### Basic command
```bash
chr3d hichip \
  --r1 sample_R1.fastq.gz \
  --r2 sample_R2.fastq.gz \
  --genome /path/to/hg38.fa \
  --fragments /path/to/hg38_MboI_fragments.bed \
  --output-dir ./results/hichip \
  --sample-id my_sample
```

### All parameters with descriptions
```bash
chr3d hichip \
  --r1 sample_R1.fastq.gz \              # R1 FASTQ file (required)
  --r2 sample_R2.fastq.gz \              # R2 FASTQ file (required)
  --genome /path/to/hg38.fa \             # BWA-indexed genome FASTA (required)
  --fragments /path/to/hg38_MboI_fragments.bed \ # Fragment BED (required)
  --output-dir ./results/hichip \         # Output directory (required)
  --sample-id my_sample \                 # Sample identifier (default: sample)
  --threads 24 \                          # Total CPU threads (default: 24)
  --n-chunks 6 \                           # Parallel BWA jobs (default: 6)
  --min-insert 100 \                      # Min insert size bp (default: 100)
  --keep-intermediates \                  # Keep per-chunk files
  -v \                                   # Verbose logging
  --log-file hichip.log                   # Log file path
```

### Parameters you can skip (optional)
```bash
--sample-id my_sample                    # Default: sample
--threads 24                           # Default: 24
--n-chunks 6                           # Default: 6
--min-insert 100                       # Default: 100
--keep-intermediates                    # Keep temporary files
-v                                      # Verbose output
--log-file hichip.log                   # Write log to file
```

---

## 5. Restriction Fragment Digest

### Basic command
```bash
chr3d digest \
  --genome /path/to/hg38.fa \
  --enzyme MboI \
  --output hg38_MboI_fragments.bed
```

### All parameters with descriptions
```bash
chr3d digest \
  --genome /path/to/hg38.fa \            # Genome FASTA file (required)
  --enzyme MboI \                         # Enzyme name or site (required)
  --output hg38_MboI_fragments.bed \      # Output BED file (required)
  --min-size 20 \                         # Minimum fragment size bp (default: 20)
  --max-size 10000000 \                   # Maximum fragment size bp (default: 10M)
  -v \                                   # Verbose logging
  --log-file digest.log                   # Log file path
```

### Parameters you can skip (optional)
```bash
--min-size 20                          # Default: 20 bp
--max-size 10000000                    # Default: 10M bp
-v                                      # Verbose output
--log-file digest.log                   # Write log to file
```

### Supported enzymes
```
HindIII, DpnII, MboI, BglII, Sau3AI, Hinf1, NlaIII, AluI, EcoRI, BamHI, PstI, SalI, XbaI
```

### Dual enzyme (Arima Hi-C)
```bash
chr3d digest \
  --genome /path/to/hg38.fa \
  --enzyme MboI \
  --enzyme GATC^ \
  --output arima_fragments.bed
```

---

## Quick Start Examples

### Bulk Hi-C (minimal)
```bash
chr3d bulk-hic \
  --r1 sample_R1.fastq.gz \
  --r2 sample_R2.fastq.gz \
  --genome hg38.fa \
  --chrom-sizes hg38.chrom.sizes \
  --output-dir ./results
```

### HiChIP (minimal)
```bash
# First generate fragments
chr3d digest --genome hg38.fa --enzyme MboI --output hg38_MboI.bed

# Then run HiChIP
chr3d hichip \
  --r1 sample_R1.fastq.gz \
  --r2 sample_R2.fastq.gz \
  --genome hg38.fa \
  --fragments hg38_MboI.bed \
  --output-dir ./results
```

### ChIA-PET (minimal)
```bash
chr3d chia-pet \
  --r1 sample_R1.fastq.gz \
  --r2 sample_R2.fastq.gz \
  --genome hg38.fa \
  --linkers ACGCGATATCGCG \
  --output-dir ./results
```

---

## Output Directory Structures

### Bulk Hi-C
```
output_dir/
|-- cool/          # Contact matrices (.cool files)
|-- mcool/         # Multi-resolution matrix
|-- tads/          # TAD boundaries (.bed)
|-- loops/         # Loop calls (.bedpe)
|-- compartments/  # A/B compartments (.bed)
|-- aligned/       # BAM files
|-- pairs/         # Pair files
`-- qc/           # Quality reports
```

### HiChIP
```
output_dir/
|-- splits/        # FASTQ chunks (removed)
|-- aligned/       # Merged BAM
|-- bedpe/         # Raw & dedup BEDPE
|-- purified/      # MboI-filtered PETs
|-- background/    # Randomised background
`-- qc/           # Quality reports
```

### ChIA-PET
```
output_dir/
|-- filtered/      # Linker-filtered FASTQ
|-- mapped/        # BAM, BEDPE files
|-- peaks/         # MACS3 peaks
|-- loops/         # Loop results
`-- qc/           # Quality reports
```

---

## Performance Tips

### For large datasets (>100M reads)
```bash
# Increase parallelism
chr3d bulk-hic --threads 48 --splits 12 ...

# For HiChIP
chr3d hichip --threads 48 --n-chunks 12 ...
```

### For quick testing
```bash
# Use subset of data
chr3d bulk-hic --threads 8 --splits 2 ...

# Skip time-consuming analyses
chr3d bulk-hic --no-tads --no-compartments ...
```

---

## Troubleshooting

### Common issues
- **Missing BWA index**: Run `bwa index genome.fa` first
- **Memory issues**: Reduce `--threads` or `--splits`
- **Permission errors**: Ensure write access to `--output-dir`
- **Missing dependencies**: Install with `conda install -c bioconda -c conda-forge chr3d`

### Getting help
```bash
chr3d --help                    # General help
chr3d bulk-hic --help         # Bulk Hi-C help
chr3d hichip --help           # HiChIP help
chr3d chia-pet --help         # ChIA-PET help
chr3d digest --help           # Digest help
```
