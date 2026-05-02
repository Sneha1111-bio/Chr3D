#!/bin/bash
set -e

echo "=========================================="
echo "Chr3D Pipeline Installation"
echo "=========================================="

ENV_NAME="trial02"

echo "[1/7] Configuring conda channels..."
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge

echo "[2/7] Creating conda environment: $ENV_NAME (Python 3.12)..."
conda create -n $ENV_NAME python=3.12 -y

echo "[3/7] Activating environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate $ENV_NAME

echo "[4/7] Installing bioinformatics tools..."
conda install -c bioconda -y \
    bwa \
    samtools \
    macs3 \
    pairtools \
    cooler \
    cooltools

echo "[5/7] Installing Python dependencies..."
conda install -c conda-forge -y \
    numpy>=1.21.0 \
    pandas>=1.3.0 \
    scipy>=1.7.0 \
    biopython>=1.79 \
    pysam>=0.19.0 \
    tqdm>=4.62.0 \
    statsmodels \
    polars

conda install -c bioconda parasail-python -y

echo "[6/7] Installing additional Python packages (pip)..."
pip install clodius

echo "[7/7] Installing Chr3D package (editable mode)..."
cd "$(dirname "$0")"
pip install -e .

echo ""
echo "Verifying installation..."
$CONDA_PREFIX/bin/python -c "
import chr3d as c3d
print(f'  chr3d version: {c3d.__version__}')
print(f'  Available: {\", \".join([x for x in dir(c3d) if not x.startswith(\"_\")])}')
" && echo "  ✓ Chr3D package installed successfully" || echo "  ✗ Chr3D package installation FAILED"

# Verify external tools
echo ""
echo "Verifying external tools..."
for tool in bwa samtools macs3 pairtools cooler cooltools; do
    if command -v $tool &> /dev/null; then
        echo "  ✓ $tool"
    else
        echo "  ✗ $tool not found"
    fi
done

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "To use Chr3D:"
echo "  1. Activate environment: conda activate $ENV_NAME"
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
echo "  - clodius (HiGlass tileset generation)"
echo "  - polars (fast DataFrames for loops_to_beddb)"
echo ""