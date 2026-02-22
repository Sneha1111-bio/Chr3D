#!/bin/bash
# Example script to run ChIA-PET linker filtering on SRR2312566
# Reproduces the results from Li et al. 2019 (Genes) with corrected parameters

# Set paths (adjust these for your system)
R1_FASTQ="/path/to/SRR2312566_1.fastq"
R2_FASTQ="/path/to/SRR2312566_2.fastq"
OUTPUT_DIR="./data/linker_filter_output"
OUTPUT_PREFIX="SRR2312566_full"
THREADS=50
CHUNKS=50

# Linker sequences (ACGCGATATCTTATCTGACT / AGTCAGATAAGATATCGCGT are reverse complements)
LINKER_A="ACGCGATATCTTATCTGACT"
LINKER_B="AGTCAGATAAGATATCGCGT"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run linker filtering with corrected parameters
python Chr3D/src/chr3d/linker_filtering_v3.py \
  --r1 "$R1_FASTQ" \
  --r2 "$R2_FASTQ" \
  --linker-a "$LINKER_A" \
  --linker-b "$LINKER_B" \
  --output-prefix "$OUTPUT_PREFIX" \
  --output-dir "$OUTPUT_DIR" \
  --threads "$THREADS" \
  --chunks "$CHUNKS" \
  --min-score 14 \
  --min-tag 18 \
  --max-tag 1000 \
  --min-diff 4 \
  --match 1 \
  --mismatch 1 \
  --gap-open 1 \
  --gap-extend 1 \
  --keep-chunks

echo "Linker filtering complete. Output files in $OUTPUT_DIR"
echo "Expected results: ~341M same-linker PETs (50.13% of total reads)"
