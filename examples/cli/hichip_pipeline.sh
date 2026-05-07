#!/bin/bash

# HiChIP Pipeline Example

# Basic Command (minimal required arguments)
# chr3d hichip \
#     --r1 /path/to/sample_R1.fastq.gz \
#     --r2 /path/to/sample_R2.fastq.gz \
#     --genome /path/to/hg38.fa \
#     --fragments /path/to/mboi_fragments.bed \
#     --output-dir ./hichip_results

# Advanced Command (with additional options)
# chr3d hichip \
#     --r1 /path/to/sample_R1.fastq.gz \
#     --r2 /path/to/sample_R2.fastq.gz \
#     --genome /path/to/hg38.fa \
#     --fragments /path/to/mboi_fragments.bed \
#     --output-dir ./hichip_results \
#     --threads 48 \
#     --n-chunks 12 \
#     --min-insert 150 \
#     --background-samples 20000 \
#     --keep-intermediates \
#     --verbose

# Set input files
GENOME="/path/to/hg38.fa"
FRAGMENTS="/path/to/mboi_fragments.bed"
R1="/path/to/sample_R1.fastq.gz"
R2="/path/to/sample_R2.fastq.gz"
OUTPUT="./hichip_results"

# Run pipeline
chr3d hichip \
    --r1 "$R1" \
    --r2 "$R2" \
    --genome "$GENOME" \
    --fragments "$FRAGMENTS" \
    --output-dir "$OUTPUT"
