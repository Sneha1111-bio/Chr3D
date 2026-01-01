# Quick Start Guide

Get started with Rowan-PET in minutes.

---

## Workflow Overview

| Protocol | Steps | Linker Filtering? |
|----------|-------|-------------------|
| **ChIA-PET** | 6 steps | ✅ Yes |
| **HiChIP** | 5 steps | ❌ No (starts at mapping) |
| **Hi-C** | 4 steps | ❌ No |

---

## ChIA-PET Analysis (6 steps)

ChIA-PET uses bridge linkers, so linker filtering is **required**.

```python
import rowan_pet as rp

# Step 1: Linker Filtering (ChIA-PET ONLY)
linker_filter = rp.LinkerFilterV3(
    linker_a="GTTGGATAAG",
    linker_b="GTTGGAATGT",
    n_threads=24
)
stats = linker_filter.filter_fastq(
    "sample_R1.fastq.gz", 
    "sample_R2.fastq.gz",
    "filtered", 
    "output/"
)

# Step 2: Mapping
mapper = rp.PETMapper("/path/to/hg38.fa", n_threads=24)
mapper.map_linker_filtered_fastq(
    "output/filtered.1_1.R1.fastq",
    "output/filtered.1_1.R2.fastq",
    "mapped", 
    "output/"
)

# Step 3: Purifying (ChIA-PET deduplication)
purifier = rp.ChIAPETPurifier()
purifier.purify("output/mapped.bedpe", "purified", "output/")

# Step 4: Categorization
categorizer = rp.PETCategorizer(mode='chiapet')  # 8000bp cutoff
categorizer.categorize("output/purified.bedpe", "categorized", "output/")

# Step 5: Peak Calling
peak_caller = rp.PeakCaller(genome_size='hs')
peak_caller.call_peaks_from_bedpe("output/categorized.spet", "peaks", "output/")

# Step 6: Loop Calling
pre_clusterer = rp.PreClusterer(extension_length=500)
pre_clusterer.pre_cluster("output/categorized.ipet", "output/loop")

anchor_clusterer = rp.AnchorClusterer()
anchor_clusterer.cluster_anchors("output/loop.pre_cluster.sorted", "output/clusters.txt")

stat_sig = rp.StatisticalSignificance()
stat_sig.calculate_significance("output/clusters.txt", "output/categorized.ipet", "output/loops")
```

---

## HiChIP Analysis (5 steps - NO linker filtering)

> ⚠️ **Important:** HiChIP does NOT use linker filtering. It uses *in situ* Hi-C chemistry with biotin-dATP fill-in at restriction sites. **Start directly at mapping.**

```python
import rowan_pet as rp

# Step 1: Mapping (HiChIP starts HERE - no linker filtering!)
mapper = rp.PETMapper("/path/to/hg38.fa", n_threads=24)
mapper.map_fastq(
    "sample_R1.fastq.gz",  # Raw FASTQ, not linker-filtered
    "sample_R2.fastq.gz",
    "mapped", 
    "output/"
)

# Step 2: Purifying (HiChIP same-fragment removal)
# Removes self-ligation artifacts from biotin fill-in
purifier = rp.HiChIPPurifier(restriction_file="/path/to/MboI_sites.bed")
purifier.purify("output/mapped.bedpe", "purified", "output/")

# Step 3: Categorization
categorizer = rp.PETCategorizer(mode='hichip')  # 1000bp cutoff (Mumbach et al., 2016)
categorizer.categorize("output/purified.bedpe", "categorized", "output/")

# Step 4: Peak Calling
peak_caller = rp.PeakCaller(genome_size='hs')
peak_caller.call_peaks_from_bedpe("output/categorized.spet", "peaks", "output/")

# Step 5: Loop Calling
pre_clusterer = rp.PreClusterer(extension_length=500)
pre_clusterer.pre_cluster("output/categorized.ipet", "output/loop")

anchor_clusterer = rp.AnchorClusterer()
anchor_clusterer.cluster_anchors("output/loop.pre_cluster.sorted", "output/clusters.txt")

stat_sig = rp.StatisticalSignificance()
stat_sig.calculate_significance("output/clusters.txt", "output/categorized.ipet", "output/loops")
```

## Hi-C Analysis

### Option 1: Complete Pipeline

```python
import rowan_pet as rp

# Initialize pipeline
hic = rp.HiCPipeline(
    genome_index="/path/to/hg38.fa",
    chrom_sizes="/path/to/hg38.chrom.sizes",
    threads=24
)

# Run complete pipeline
stats = hic.run(
    fastq1="sample_R1.fastq.gz",
    fastq2="sample_R2.fastq.gz",
    output_dir="results/",
    sample_id="sample1"
)

# Output: results/matrices/sample1.mcool
```

### Option 2: Modular Step-by-Step

```python
import rowan_pet as rp

# Step 1: Alignment
aligner = rp.HiCAligner("/path/to/hg38.fa", threads=24)
aligner.align("R1.fastq.gz", "R2.fastq.gz", "aligned.sam")

# Step 2: SAM/BAM processing
processor = rp.HiCSamProcessor(threads=24)
processor.process("aligned.sam", "sorted.bam")

# Step 3: Pairs processing
pairs = rp.HiCPairsProcessor("/path/to/hg38.chrom.sizes", threads=24)
pairs.parse("sorted.bam", "parsed.pairs.gz")
pairs.sort("parsed.pairs.gz", "sorted.pairs.gz")
pairs.dedup("sorted.pairs.gz", "dedup.pairs.gz")
pairs.filter("dedup.pairs.gz", "filtered.pairs.gz")

# Step 4: Contact matrix
matrix = rp.HiCMatrixGenerator("/path/to/hg38.chrom.sizes", threads=24)
matrix.create("filtered.pairs.gz", "sample.cool")
matrix.zoomify("sample.cool", "sample.mcool")
```

## Output Files

| Protocol | Key Outputs |
|----------|-------------|
| ChIA-PET/HiChIP | `*.ipet`, `*.spet`, `*_peaks.narrowPeak`, `*.FDRfiltered.txt` |
| Hi-C | `*.cool`, `*.mcool`, `*.filtered.pairs.gz` |
