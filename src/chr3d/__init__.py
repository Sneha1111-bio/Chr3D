# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
"""
Chr3D: Chromatin Interaction Analysis Framework

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

__version__ = "1.0.0"
__author__ = "Rudhra Joshi"

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
# Utilities (convenience functions + classes)
# ============================================================================

from .utils import (
    restriction_site_generator,
    loops_to_beddb,
    detect_restriction_enzyme,
    RestrictionSiteGenerator,
)

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

    # ---- Utilities (functions) ----
    'restriction_site_generator',
    'loops_to_beddb',
    'detect_restriction_enzyme',

    # ---- Utilities (classes) ----
    'RestrictionSiteGenerator',
]
