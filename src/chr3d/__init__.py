"""
Chr3D: Hi-C Chromatin Interaction Analysis Framework

Modules:
    Bulk Hi-C:
    - HiCAligner:        BWA MEM alignment
    - HiCSamProcessor:   SAM → sorted BAM (samtools)
    - HiCPairsProcessor: pairtools parse / sort / dedup / filter
    - HiCMatrixGenerator: cooler contact matrix generation
    - HiCPipeline:       Complete bulk Hi-C orchestrator

    Single-Nucleus Hi-C:
    - SnHiCPipeline:     Per-cell pipeline + pseudobulk aggregation

    Utilities:
    - FastqSplitter:            Split FASTQ for parallel alignment
    - RestrictionSiteGenerator: Generate restriction fragment sites
"""

__version__ = "3.2.0"
__author__ = "Chr3D Development Team"

# ============================================================================
# Hi-C Modules
# ============================================================================

from .hic import (
    FastqSplitter,
    HiCAligner,
    HiCSamProcessor,
    HiCPairsProcessor,
    HiCMatrixGenerator,
    HiCPipeline,
    HiCQCAnalyzer,
    SnHiCPipeline,
)

# ============================================================================
# Utilities
# ============================================================================

from .utils.restriction_sites import RestrictionSiteGenerator

__all__ = [
    '__version__',

    # ---- Bulk Hi-C ----
    'FastqSplitter',
    'HiCAligner',
    'HiCSamProcessor',
    'HiCPairsProcessor',
    'HiCMatrixGenerator',
    'HiCPipeline',
    'HiCQCAnalyzer',

    # ---- sn-Hi-C ----
    'SnHiCPipeline',

    # ---- Utilities ----
    'RestrictionSiteGenerator',
]
