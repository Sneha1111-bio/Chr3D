"""
Chr3D Peak-Based Analysis Subpackage

Contains modules for peak-based chromatin interaction analysis,
shared between ChIA-PET and HiChIP pipelines.

Modules:
    mapping            - BWA-based read alignment (PETMapperV3)
    background_model   - Loop calling via background statistical model:
                           classify_pets       - PET classification (P2P/P2D/D2D)
                           extract_templates   - Template extraction from P2P PETs
                           background_sampling_phase1 - NB parameter estimation
                           background_sampling_phase2 - PMF p-value calculation
                           apply_fdr_correction       - Multiple testing correction
"""

from .mapping import PETMapperV3

__all__ = [
    'PETMapperV3',
]
