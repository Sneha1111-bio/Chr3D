# Rowan-PET: ChIA-PET and HiChIP Analysis Pipeline

A comprehensive Python library for analyzing chromatin interaction data from ChIA-PET and HiChIP experiments. Similar to how **Scanpy** is the standard for single-cell RNA-seq analysis, **Rowan-PET** aims to be the standard for chromatin interaction analysis.

## Features

- **Complete Pipeline**: From raw FASTQ to significant chromatin loops
- **Dual Protocol Support**: ChIA-PET and HiChIP analysis modes
- **Python API**: Use as a library in your scripts or Jupyter notebooks
- **Statistical Rigor**: Hypergeometric test with FDR correction
- **High Performance**: SIMD-accelerated alignment (parasail), parallel processing
- **Modular Design**: Run individual steps or the complete pipeline

## Installation

```bash
# Clone and install
git clone https://github.com/rowan-pet/rowan-pet.git
cd rowan-pet
pip install -e .

# Install external dependencies via conda
conda install -c bioconda bwa samtools macs3
pip install parasail  # For SIMD-accelerated linker filtering
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| BWA | >= 0.7.17 | Genomic mapping |
| SAMtools | >= 1.10 | BAM/SAM processing |
| MACS3 | >= 3.0.0 | Peak calling |
| parasail | >= 1.3 | SIMD-accelerated alignment |
| pandas | >= 1.5 | Data manipulation |
| scipy | >= 1.10 | Statistical tests |

---

## Python API

Rowan-PET is designed as a Python library. Import and use individual modules directly:

```python
import rowan_pet as rp

# Check version
print(rp.__version__)  # 3.0.0
```

### Available Classes

| Class | Step | Description |
|-------|------|-------------|
| `rp.LinkerFilterV3` | 1 | Linker filtering with parasail SIMD |
| `rp.PETMapper` | 2 | Genomic mapping with BWA |
| `rp.ChIAPETPurifier` | 3a | ChIA-PET deduplication & merging |
| `rp.HiChIPPurifier` | 3b | HiChIP same-fragment removal |
| `rp.PETCategorizer` | 4 | PET classification (iPET/sPET/oPET) |
| `rp.PeakCaller` | 5 | Peak calling with MACS3 |
| `rp.PreClusterer` | 6.1 | Pre-clustering with tag extension |
| `rp.AnchorClusterer` | 6.2 | Anchor clustering |
| `rp.StatisticalSignificance` | 6.3 | FDR-corrected loop significance |
| `rp.RestrictionSiteGenerator` | Util | Generate restriction fragments |

---

## Step-by-Step Python API Usage

### Step 1: Linker Filtering

Detects and removes linker sequences from paired-end reads using SIMD-accelerated local alignment.

```python
import rowan_pet as rp

# Initialize linker filter
linker_filter = rp.LinkerFilterV3(
    linker_a="GTTGGATAAG",           # Linker A sequence
    linker_b="GTTGGAATGT",           # Linker B sequence  
    min_score_ratio=0.7,             # Minimum alignment score ratio (0-1)
    min_tag_length=18,               # Minimum tag length after trimming
    max_tag_length=None,             # Maximum tag length (None = no limit)
    n_threads=24,                    # Number of threads
    check_reverse_complement=True    # Check reverse complement of linkers
)

# Run filtering
stats = linker_filter.filter_fastq(
    fastq_r1="sample_R1.fastq.gz",
    fastq_r2="sample_R2.fastq.gz",
    output_prefix="filtered",
    output_dir="output/",
    batch_size=100000,               # Reads per batch
    show_progress=True,              # Show progress bar
    compress_output=False            # Compress output files
)

# Access statistics
print(f"Total reads: {stats['total_reads']:,}")
print(f"Valid PETs: {stats['valid_pets']:,}")
print(f"Linker composition: {stats['linker_composition']}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `linker_a` | str | required | Linker A sequence (5'→3') |
| `linker_b` | str | required | Linker B sequence (5'→3') |
| `min_score_ratio` | float | 0.7 | Min alignment score / max possible score |
| `min_tag_length` | int | 18 | Minimum tag length after linker removal |
| `max_tag_length` | int | None | Maximum tag length (None = unlimited) |
| `n_threads` | int | 1 | Number of parallel threads |
| `check_reverse_complement` | bool | True | Also check reverse complement |

---

### Step 2: Genomic Mapping

Maps linker-filtered tags to reference genome using BWA.

```python
import rowan_pet as rp

# Initialize mapper
mapper = rp.PETMapper(
    genome_index="/path/to/hg38.fa",  # BWA-indexed genome
    n_threads=24,                      # Number of threads
    use_bwa_mem=True,                  # True=BWA-MEM (fast), False=BWA-ALN (accurate)
    mapping_quality_cutoff=30          # Minimum MAPQ score
)

# Map a single linker combination
stats = mapper.map_linker_filtered_fastq(
    r1_fastq="filtered.1_1.R1.fastq",
    r2_fastq="filtered.1_1.R2.fastq",
    output_prefix="mapped_1_1",
    output_dir="output/",
    remove_duplicates=True,            # Remove PCR duplicates
    parallel=True,                     # Use parallel chunk-based mapping
    n_chunks=24                        # Number of chunks for parallel mode
)

# Access statistics
print(f"Total pairs: {stats['total_pairs']:,}")
print(f"Mapped pairs: {stats['mapped_pairs']:,}")
print(f"Unique pairs: {stats['unique_pairs']:,}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `genome_index` | str | required | Path to BWA-indexed genome FASTA |
| `n_threads` | int | 1 | Number of threads for BWA |
| `use_bwa_mem` | bool | True | Use BWA-MEM (True) or BWA-ALN (False) |
| `mapping_quality_cutoff` | int | 30 | Minimum mapping quality score |

**BWA Aligner Selection:**

| Read Length | Recommended | Speed | Accuracy |
|-------------|-------------|-------|----------|
| < 55 bp | BWA-ALN (`use_bwa_mem=False`) | Slow | Excellent |
| ≥ 55 bp | BWA-MEM (`use_bwa_mem=True`) | Fast | Excellent |

---

### Step 3a: ChIA-PET Purifying

Deduplication and merging of similar PETs for ChIA-PET data.

```python
import rowan_pet as rp

# Initialize purifier
purifier = rp.ChIAPETPurifier(
    merge_distance=2,      # Max distance to merge similar PETs (bp)
    min_mapq=30            # Minimum mapping quality
)

# Run purification
stats = purifier.purify(
    input_bedpe="mapped.bedpe",
    output_prefix="purified",
    output_dir="output/"
)

# Access statistics
print(f"Input PETs: {stats['input_pets']:,}")
print(f"After dedup: {stats['after_dedup']:,}")
print(f"After merge: {stats['after_merge']:,}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `merge_distance` | int | 2 | Max bp distance to merge similar PETs |
| `min_mapq` | int | 30 | Minimum mapping quality |

---

### Step 3b: HiChIP Purifying

Removes same-fragment PETs for HiChIP data using restriction site information.

```python
import rowan_pet as rp

# Initialize HiChIP purifier
purifier = rp.HiChIPPurifier(
    restriction_file="/path/to/MboI_sites.bed",  # Restriction site BED file
    min_insert_size=1                             # Min fragment skip distance
)

# Run purification
stats = purifier.purify(
    input_bedpe="mapped.bedpe",
    output_prefix="purified",
    output_dir="output/"
)

# Access statistics
print(f"Input PETs: {stats['input_pets']:,}")
print(f"Same-fragment removed: {stats['same_fragment_removed']:,}")
print(f"Output PETs: {stats['output_pets']:,}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `restriction_file` | str | required | BED file with restriction sites |
| `min_insert_size` | int | 1 | Minimum fragment skip distance |

---

### Step 4: PET Categorization

Classifies PETs into iPET (inter-ligation), sPET (self-ligation), and oPET (other).

```python
import rowan_pet as rp

# Initialize categorizer
categorizer = rp.PETCategorizer(
    mode='chiapet',              # 'chiapet' or 'hichip'
    self_ligation_cutoff=None    # None = use mode default
)

# Run categorization
stats = categorizer.categorize(
    input_bedpe="purified.bedpe",
    output_prefix="categorized",
    output_dir="output/"
)

# Access statistics
print(f"Total PETs: {stats['total']:,}")
print(f"iPETs: {stats['ipet']['count']:,} ({stats['ipet']['percentage']:.1f}%)")
print(f"sPETs: {stats['spet']['count']:,} ({stats['spet']['percentage']:.1f}%)")
print(f"oPETs: {stats['opet']['count']:,} ({stats['opet']['percentage']:.1f}%)")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | str | 'chiapet' | Analysis mode: 'chiapet' or 'hichip' |
| `self_ligation_cutoff` | int | None | Distance cutoff (None = mode default) |

**Mode-Specific Defaults:**

| Mode | Self-Ligation Cutoff |
|------|---------------------|
| ChIA-PET | 8000 bp |
| HiChIP | 1000 bp |

---

### Step 5: Peak Calling

Identifies protein binding sites using MACS3 on sPET data.

```python
import rowan_pet as rp

# Initialize peak caller
peak_caller = rp.PeakCaller(
    genome_size='hs',          # 'hs' (human), 'mm' (mouse), or integer
    qvalue_cutoff=0.05,        # Q-value threshold
    keep_dup='1',              # '1' = remove duplicates, 'all' = keep
    build_model=True,          # Build MACS3 shift model
    macs3_path='macs3',        # Path to MACS3 executable
    conda_env='rowan-hic'      # Conda environment (optional)
)

# Run peak calling
stats = peak_caller.call_peaks_from_bedpe(
    bedpe_file="categorized.spet",
    output_prefix="peaks",
    output_dir="output/"
)

# Access statistics
print(f"Peaks called: {stats['num_peaks']:,}")
print(f"Output file: {stats['peak_file']}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `genome_size` | str | 'hs' | Genome size ('hs', 'mm', or integer) |
| `qvalue_cutoff` | float | 0.05 | Q-value threshold for peaks |
| `keep_dup` | str | '1' | Duplicate handling ('1' or 'all') |
| `build_model` | bool | True | Build MACS3 shift model |
| `macs3_path` | str | 'macs3' | Path to MACS3 executable |
| `conda_env` | str | None | Conda environment name |

---

### Step 6.1: Pre-Clustering

Extends PET tags and creates initial clusters.

```python
import rowan_pet as rp

# Initialize pre-clusterer
pre_clusterer = rp.PreClusterer(
    extension_length=500,                    # Tag extension length (bp)
    chrom_sizes_file="/path/to/chrom.sizes"  # Optional chromosome sizes
)

# Run pre-clustering
stats = pre_clusterer.pre_cluster(
    ipet_file="categorized.ipet",
    output_prefix="output/loop"
)

# Access statistics
print(f"Input iPETs: {stats['num_pets']:,}")
print(f"Pre-clusters: {stats['num_clusters']:,}")
print(f"Output file: {stats['output_file']}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `extension_length` | int | 500 | Tag extension length in bp |
| `chrom_sizes_file` | str | None | Path to chromosome sizes file |

---

### Step 6.2: Anchor Clustering

Merges overlapping anchor clusters.

```python
import rowan_pet as rp

# Initialize anchor clusterer
anchor_clusterer = rp.AnchorClusterer()

# Run anchor clustering
stats = anchor_clusterer.cluster_anchors(
    precluster_file="output/loop.pre_cluster.sorted",
    output_file="output/anchor_clusters.txt"
)

# Access statistics
print(f"Input pre-clusters: {stats['input_preclusters']:,}")
print(f"Output anchor clusters: {stats['output_anchor_clusters']:,}")
print(f"Reduction: {stats['reduction']:,} clusters merged")
```

---

### Step 6.3: Statistical Significance

Calculates statistical significance of chromatin loops using hypergeometric test with FDR correction.

```python
import rowan_pet as rp

# Initialize statistical significance calculator
stat_sig = rp.StatisticalSignificance(
    ipet_count_threshold=2,    # Minimum iPET count per loop
    pvalue_cutoff=0.05,        # FDR threshold
    extension_length=500       # Tag extension for counting
)

# Calculate significance
stats = stat_sig.calculate_significance(
    cluster_file="output/anchor_clusters.txt",
    ipet_file="categorized.ipet",
    output_prefix="output/loops"
)

# Access statistics
print(f"Input clusters: {stats['num_input_clusters']:,}")
print(f"Significant loops (FDR < 0.05): {stats['num_significant_loops']:,}")
print(f"FDR < 0.01: {stats['num_fdr_001']:,}")
print(f"Output file: {stats['output_file']}")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ipet_count_threshold` | int | 2 | Minimum iPET count for a loop |
| `pvalue_cutoff` | float | 0.05 | FDR threshold for significance |
| `extension_length` | int | 500 | Tag extension for counting |

---

### Utility: Restriction Site Generator

Generates restriction fragments from a genome FASTA file.

```python
import rowan_pet as rp

# Initialize generator
generator = rp.RestrictionSiteGenerator(
    enzyme="MboI",              # Restriction enzyme name
    recognition_site="GATC"     # Recognition sequence
)

# Generate restriction sites
stats = generator.generate(
    genome_fasta="/path/to/hg38.fa",
    output_file="MboI_sites.bed"
)

print(f"Total sites: {stats['total_sites']:,}")
print(f"Total fragments: {stats['total_fragments']:,}")
```

---

## Complete Pipeline Example

### ChIA-PET Analysis

```python
import rowan_pet as rp

# Configuration
GENOME = "/path/to/hg38.fa"
R1 = "sample_R1.fastq.gz"
R2 = "sample_R2.fastq.gz"
OUTPUT = "results/"
THREADS = 24

# Step 1: Linker Filtering
linker_filter = rp.LinkerFilterV3(
    linker_a="GTTGGATAAG",
    linker_b="GTTGGAATGT",
    n_threads=THREADS
)
linker_filter.filter_fastq(R1, R2, "filtered", OUTPUT)

# Step 2: Mapping (for each linker combination)
mapper = rp.PETMapper(GENOME, n_threads=THREADS, use_bwa_mem=True)
for combo in ["1_1", "1_2", "2_1", "2_2"]:
    mapper.map_linker_filtered_fastq(
        f"{OUTPUT}/filtered.{combo}.R1.fastq",
        f"{OUTPUT}/filtered.{combo}.R2.fastq",
        f"mapped_{combo}", OUTPUT
    )

# Step 3: Purifying
purifier = rp.ChIAPETPurifier(merge_distance=2)
purifier.purify(f"{OUTPUT}/mapped_merged.bedpe", "purified", OUTPUT)

# Step 4: Categorization
categorizer = rp.PETCategorizer(mode='chiapet')
categorizer.categorize(f"{OUTPUT}/purified.bedpe", "categorized", OUTPUT)

# Step 5: Peak Calling
peak_caller = rp.PeakCaller(genome_size='hs')
peak_caller.call_peaks_from_bedpe(f"{OUTPUT}/categorized.spet", "peaks", OUTPUT)

# Step 6: Loop Calling
pre_clusterer = rp.PreClusterer(extension_length=500)
pre_clusterer.pre_cluster(f"{OUTPUT}/categorized.ipet", f"{OUTPUT}/loop")

anchor_clusterer = rp.AnchorClusterer()
anchor_clusterer.cluster_anchors(
    f"{OUTPUT}/loop.pre_cluster.sorted",
    f"{OUTPUT}/anchor_clusters.txt"
)

stat_sig = rp.StatisticalSignificance(ipet_count_threshold=2, pvalue_cutoff=0.05)
stat_sig.calculate_significance(
    f"{OUTPUT}/anchor_clusters.txt",
    f"{OUTPUT}/categorized.ipet",
    f"{OUTPUT}/loops"
)
```

### HiChIP Analysis

```python
import rowan_pet as rp

# Configuration (HiChIP-specific)
GENOME = "/path/to/hg38.fa"
RESTRICTION_SITES = "/path/to/MboI_sites.bed"
R1 = "sample_R1.fastq.gz"
R2 = "sample_R2.fastq.gz"
OUTPUT = "results/"
THREADS = 24

# Step 1: Linker Filtering (same as ChIA-PET)
linker_filter = rp.LinkerFilterV3(
    linker_a="GTTGGATAAG",
    linker_b="GTTGGAATGT",
    n_threads=THREADS
)
linker_filter.filter_fastq(R1, R2, "filtered", OUTPUT)

# Step 2: Mapping (same as ChIA-PET)
mapper = rp.PETMapper(GENOME, n_threads=THREADS, use_bwa_mem=True)
mapper.map_linker_filtered_fastq(
    f"{OUTPUT}/filtered.1_1.R1.fastq",
    f"{OUTPUT}/filtered.1_1.R2.fastq",
    "mapped", OUTPUT
)

# Step 3: HiChIP Purifying (different from ChIA-PET!)
purifier = rp.HiChIPPurifier(restriction_file=RESTRICTION_SITES)
purifier.purify(f"{OUTPUT}/mapped.bedpe", "purified", OUTPUT)

# Step 4: Categorization (HiChIP mode - 1000bp cutoff)
categorizer = rp.PETCategorizer(mode='hichip')
categorizer.categorize(f"{OUTPUT}/purified.bedpe", "categorized", OUTPUT)

# Steps 5-6: Same as ChIA-PET
# ...
```

---

## Output Files

| File | Description |
|------|-------------|
| `filtered.*.R1.fastq` | Linker-filtered R1 reads |
| `filtered.*.R2.fastq` | Linker-filtered R2 reads |
| `mapped.bedpe` | Mapped PET pairs in BEDPE format |
| `purified.bedpe` | Purified PETs |
| `categorized.ipet` | Inter-ligation PETs (for loops) |
| `categorized.spet` | Self-ligation PETs (for peaks) |
| `categorized.opet` | Other PETs (discarded) |
| `peaks_peaks.narrowPeak` | Called peaks (MACS3 format) |
| `loops.cluster.FDRfiltered.txt` | Significant chromatin loops |

---

## ChIA-PET vs HiChIP Comparison

| Feature | ChIA-PET | HiChIP |
|---------|----------|--------|
| **Linker filtering** | ✅ Yes (bridge linkers) | ❌ No (*in situ* Hi-C chemistry) |
| **First step** | LinkerFilterV3 | PETMapper |
| **Purifying** | Deduplication + PET merging | Same-fragment removal (biotin artifacts) |
| **Self-ligation cutoff** | 8000 bp | 1000 bp (Mumbach et al., 2016) |
| **Requires restriction sites** | No | Yes |
| **Purifier class** | `ChIAPETPurifier` | `HiChIPPurifier` |
| **Total steps** | 6 | 5 |

> **Note:** HiChIP does NOT use linker filtering. It uses standard *in situ* Hi-C chemistry with biotin-dATP fill-in at restriction sites, not synthetic bridge linkers.

---

# Hi-C Analysis

Rowan-PET includes a complete **Hi-C** analysis pipeline with **modular classes** for each step.

## Hi-C Available Classes

| Class | Purpose | When to Use |
|-------|---------|-------------|
| `rp.FastqSplitter` | Split FASTQ files | Large datasets, parallel processing |
| `rp.HiCAligner` | BWA MEM alignment | Just need alignment |
| `rp.HiCSamProcessor` | SAM → sorted BAM | Just need BAM conversion |
| `rp.HiCPairsProcessor` | pairtools processing | Just need pairs (parse/sort/dedup/filter) |
| `rp.HiCMatrixGenerator` | cooler matrix | Just need .cool/.mcool |
| `rp.HiCPipeline` | Complete pipeline | Run everything |
| `rp.HiCQCAnalyzer` | QC analysis | Analyze QC metrics |

### Hi-C Dependencies

```bash
conda install -c bioconda bwa samtools pairtools cooler
```

---

## Hi-C Python API

### Option 1: Complete Pipeline (HiCPipeline)

Run the entire Hi-C pipeline with one class:

```python
import rowan_pet as rp

hic = rp.HiCPipeline(
    genome_index="/path/to/hg38.fa",
    chrom_sizes="/path/to/hg38.chrom.sizes",
    threads=24
)

stats = hic.run(
    fastq1="sample_R1.fastq.gz",
    fastq2="sample_R2.fastq.gz",
    output_dir="results/",
    sample_id="sample1"
)
```

---

### Option 2: Modular Step-by-Step

Use individual classes for more control:

```python
import rowan_pet as rp

# Step 0 (Optional): Split large FASTQ files
splitter = rp.FastqSplitter(n_chunks=10)
chunks = splitter.split("R1.fastq.gz", "R2.fastq.gz", "split_dir/")

# Step 1: Alignment
aligner = rp.HiCAligner("/path/to/hg38.fa", threads=24)
aligner.align("R1.fastq.gz", "R2.fastq.gz", "aligned.sam")

# Step 2: SAM/BAM processing
processor = rp.HiCSamProcessor(threads=24)
processor.process("aligned.sam", "sorted.bam")

# Step 3: Pairs processing (individual pairtools steps)
pairs = rp.HiCPairsProcessor("/path/to/hg38.chrom.sizes", threads=24)
pairs.parse("sorted.bam", "parsed.pairs.gz")
pairs.sort("parsed.pairs.gz", "sorted.pairs.gz")
pairs.dedup("sorted.pairs.gz", "dedup.pairs.gz")
pairs.filter("dedup.pairs.gz", "filtered.pairs.gz")

# Step 4: Contact matrix generation
matrix = rp.HiCMatrixGenerator("/path/to/hg38.chrom.sizes", threads=24)
matrix.create("filtered.pairs.gz", "sample.cool", resolution=1000)
matrix.balance("sample.cool")
matrix.zoomify("sample.cool", "sample.mcool")
```

---

### HiCPairsProcessor - Individual pairtools Steps

The `HiCPairsProcessor` exposes each pairtools step individually:

```python
import rowan_pet as rp

pairs = rp.HiCPairsProcessor("/path/to/hg38.chrom.sizes", threads=24)

# Run just deduplication on existing pairs
pairs.dedup("sorted.pairs.gz", "dedup.pairs.gz", stats_file="dedup.stats")

# Run just filtering with custom pair types
pairs.filter("dedup.pairs.gz", "filtered.pairs.gz", pair_types=['UU', 'UR', 'RU'])

# Or run all steps at once
pairs.process_all("sorted.bam", "output_dir/", prefix="sample")
```

---

## Hi-C Output Files

| File | Description |
|------|-------------|
| `*.sam` | Raw BWA MEM alignments |
| `*_sorted.bam` | Name-sorted BAM file |
| `*.filtered.pairs.gz` | Filtered valid pairs |
| `*.cool` | Contact matrix (1kb resolution) |
| `*.mcool` | Multi-resolution contact matrix |

---

## Protocol Comparison

| Feature | ChIA-PET | HiChIP | Hi-C |
|---------|----------|--------|------|
| **Linker filtering** | Yes | Yes | No |
| **Protein-specific** | Yes | Yes | No |
| **Genome-wide** | No | No | Yes |
| **Output format** | BEDPE/Loops | BEDPE/Loops | .cool/.mcool |
| **Pipeline class** | Multiple steps | Multiple steps | `HiCPipeline` |

---

## Citation

If you use Rowan-PET in your research, please cite:

```
Rowan-PET: A Python Pipeline for ChIA-PET, HiChIP, and Hi-C Analysis
```

## License

MIT License

## References

- Li et al. (2010) ChIA-PET tool for comprehensive chromatin interaction analysis
- Fullwood et al. (2009) An oestrogen-receptor-α-bound human chromatin interactome
- Mumbach et al. (2016) HiChIP: efficient and sensitive analysis of protein-directed genome architecture
- Rao et al. (2014) A 3D map of the human genome at kilobase resolution
- 4DN Hi-C Processing Pipeline
# Chr3D
