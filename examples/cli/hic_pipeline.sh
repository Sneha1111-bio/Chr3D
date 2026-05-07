#!/bin/bash

# Hi-C Pipeline Example

# Basic Command (minimal required arguments)
# chr3d bulk-hic \
#     --r1 /path/to/sample_R1.fastq.gz \
#     --r2 /path/to/sample_R2.fastq.gz \
#     --genome /path/to/hg38.fa \
#     --chrom-sizes /path/to/hg38.chrom.sizes \
#     --output-dir ./hic_results

# Advanced Command (with additional options)
# chr3d bulk-hic \
#     --r1 /path/to/sample_R1.fastq.gz \
#     --r2 /path/to/sample_R2.fastq.gz \
#     --genome /path/to/hg38.fa \
#     --chrom-sizes /path/to/hg38.chrom.sizes \
#     --output-dir ./hic_results \
#     --restriction-enzyme MboI \
#     --threads 24 \
#     --resolutions 1000,5000,10000,25000 \
#     --keep-intermediates \
#     --verbose

# Set input files
GENOME="/path/to/hg38.fa"
CHROM_SIZES="/path/to/hg38.chrom.sizes"
R1="/path/to/sample_R1.fastq.gz"
R2="/path/to/sample_R2.fastq.gz"
OUTPUT="./hic_results"

# Run pipeline
chr3d bulk-hic \
    --r1 "$R1" \
    --r2 "$R2" \
    --genome "$GENOME" \
    --chrom-sizes "$CHROM_SIZES" \
    --output-dir "$OUTPUT"
