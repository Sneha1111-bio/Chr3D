# Changelog

All notable changes to Rowan-PET will be documented in this file.

## [3.1.0] - 2024-12-16

### Added
- **Bulk Hi-C Pipeline** (`BulkHiCPipeline`) - Complete Hi-C analysis from FASTQ to .cool/.mcool
  - BWA MEM alignment with Hi-C specific parameters (-SP5M)
  - SAM/BAM processing with samtools
  - Pairs processing with pairtools (parse, sort, dedup, filter)
  - Contact matrix generation with cooler (balance, zoomify)
- **Hi-C QC Analyzer** (`HiCQCAnalyzer`) - Parse and summarize Hi-C QC metrics
- Integrated rowan-hic functionality into rowan-pet package

### Changed
- Updated version to 3.1.0
- Updated README with comprehensive Hi-C Python API documentation
- Added protocol comparison table (ChIA-PET vs HiChIP vs Bulk Hi-C)

## [3.0.0] - 2024-12-16

### Added
- **Statistical Significance** (`StatisticalSignificance`) - FDR-corrected loop significance
- Hypergeometric test for chromatin loop enrichment
- Benjamini-Hochberg FDR correction

### Changed
- Reorganized package structure for cleaner API
- Removed deprecated linker_filtering_v1 and v2 modules
- Updated to use LinkerFilterV3 with parasail SIMD acceleration

### Fixed
- Edge case handling in loop_calling.py for empty results
- Division by zero when no clusters pass iPET count filter

## [2.0.0] - 2024-12-15

### Added
- **Parallel chunk-based mapping** in PETMapper
- Support for mapping all 4 linker combinations (1_1, 1_2, 2_1, 2_2)
- BEDPE-level merging and deduplication

### Changed
- Switched default aligner to BWA-ALN for short reads
- Added mapping_quality_cutoff parameter

## [1.0.0] - Initial Release

### Added
- LinkerFilterV3 with parasail SIMD acceleration
- PETMapper with BWA-MEM and BWA-ALN support
- ChIAPETPurifier for deduplication and merging
- HiChIPPurifier for same-fragment removal
- PETCategorizer for iPET/sPET/oPET classification
- PeakCaller with MACS3 integration
- PreClusterer and AnchorClusterer for loop calling
- RestrictionSiteGenerator utility
