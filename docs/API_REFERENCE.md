# Chr3D API Reference

Complete API documentation for all Chr3D classes and methods.

**Version: 3.2.0**

---

## Quick Reference: Which Class for Which Protocol?

| Class | ChIA-PET | HiChIP | Hi-C | Step | Description |
|-------|:--------:|:------:|:----:|------|-------------|
| `LinkerFilterV3` | ✅ | ❌ | ❌ | 1 | Linker filtering (ChIA-PET only) |
| `PETMapper` | ✅ | ✅ | ❌ | 2/1 | BWA mapping |
| `ChIAPETPurifier` | ✅ | ❌ | ❌ | 3 | Dedup + merge |
| `HiChIPPurifier` | ❌ | ✅ | ❌ | 2 | Same-fragment removal (biotin artifacts) |
| `PETCategorizer` | ✅ | ✅ | ❌ | 4/3 | iPET/sPET/oPET |
| `PeakCaller` | ✅ | ✅ | ❌ | 5/4 | MACS3 peaks |
| `PreClusterer` | ✅ | ✅ | ❌ | 6a/5a | Loop pre-clustering |
| `AnchorClusterer` | ✅ | ✅ | ❌ | 6b/5b | Anchor merging |
| `StatisticalSignificance` | ✅ | ✅ | ❌ | 6c/5c | FDR filtering |
| `FastqSplitter` | ❌ | ❌ | ✅ | 0 | Split FASTQ |
| `HiCAligner` | ❌ | ❌ | ✅ | 1 | BWA MEM (-SP5M) |
| `HiCSamProcessor` | ❌ | ❌ | ✅ | 2 | SAM → BAM |
| `HiCPairsProcessor` | ❌ | ❌ | ✅ | 3 | pairtools |
| `HiCMatrixGenerator` | ❌ | ❌ | ✅ | 4 | cooler matrix |
| `HiCPipeline` | ❌ | ❌ | ✅ | ALL | Complete pipeline |
| `HiCQCAnalyzer` | ❌ | ❌ | ✅ | QC | QC analysis |
| `RestrictionSiteGenerator` | ❌ | ✅ | ⚠️ | Util | RE sites (RE-based protocols only) |

> **Note:** HiChIP does NOT use linker filtering. It uses standard *in situ* Hi-C chemistry with biotin-dATP fill-in at restriction sites, not synthetic bridge linkers. The step numbers show ChIA-PET/HiChIP order.

> **Note:** For bridge-linker Hi-C variants (BL-Hi-C), linker filtering may be required - see protocol-specific documentation.

---

## Workflow Diagrams

### ChIA-PET Workflow (6 steps)
```
FASTQ → [1] LinkerFilterV3 → [2] PETMapper → [3] ChIAPETPurifier → [4] PETCategorizer → [5] PeakCaller → [6] Loop Calling
```

### HiChIP Workflow (5 steps - NO linker filtering)
```
FASTQ → [1] PETMapper → [2] HiChIPPurifier → [3] PETCategorizer → [4] PeakCaller → [5] Loop Calling
```

### Hi-C Workflow (4 steps)
```
FASTQ → [1] HiCAligner → [2] HiCSamProcessor → [3] HiCPairsProcessor → [4] HiCMatrixGenerator
```

---

## Table of Contents

- [ChIA-PET Pipeline](#chia-pet-pipeline)
  - [Step 1: LinkerFilterV3](#step-1-linkerfilterv3) - Linker filtering (ChIA-PET ONLY)
  - [Step 2: PETMapper](#step-2-petmapper) - BWA mapping
  - [Step 3: ChIAPETPurifier](#step-3a-chiapetpurifier) - Dedup + merge
  - [Step 4: PETCategorizer](#step-4-petcategorizer) - PET classification
  - [Step 5: PeakCaller](#step-5-peakcaller) - MACS3 peaks
  - [Step 6: Loop Calling](#step-6-loop-calling) - PreClusterer, AnchorClusterer, StatisticalSignificance
- [HiChIP Pipeline](#hichip-pipeline)
  - [Step 1: PETMapper](#step-2-petmapper) - BWA mapping (START HERE)
  - [Step 2: HiChIPPurifier](#step-3b-hichippurifier) - Same-fragment removal
  - [Step 3-5: Same as ChIA-PET Steps 4-6](#step-4-petcategorizer)
- [Hi-C Pipeline](#hi-c-pipeline)
  - [FastqSplitter](#fastqsplitter) - Split FASTQ (optional)
  - [HiCAligner](#hicaligner) - BWA MEM alignment
  - [HiCSamProcessor](#hicsamprocessor) - SAM/BAM processing
  - [HiCPairsProcessor](#hicpairsprocessor) - pairtools (parse/sort/dedup/filter)
  - [HiCMatrixGenerator](#hicmatrixgenerator) - cooler matrix generation
  - [HiCPipeline](#hicpipeline) - Complete pipeline
  - [HiCQCAnalyzer](#hicqcanalyzer) - QC analysis
- [Utilities](#utilities)
  - [RestrictionSiteGenerator](#restrictionsitegenerator)
- [Command Line Interface](#command-line-interface)
- [File Cleanup Guide](#file-cleanup-guide)

---

# ChIA-PET Pipeline

## Step 1: LinkerFilterV3

**Protocols:** ChIA-PET ✅ | HiChIP ❌ | Hi-C ❌

> ⚠️ **ChIA-PET ONLY:** HiChIP does NOT use linker filtering. HiChIP uses *in situ* Hi-C chemistry with biotin-dATP fill-in, not synthetic bridge linkers. If you're running HiChIP, skip to [PETMapper](#step-2-petmapper).

High-performance linker filtering with parasail SIMD acceleration.

```python
import chr3d as c3d

linker_filter = c3d.LinkerFilterV3(
    linker_a: str,                    # Linker A sequence (required)
    linker_b: str,                    # Linker B sequence (required)
    min_score_ratio: float = 0.7,     # Min alignment score ratio
    min_tag_length: int = 18,         # Min tag length after trimming
    max_tag_length: int = None,       # Max tag length (None = unlimited)
    n_threads: int = 1,               # Number of threads
    check_reverse_complement: bool = True  # Check reverse complement
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `filter_fastq(fastq_r1, fastq_r2, output_prefix, output_dir, ...)` | Filter paired FASTQ files |

---

## Step 2: PETMapper

**Protocols:** ChIA-PET ✅ | HiChIP ✅ | Hi-C ❌

Genomic mapping with BWA (MEM or ALN mode).

```python
mapper = c3d.PETMapper(
    genome_index: str,                # BWA-indexed genome (required)
    n_threads: int = 1,               # Number of threads
    use_bwa_mem: bool = True,         # True=BWA-MEM, False=BWA-ALN
    mapping_quality_cutoff: int = 30  # Minimum MAPQ
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `map_linker_filtered_fastq(r1_fastq, r2_fastq, output_prefix, ...)` | Map filtered FASTQ to genome |

---

## Step 3a: ChIAPETPurifier

**Protocols:** ChIA-PET ✅ | HiChIP ❌ | Hi-C ❌

ChIA-PET deduplication and PET merging.

```python
purifier = c3d.ChIAPETPurifier(
    merge_distance: int = 2,          # Max bp distance to merge
    min_mapq: int = 30                # Minimum mapping quality
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `purify(input_bedpe, output_prefix, output_dir)` | Deduplicate and merge PETs |

---

---

# HiChIP Pipeline

> **Important:** HiChIP starts at mapping (PETMapper), NOT linker filtering. HiChIP uses *in situ* Hi-C chemistry with biotin-dATP fill-in at restriction enzyme sites.

## Step 1 (HiChIP): PETMapper

See [PETMapper](#step-2-petmapper) above. For HiChIP, this is your **first step**.

## Step 2 (HiChIP): HiChIPPurifier

**Protocols:** ChIA-PET ❌ | HiChIP ✅ | Hi-C ❌

HiChIP same-fragment PET removal.

> **Why this step?** HiChIP uses biotin-dATP fill-in at restriction sites. Same-fragment PETs result from self-ligation artifacts where both ends of a DNA fragment ligate to each other instead of forming inter-fragment contacts. These must be removed for accurate interaction calling. (Mumbach et al., 2016)

```python
purifier = c3d.HiChIPPurifier(
    restriction_file: str,            # Restriction sites BED (required)
    min_insert_size: int = 1          # Min fragment skip distance
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `purify(input_bedpe, output_prefix, output_dir)` | Remove same-fragment PETs |

---

## Step 3 (HiChIP) / Step 4 (ChIA-PET): PETCategorizer

**Protocols:** ChIA-PET ✅ | HiChIP ✅ | Hi-C ❌

PET classification into iPET, sPET, and oPET.

```python
categorizer = c3d.PETCategorizer(
    mode: str = 'chiapet',            # 'chiapet' or 'hichip'
    self_ligation_cutoff: int = None  # None = use mode default
)
```

**Mode Defaults:**
- ChIA-PET: 8000 bp
- HiChIP: 1000 bp (Mumbach et al., 2016)

**Methods:**

| Method | Description |
|--------|-------------|
| `categorize(input_bedpe, output_prefix, output_dir)` | Categorize PETs |

---

## Step 4 (HiChIP) / Step 5 (ChIA-PET): PeakCaller

**Protocols:** ChIA-PET ✅ | HiChIP ✅ | Hi-C ❌

Peak calling with MACS3.

```python
peak_caller = c3d.PeakCaller(
    genome_size: str = 'hs',          # 'hs', 'mm', or integer
    qvalue_cutoff: float = 0.05,      # Q-value threshold
    keep_dup: str = '1',              # '1' or 'all'
    build_model: bool = True,         # Build MACS3 model
    macs3_path: str = 'macs3',        # MACS3 executable
    conda_env: str = None             # Conda environment
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `call_peaks_from_bedpe(bedpe_file, output_prefix, output_dir)` | Call peaks from sPETs |
| `bedpe_to_bed(bedpe_file, output_bed)` | Convert BEDPE to BED |

---

## Step 5 (HiChIP) / Step 6 (ChIA-PET): Loop Calling

**Protocols:** ChIA-PET ✅ | HiChIP ✅ | Hi-C ❌

Loop calling consists of three sub-steps using three classes.

### Step 6a: PreClusterer

Pre-clustering with tag extension for loop calling.

```python
pre_clusterer = c3d.PreClusterer(
    extension_length: int = 500,      # Tag extension in bp
    chrom_sizes_file: str = None      # Chromosome sizes file
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `pre_cluster(ipet_file, output_prefix)` | Create pre-clusters from iPETs |

---

### Step 6b: AnchorClusterer

Merge overlapping anchor clusters.

```python
anchor_clusterer = c3d.AnchorClusterer()
```

**Methods:**

| Method | Description |
|--------|-------------|
| `cluster_anchors(precluster_file, output_file)` | Merge overlapping clusters |

---

### Step 6c: StatisticalSignificance

FDR-corrected loop significance testing.

```python
stat_sig = c3d.StatisticalSignificance(
    ipet_count_threshold: int = 2,    # Min iPET count per loop
    pvalue_cutoff: float = 0.05,      # FDR threshold
    extension_length: int = 500       # Tag extension for counting
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `calculate_significance(cluster_file, ipet_file, output_prefix)` | Calculate loop significance |

---

# Hi-C Pipeline

**Protocols:** ChIA-PET ❌ | HiChIP ❌ | Hi-C ✅

The Hi-C module provides **modular classes** for each processing step. You can use them individually or combine them via `HiCPipeline`.

## Step 0 (Optional): FastqSplitter

Split large FASTQ files into chunks for parallel processing.

```python
splitter = c3d.FastqSplitter(
    n_chunks: int = 10,               # Number of chunks to create
    reads_per_chunk: int = None       # Reads per chunk (overrides n_chunks)
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `split(fastq1, fastq2, output_dir, prefix)` | Split paired FASTQ files into chunks |

**Example:**
```python
splitter = c3d.FastqSplitter(n_chunks=10)
chunks = splitter.split("R1.fastq.gz", "R2.fastq.gz", "split_dir/")
# Returns: [("chunk_000_R1.fastq", "chunk_000_R2.fastq"), ...]
```

---

## Step 1: HiCAligner

BWA MEM alignment with Hi-C specific parameters (-SP5M).

```python
aligner = c3d.HiCAligner(
    genome_index: str,                # BWA-indexed genome (required)
    threads: int = 1                  # Number of threads
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `align(fastq1, fastq2, output_sam, stats_file)` | Run BWA MEM alignment |

**Example:**
```python
aligner = c3d.HiCAligner("/path/to/hg38.fa", threads=24)
stats = aligner.align("R1.fastq.gz", "R2.fastq.gz", "aligned.sam")
```

---

## Step 2: HiCSamProcessor

SAM to BAM conversion and sorting (required for pairtools).

```python
processor = c3d.HiCSamProcessor(
    threads: int = 1                  # Number of threads
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `process(input_sam, output_bam, stats_file, keep_unsorted)` | Convert SAM to sorted BAM |

**Example:**
```python
processor = c3d.HiCSamProcessor(threads=24)
stats = processor.process("aligned.sam", "sorted.bam")
```

---

## Step 3: HiCPairsProcessor

pairtools processing with individual methods for each step.

```python
pairs = c3d.HiCPairsProcessor(
    chrom_sizes: str,                 # Chromosome sizes file (required)
    assembly: str = 'hg38',           # Genome assembly name
    threads: int = 1                  # Number of threads
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `parse(input_bam, output_pairs, stats_file)` | Convert BAM to pairs format |
| `sort(input_pairs, output_pairs, tmp_dir)` | Sort pairs by position |
| `dedup(input_pairs, output_pairs, stats_file)` | Remove PCR duplicates |
| `filter(input_pairs, output_pairs, pair_types)` | Filter valid pair types |
| `process_all(input_bam, output_dir, prefix, cleanup)` | Run all steps |

**Example - Individual Steps:**
```python
pairs = c3d.HiCPairsProcessor("/path/to/hg38.chrom.sizes", threads=24)

# Run each step individually
pairs.parse("sorted.bam", "parsed.pairs.gz")
pairs.sort("parsed.pairs.gz", "sorted.pairs.gz")
pairs.dedup("sorted.pairs.gz", "dedup.pairs.gz")
pairs.filter("dedup.pairs.gz", "filtered.pairs.gz", pair_types=['UU', 'UR', 'RU'])
```

**Example - All Steps:**
```python
pairs = c3d.HiCPairsProcessor("/path/to/hg38.chrom.sizes", threads=24)
stats = pairs.process_all("sorted.bam", "output_dir/", prefix="sample")
# Creates: sample.sorted.pairs.gz, sample.dedup.pairs.gz, sample.filtered.pairs.gz
```

---

## Step 4: HiCMatrixGenerator

Contact matrix generation using cooler.

```python
matrix = c3d.HiCMatrixGenerator(
    chrom_sizes: str,                 # Chromosome sizes file (required)
    assembly: str = 'hg38',           # Genome assembly name
    threads: int = 1                  # Number of threads
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `create(input_pairs, output_cool, resolution)` | Create .cool matrix |
| `balance(input_cool, max_iters, cis_only)` | Balance contact matrix |
| `zoomify(input_cool, output_mcool, resolutions)` | Create multi-resolution .mcool |

**Example:**
```python
matrix = c3d.HiCMatrixGenerator("/path/to/hg38.chrom.sizes", threads=24)

# Create matrix at 1kb resolution
matrix.create("filtered.pairs.gz", "sample.cool", resolution=1000)

# Balance the matrix
matrix.balance("sample.cool")

# Create multi-resolution file
matrix.zoomify("sample.cool", "sample.mcool", 
               resolutions=[1000, 5000, 10000, 25000, 50000, 100000])
```

---

## Complete Pipeline: HiCPipeline

Complete Hi-C pipeline orchestrator (combines all steps).

```python
hic = c3d.HiCPipeline(
    genome_index: str,                # BWA-indexed genome (required)
    chrom_sizes: str,                 # Chromosome sizes file (required)
    threads: int = 1,                 # Number of threads
    assembly: str = 'hg38',           # Genome assembly name
    min_mapq: int = 30,               # Minimum mapping quality
    min_distance: int = 1000,         # Minimum pair distance
    resolutions: list = [1000, 5000, 10000, 25000, 50000, 100000]
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `run(fastq1, fastq2, output_dir, sample_id, cleanup)` | Run complete pipeline |
| `align(fastq1, fastq2, output_dir, sample_id)` | Step 1: BWA MEM alignment |
| `process_sam(input_sam, output_dir, sample_id)` | Step 2: SAM/BAM processing |
| `process_pairs(input_bam, output_dir, sample_id)` | Step 3: Pairs processing |
| `create_contact_matrix(input_pairs, output_dir, sample_id)` | Step 4: Matrix generation |

**Example - Complete Pipeline:**
```python
hic = c3d.HiCPipeline(
    genome_index="/path/to/hg38.fa",
    chrom_sizes="/path/to/hg38.chrom.sizes",
    threads=24
)
stats = hic.run("R1.fastq.gz", "R2.fastq.gz", "results/", sample_id="sample1")
```

---

## QC: HiCQCAnalyzer

Hi-C quality control analysis.

```python
qc = c3d.HiCQCAnalyzer()
```

**Methods:**

| Method | Description |
|--------|-------------|
| `analyze(qc_dir, output_dir)` | Analyze all QC files |
| `parse_alignment_stats(stats_file)` | Parse samtools stats |
| `parse_pairs_stats(stats_file)` | Parse pairtools stats |

**Example:**
```python
qc = c3d.HiCQCAnalyzer()
stats = qc.analyze("results/qc", "results/summary")
```

---

## Utilities

### RestrictionSiteGenerator

Generate restriction fragments from genome.

```python
generator = c3d.RestrictionSiteGenerator(
    enzyme: str,                      # Enzyme name (e.g., 'MboI')
    recognition_site: str             # Recognition sequence (e.g., 'GATC')
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `generate(genome_fasta, output_file)` | Generate restriction sites |

**Protocols:** HiChIP ✅ | Hi-C ✅ (for restriction enzyme-based protocols)

---

# Command Line Interface

## ChIA-PET CLI

```bash
# Run complete ChIA-PET pipeline (with linker filtering)
chr3d run-chiapet \
    --fastq1 sample_R1.fastq.gz \
    --fastq2 sample_R2.fastq.gz \
    --genome-idx /path/to/hg38.fa \
    --linker-a GTTGGATAAG \
    --linker-b GTTGGAATGT \
    --threads 24 \
    --output-dir results/
```

## HiChIP CLI

> ⚠️ **Note:** HiChIP does NOT use linker filtering. No `--linker-a` or `--linker-b` flags.

```bash
# Run complete HiChIP pipeline (NO linker filtering)
chr3d run-hichip \
    --fastq1 sample_R1.fastq.gz \
    --fastq2 sample_R2.fastq.gz \
    --genome-idx /path/to/hg38.fa \
    --restriction-sites /path/to/MboI_sites.bed \
    --threads 24 \
    --output-dir results/
```

## Hi-C CLI

```bash
# Run complete Hi-C pipeline
rowan-pet run-hic \
    --fastq1 sample_R1.fastq.gz \
    --fastq2 sample_R2.fastq.gz \
    --genome-idx /path/to/hg38.fa \
    --chrom-sizes /path/to/hg38.chrom.sizes \
    --assembly hg38 \
    --threads 24 \
    --output-dir results/
```

## CLI Options Reference

| Option | Description | ChIA-PET | HiChIP | Hi-C |
|--------|-------------|:--------:|:------:|:----:|
| `--fastq1` | R1 FASTQ file | ✅ | ✅ | ✅ |
| `--fastq2` | R2 FASTQ file | ✅ | ✅ | ✅ |
| `--genome-idx` | BWA-indexed genome | ✅ | ✅ | ✅ |
| `--output-dir` | Output directory | ✅ | ✅ | ✅ |
| `--threads` | Number of threads | ✅ | ✅ | ✅ |
| `--linker-a` | Linker A sequence | ✅ | ❌ | ❌ |
| `--linker-b` | Linker B sequence | ✅ | ❌ | ❌ |
| `--restriction-sites` | Restriction sites BED | ❌ | ✅ | ❌ |
| `--chrom-sizes` | Chromosome sizes file | ❌ | ❌ | ✅ |
| `--assembly` | Genome assembly name | ❌ | ❌ | ✅ |

---

# File Cleanup Guide

## Which Files to Keep vs Delete

### Hi-C Intermediate Files

| File | Size | Keep? | Description |
|------|------|-------|-------------|
| `*.sam` | Very Large | ❌ Delete | Raw alignment (convert to BAM) |
| `*.unsorted.bam` | Large | ❌ Delete | Unsorted BAM |
| `*_sorted.bam` | Large | ⚠️ Optional | Sorted BAM (needed for re-processing) |
| `*.parsed.pairs.gz` | Medium | ❌ Delete | Parsed pairs (before sort) |
| `*.sorted.pairs.gz` | Medium | ⚠️ Optional | Sorted pairs |
| `*.dedup.pairs.gz` | Medium | ⚠️ Optional | Deduplicated pairs |
| `*.filtered.pairs.gz` | Medium | ✅ Keep | Final filtered pairs |
| `*.cool` | Small | ✅ Keep | Contact matrix |
| `*.mcool` | Small | ✅ Keep | Multi-resolution matrix |

### ChIA-PET / HiChIP Intermediate Files

| File | Size | Keep? | Description |
|------|------|-------|-------------|
| `*.sam` | Large | ❌ Delete | Raw alignment |
| `*.bam` | Large | ⚠️ Optional | BAM file |
| `*.bedpe` (raw) | Medium | ❌ Delete | Raw BEDPE |
| `*.purified.bedpe` | Medium | ⚠️ Optional | Purified BEDPE |
| `*.ipet` | Small | ✅ Keep | Inter-chromosomal PETs |
| `*.spet` | Small | ✅ Keep | Self-ligation PETs |
| `*_peaks.narrowPeak` | Small | ✅ Keep | Called peaks |
| `*.FDRfiltered.txt` | Small | ✅ Keep | Significant loops |

## Cleanup Functions

### Hi-C Cleanup

```python
import os
import glob

def cleanup_hic(output_dir: str, keep_bam: bool = False, keep_intermediate_pairs: bool = False):
    """
    Remove Hi-C intermediate files to save disk space.
    
    Args:
        output_dir: Pipeline output directory
        keep_bam: Keep sorted BAM file (default: False)
        keep_intermediate_pairs: Keep sorted/dedup pairs (default: False)
    """
    # Always delete
    for pattern in ['*.sam', '*.unsorted.bam', '*.parsed.pairs.gz']:
        for f in glob.glob(os.path.join(output_dir, '**', pattern), recursive=True):
            os.remove(f)
            print(f"Deleted: {f}")
    
    # Optionally delete
    if not keep_bam:
        for f in glob.glob(os.path.join(output_dir, '**', '*_sorted.bam'), recursive=True):
            os.remove(f)
            print(f"Deleted: {f}")
    
    if not keep_intermediate_pairs:
        for pattern in ['*.sorted.pairs.gz', '*.dedup.pairs.gz']:
            for f in glob.glob(os.path.join(output_dir, '**', pattern), recursive=True):
                os.remove(f)
                print(f"Deleted: {f}")

# Usage
cleanup_hic("results/", keep_bam=False, keep_intermediate_pairs=False)
```

### ChIA-PET / HiChIP Cleanup

```python
def cleanup_chiapet(output_dir: str, keep_bam: bool = False):
    """
    Remove ChIA-PET/HiChIP intermediate files.
    """
    # Always delete
    for pattern in ['*.sam']:
        for f in glob.glob(os.path.join(output_dir, '**', pattern), recursive=True):
            os.remove(f)
            print(f"Deleted: {f}")
    
    if not keep_bam:
        for f in glob.glob(os.path.join(output_dir, '**', '*.bam'), recursive=True):
            os.remove(f)
            print(f"Deleted: {f}")

# Usage
cleanup_chiapet("results/", keep_bam=False)
```

## Disk Space Estimates

| Protocol | Raw Data | After Pipeline | After Cleanup |
|----------|----------|----------------|---------------|
| Hi-C (100M reads) | ~20 GB | ~100 GB | ~5 GB |
| ChIA-PET (50M reads) | ~10 GB | ~50 GB | ~2 GB |
| HiChIP (50M reads) | ~10 GB | ~50 GB | ~2 GB |

---

## References

1. **Mumbach et al. (2016)** - HiChIP: efficient and sensitive analysis of protein-directed genome architecture. *Nature Methods* 13, 919–922. https://doi.org/10.1038/nmeth.3999
2. **Li et al. (2010)** - ChIA-PET tool for comprehensive chromatin interaction analysis with paired-end tag sequencing. *Genome Biology* 11, R22.
3. **Liang et al. (2017)** - BL-Hi-C is an efficient and sensitive approach for capturing structural and regulatory chromatin interactions. *Nature Communications* 8, 1622.
4. **Rao et al. (2014)** - A 3D Map of the Human Genome at Kilobase Resolution Reveals Principles of Chromatin Looping. *Cell* 159, 1665–1680.

---

## Version

```python
import chr3d as c3d
print(c3d.__version__)  # 3.2.0
```
