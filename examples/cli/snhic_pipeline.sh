#!/bin/bash

# Single-Nucleus Hi-C Pipeline Example

# Basic Command (minimal required arguments)
# chr3d sn-hic \
#     --manifest /path/to/cells.tsv \
#     --genome /path/to/hg38.fa \
#     --chrom-sizes /path/to/hg38.chrom.sizes \
#     --output-dir ./snhic_results

# Advanced Command (with additional options)
# chr3d sn-hic \
#     --manifest /path/to/cells.tsv \
#     --genome /path/to/hg38.fa \
#     --chrom-sizes /path/to/hg38.chrom.sizes \
#     --output-dir ./snhic_results \
#     --threads 24 \
#     --min-contacts 5000 \
#     --resolutions 1000,5000,10000 \
#     --keep-intermediates \
#     --verbose

# Set input files
GENOME="/path/to/hg38.fa"
CHROM_SIZES="/path/to/hg38.chrom.sizes"
MANIFEST="/path/to/cells.tsv"
OUTPUT="./snhic_results"

# Run pipeline
chr3d sn-hic \
    --manifest "$MANIFEST" \
    --genome "$GENOME" \
    --chrom-sizes "$CHROM_SIZES" \
    --output-dir "$OUTPUT"
