#!/bin/bash

# ChIA-PET Pipeline Example

# Basic Command (minimal required arguments)
# chr3d chia-pet \
#     --r1 /path/to/sample_R1.fastq.gz \
#     --r2 /path/to/sample_R2.fastq.gz \
#     --genome /path/to/hg38.fa \
#     --linkers ACGCGATATCGCG \
#     --output-dir ./chiapet_results

# Advanced Command (with additional options)
# chr3d chia-pet \
#     --r1 /path/to/sample_R1.fastq.gz \
#     --r2 /path/to/sample_R2.fastq.gz \
#     --genome /path/to/hg38.fa \
#     --linkers ACGCGATATCGCG \
#     --output-dir ./chiapet_results \
#     --threads 24 \
#     --mapq 30 \
#     --genome-size hs \
#     --standard-chroms \
#     --keep-intermediates \
#     --verbose

# Set input files
GENOME="/path/to/hg38.fa"
R1="/path/to/sample_R1.fastq.gz"
R2="/path/to/sample_R2.fastq.gz"
LINKERS="ACGCGATATCGCG"
OUTPUT="./chiapet_results"

# Run pipeline
chr3d chia-pet \
    --r1 "$R1" \
    --r2 "$R2" \
    --genome "$GENOME" \
    --linkers "$LINKERS" \
    --output-dir "$OUTPUT"
