"""
Chr3D: A Comprehensive Python Framework for Chromatin Interactions Analysis

A comprehensive Python pipeline for analyzing chromatin interaction data
from ChIA-PET, HiChIP, and Hi-C experiments.

Modules:
    ChIA-PET / HiChIP:
    - LinkerFilterV3: Linker filtering with parasail SIMD
    - PETMapper: Genomic mapping with BWA
    - ChIAPETPurifier: ChIA-PET deduplication and merging
    - HiChIPPurifier: HiChIP same-fragment removal
    - PETCategorizer: PET classification (iPET/sPET/oPET)
    - PeakCaller: Peak calling with MACS3
    - PreClusterer, AnchorClusterer, StatisticalSignificance: Loop calling
    
    Hi-C (modular classes for each step):
    - FastqSplitter: Split FASTQ files for parallel processing
    - HiCAligner: BWA MEM alignment for Hi-C
    - HiCSamProcessor: SAM to BAM conversion
    - HiCPairsProcessor: pairtools parse/sort/dedup/filter
    - HiCMatrixGenerator: cooler matrix generation
    - HiCPipeline: Complete pipeline orchestrator
    - HiCQCAnalyzer: Quality control analysis
    
    Utilities:
    - RestrictionSiteGenerator: Generate restriction fragments
"""

__version__ = "3.2.0"
__author__ = "Chr3D Development Team"

# ============================================================================
# ChIA-PET / HiChIP Modules
# ============================================================================

# Step 1: Linker Filtering
from .linker_filtering_v3 import LinkerFilterV3

# Step 2: Mapping
from .mapping_v2 import PETMapper

# Step 3: Purifying
from .chiapet_purifying import ChIAPETPurifier
from .hichip_purifying import HiChIPPurifier

# Step 4: PET Categorization
from .pet_categorization import PETCategorizer

# Step 5: Peak Calling
from .peak_calling import PeakCaller

# Step 6: Loop Calling
from .loop_calling import PreClusterer, AnchorClusterer, StatisticalSignificance

# ============================================================================
# Hi-C Modules (modular step-by-step classes)
# ============================================================================

from .bulk_hic import (
    # Utility
    FastqSplitter,
    # Step 1: Alignment
    HiCAligner,
    # Step 2: SAM/BAM Processing
    HiCSamProcessor,
    # Step 3: Pairs Processing
    HiCPairsProcessor,
    # Step 4: Matrix Generation
    HiCMatrixGenerator,
    # Complete Pipeline
    HiCPipeline,
    # QC Analysis
    HiCQCAnalyzer,
)

# Backward compatibility alias
BulkHiCPipeline = HiCPipeline

# ============================================================================
# Utilities
# ============================================================================

from .restriction_sites import RestrictionSiteGenerator

__all__ = [
    # Version
    '__version__',
    
    # ---- ChIA-PET / HiChIP ----
    'LinkerFilterV3',
    'PETMapper',
    'ChIAPETPurifier',
    'HiChIPPurifier',
    'PETCategorizer',
    'PeakCaller',
    'PreClusterer',
    'AnchorClusterer',
    'StatisticalSignificance',
    
    # ---- Hi-C (modular) ----
    'FastqSplitter',
    'HiCAligner',
    'HiCSamProcessor',
    'HiCPairsProcessor',
    'HiCMatrixGenerator',
    'HiCPipeline',
    'HiCQCAnalyzer',
    
    # Backward compatibility
    'BulkHiCPipeline',
    
    # ---- Utilities ----
    'RestrictionSiteGenerator',
]
