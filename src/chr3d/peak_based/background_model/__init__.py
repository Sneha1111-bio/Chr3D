# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
# This software was developed with support from the National Science Foundation under CAREER Award DBI-2239350.
"""
Background Model Subpackage for Loop Calling

Implements a statistical background model for identifying significant
chromatin loops from ChIA-PET and HiChIP BEDPE data.

Pipeline (input: BEDPE from mapping step):
    Step 1: classify_pets       - Classify PETs by peak overlap (P2P / P2D / D2D)
    Step 2: extract_templates   - Build templates from cross-peak P2P PETs
    Step 3: background_sampling_phase1 - Sample background, fit Negative Binomial
    Step 4: background_sampling_phase2 - Compute PMF p-values
    Step 5: apply_fdr_correction       - Multiple testing correction (BH, Bonferroni, etc.)

Compatible with both ChIA-PET and HiChIP pipelines.
Input requirement: deduplicated BEDPE file + MACS3 broadPeak file.

Example usage:
    from chr3d.peak_based.background_model import (
        load_peaks, classify_pets,
        extract_templates,
        run_background_sampling_phase1,
        calculate_pvalues,
        apply_fdr_corrections,
    )
"""

from .classify_pets import (
    load_peaks,
    classify_pets,
    check_overlap,
)

from .extract_templates import extract_templates

from .background_sampling_phase1 import (
    sample_template_background,
    fit_negative_binomial,
    BackgroundSamplingPhase1,
)

from .background_sampling_phase2 import (
    calculate_pmf_pvalue,
    calculate_pvalues,
)

from .apply_fdr_correction import apply_fdr_corrections

__all__ = [
    # Step 1: PET classification
    'load_peaks',
    'classify_pets',
    'check_overlap',

    # Step 2: Template extraction
    'extract_templates',

    # Step 3: Background sampling (NB parameter estimation)
    'sample_template_background',
    'fit_negative_binomial',
    'BackgroundSamplingPhase1',

    # Step 4: P-value calculation
    'calculate_pmf_pvalue',
    'calculate_pvalues',

    # Step 5: FDR correction
    'apply_fdr_corrections',
]
