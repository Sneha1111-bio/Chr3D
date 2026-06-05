# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
"""Chr3D — sn-Hi-C clustering subpackage.

Two-step pipeline:
  1. preprocessing.py    : raw contacts -> cell × bin matrix (coverage + log10 quantised)
  2. gnn_clustering.py   : matrix -> GraphSAGE embeddings -> Leiden clusters
"""

from .preprocessing import (
    parse_resolution,
    load_chrom_sizes,
    build_bin_layout,
    coverage_normalize_and_log10,
    preprocess_text,
    preprocess_mcool,
)

__all__ = [
    'parse_resolution',
    'load_chrom_sizes',
    'build_bin_layout',
    'coverage_normalize_and_log10',
    'preprocess_text',
    'preprocess_mcool',
]
