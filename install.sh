#!/bin/bash
set -e

echo "=========================================="
echo "Chr3D Pipeline Installation"
echo "=========================================="

echo "[1/6] Configuring conda channels..."
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge

echo "[2/6] Creating conda environment: chr3d-env (Python 3.12)..."
conda create -n chr3d-env python=3.12 -y

echo "[3/6] Activating environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate chr3d-env

echo "[4/6] Installing bioinformatics tools..."
conda install -c bioconda -y \
    bwa \
    samtools \
    macs3 \
    pairtools \
    cooler \
    cooltools

echo "[5/6] Installing Python dependencies..."
conda install -c conda-forge -y \
    numpy>=1.21.0 \
    pandas>=1.3.0 \
    scipy>=1.7.0 \
    biopython>=1.79 \
    pysam>=0.19.0 \
    tqdm>=4.62.0

conda install -c bioconda parasail-python -y

echo "[6/6] Installing Chr3D package..."
cd "$(dirname "$0")"
pip install -e .

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "To use Chr3D:"
echo "  1. Activate environment: conda activate chr3d-env"
echo "  2. Run pipeline: chr3d --help"
echo "  3. Or use Python API: import chr3d as c3d"
echo ""
echo "Installed tools:"
echo "  - BWA (alignment)"
echo "  - SAMtools (BAM processing)"
echo "  - MACS3 (peak calling)"
echo "  - pairtools (Hi-C pairs processing)"
echo "  - cooler (Hi-C matrix generation)"
echo "  - cooltools (Hi-C analysis)"
echo "  - parasail (SIMD-accelerated alignment)"
echo ""