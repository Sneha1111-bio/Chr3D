"""
Step 2: Genomic Mapping Module (v3 - CLEAN)

Maps linker-filtered ChIA-PET tags to reference genome using BWA.
Outputs BAM file and uses samtools for statistics.

Key changes from v2:
- Outputs BAM file (not just BEDPE)
- Uses samtools flagstat for alignment statistics
- Cleaner code with less manual stat tracking
- Proper MAPQ filtering for ChIA-PET

Based on ChIA-PET Tool V3 and paper specifications.
"""

import subprocess
import logging
import os
import gzip
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import pysam
import itertools

# Use centralized logging
from ..utils.logging import get_logger

# Get module logger
logger = get_logger(__name__)


class PETMapperV3:
    """
    Maps ChIA-PET tags to reference genome and generates BEDPE files.
    
    Workflow:
    1. BWA paired-end alignment → SAM
    2. SAM → sorted BAM (coordinate sorted for stats)
    3. samtools flagstat → alignment statistics
    4. Name-sorted BAM → BEDPE
    5. Deduplicate BEDPE
    """
    
    def __init__(
        self,
        genome_index: str,
        mapping_quality_cutoff: int = 30,
        n_threads: int = 4,
        use_bwa_mem: bool = True,
    ):
        """
        Initialize PET mapper.
        
        Args:
            genome_index: Path to BWA genome index
            mapping_quality_cutoff: Minimum mapping quality (default: 30)
            n_threads: Number of threads for BWA/SAMtools
            use_bwa_mem: Use BWA-MEM (True) or BWA-ALN (False)
        """
        self.genome_index = genome_index
        self.mapping_quality_cutoff = mapping_quality_cutoff
        self.n_threads = n_threads
        self.use_bwa_mem = use_bwa_mem
        
        self._validate_genome_index()
        
        logger.info(f"Initialized PETMapperV3")
        logger.info(f"  Genome index: {genome_index}")
        logger.info(f"  MAPQ cutoff: {mapping_quality_cutoff}")
        logger.info(f"  Threads: {n_threads}")
        logger.info(f"  BWA mode: {'MEM' if use_bwa_mem else 'ALN'}")
    
    def _validate_genome_index(self):
        """Validate that genome index files exist."""
        required_extensions = ['.amb', '.ann', '.bwt', '.pac', '.sa']
        missing = []
        
        for ext in required_extensions:
            if not Path(f"{self.genome_index}{ext}").exists():
                missing.append(ext)
        
        if missing:
            raise FileNotFoundError(
                f"Genome index incomplete. Missing: {missing}"
            )
    
    def _run_cmd(self, cmd: List[str], desc: str, stdout_file: str = None) -> bool:
        """Run a command with logging."""
        logger.info(f"Running: {desc}")
        logger.debug(f"  Command: {' '.join(cmd)}")
        
        try:
            if stdout_file:
                with open(stdout_file, 'w') as out_f:
                    result = subprocess.run(
                        cmd, stdout=out_f, stderr=subprocess.PIPE, 
                        text=True, check=True
                    )
            else:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True
                )
            logger.info(f"  ✓ {desc} completed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ {desc} failed: {e.stderr}")
            return False
        except FileNotFoundError as e:
            logger.error(f"  ✗ Command not found: {e}")
            return False
    
    def run_bwa_mem(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_bam: str
    ) -> bool:
        """
        Run BWA-MEM and pipe to samtools for BAM output.
        """
        # BWA-MEM | samtools view -bS | samtools sort
        bwa_cmd = f"bwa mem -t {self.n_threads} -M {self.genome_index} {fastq_r1} {fastq_r2}"
        sam_view = f"samtools view -@ {self.n_threads} -bS -"
        sam_sort = f"samtools sort -@ {self.n_threads} -o {output_bam} -"
        
        full_cmd = f"{bwa_cmd} | {sam_view} | {sam_sort}"
        
        logger.info(f"Running BWA-MEM pipeline: {fastq_r1} + {fastq_r2} → {output_bam}")
        
        try:
            result = subprocess.run(
                full_cmd, shell=True, capture_output=True, text=True, check=True
            )
            
            # Index the BAM
            subprocess.run(
                ['samtools', 'index', '-@', str(self.n_threads), output_bam],
                check=True, capture_output=True
            )
            
            logger.info(f"  ✓ BWA-MEM completed: {output_bam}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ BWA-MEM failed: {e.stderr}")
            return False
    
    def run_bwa_aln(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_bam: str
    ) -> bool:
        """
        Run BWA-ALN + SAMPE for short reads.
        """
        sai_r1 = output_bam.replace('.bam', '.R1.sai')
        sai_r2 = output_bam.replace('.bam', '.R2.sai')
        temp_sam = output_bam.replace('.bam', '.temp.sam')
        
        logger.info(f"Running BWA-ALN pipeline: {fastq_r1} + {fastq_r2} → {output_bam}")
        
        try:
            # Step 1: bwa aln R1
            cmd_aln_r1 = ['bwa', 'aln', '-t', str(self.n_threads), '-n', '2',
                         self.genome_index, fastq_r1]
            with open(sai_r1, 'w') as f:
                subprocess.run(cmd_aln_r1, stdout=f, stderr=subprocess.PIPE, check=True)
            
            # Step 2: bwa aln R2
            cmd_aln_r2 = ['bwa', 'aln', '-t', str(self.n_threads), '-n', '2',
                         self.genome_index, fastq_r2]
            with open(sai_r2, 'w') as f:
                subprocess.run(cmd_aln_r2, stdout=f, stderr=subprocess.PIPE, check=True)
            
            # Step 3: bwa sampe → SAM
            cmd_sampe = ['bwa', 'sampe', self.genome_index, sai_r1, sai_r2, fastq_r1, fastq_r2]
            with open(temp_sam, 'w') as f:
                subprocess.run(cmd_sampe, stdout=f, stderr=subprocess.PIPE, check=True)
            
            # Step 4: SAM → sorted BAM
            cmd_sort = f"samtools view -@ {self.n_threads} -bS {temp_sam} | samtools sort -@ {self.n_threads} -o {output_bam} -"
            subprocess.run(cmd_sort, shell=True, check=True, capture_output=True)
            
            # Index
            subprocess.run(['samtools', 'index', '-@', str(self.n_threads), output_bam],
                          check=True, capture_output=True)
            
            # Cleanup
            for f in [sai_r1, sai_r2, temp_sam]:
                if os.path.exists(f):
                    os.remove(f)
            
            logger.info(f"  ✓ BWA-ALN completed: {output_bam}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ BWA-ALN failed: {e}")
            return False
    
    def get_samtools_stats(self, bam_file: str, output_stats: str) -> Dict:
        """
        Run samtools flagstat and parse results.
        """
        logger.info(f"Running samtools flagstat: {bam_file}")
        
        try:
            result = subprocess.run(
                ['samtools', 'flagstat', '-@', str(self.n_threads), bam_file],
                capture_output=True, text=True, check=True
            )
            
            # Save raw output
            with open(output_stats, 'w') as f:
                f.write(result.stdout)
            
            # Parse key metrics
            stats = {}
            for line in result.stdout.strip().split('\n'):
                parts = line.split(' + ')
                if len(parts) >= 2:
                    count = int(parts[0])
                    desc = ' '.join(parts[1].split()[1:])  # Skip second number
                    
                    if 'in total' in line:
                        stats['total_reads'] = count
                    elif 'mapped (' in line:
                        stats['mapped_reads'] = count
                    elif 'properly paired' in line:
                        stats['properly_paired'] = count
                    elif 'singletons' in line:
                        stats['singletons'] = count
            
            logger.info(f"  Total reads: {stats.get('total_reads', 0):,}")
            logger.info(f"  Mapped: {stats.get('mapped_reads', 0):,}")
            logger.info(f"  Properly paired: {stats.get('properly_paired', 0):,}")
            
            return stats
        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ samtools flagstat failed: {e}")
            return {}
    
    def filter_bam_by_mapq(
        self,
        input_bam: str,
        output_bam: str,
        min_mapq: int = None
    ) -> bool:
        """
        Filter BAM by mapping quality.
        """
        if min_mapq is None:
            min_mapq = self.mapping_quality_cutoff
        
        logger.info(f"Filtering BAM by MAPQ >= {min_mapq}")
        
        cmd = [
            'samtools', 'view',
            '-@', str(self.n_threads),
            '-b',
            '-q', str(min_mapq),
            '-o', output_bam,
            input_bam
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            subprocess.run(['samtools', 'index', '-@', str(self.n_threads), output_bam],
                          check=True, capture_output=True)
            logger.info(f"  ✓ Filtered BAM: {output_bam}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ Filter failed: {e}")
            return False
    
    def bam_to_bedpe(
        self,
        bam_file: str,
        output_bedpe: str
    ) -> Dict:
        """
        Convert name-sorted BAM to BEDPE format.
        
        For ChIA-PET:
        - Both reads must be mapped
        - Use 5' positions
        - No filtering by proper pair (ChIA-PET has unusual orientations)
        """
        logger.info(f"Converting BAM to BEDPE: {bam_file} → {output_bedpe}")
        
        # First, name-sort the BAM
        name_sorted = bam_file.replace('.bam', '.namesorted.bam')
        cmd_sort = [
            'samtools', 'sort', '-n',
            '-@', str(self.n_threads),
            '-o', name_sorted,
            bam_file
        ]
        
        try:
            subprocess.run(cmd_sort, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ Name sort failed: {e}")
            return {}
        
        stats = defaultdict(int)
        
        with pysam.AlignmentFile(name_sorted, 'rb') as bam, \
             open(output_bedpe, 'w') as bedpe:
            
            for read_name, group in itertools.groupby(bam, key=lambda r: r.query_name):
                alignments = list(group)
                stats['total_read_groups'] += 1
                
                # Separate R1 and R2
                r1_alns = [a for a in alignments if a.is_read1 and not a.is_unmapped]
                r2_alns = [a for a in alignments if a.is_read2 and not a.is_unmapped]
                
                if not r1_alns or not r2_alns:
                    stats['unmapped_pair'] += 1
                    continue
                
                # Take best alignment for each (highest MAPQ)
                r1 = max(r1_alns, key=lambda a: a.mapping_quality)
                r2 = max(r2_alns, key=lambda a: a.mapping_quality)
                
                # Get 5' positions
                if r1.is_reverse:
                    pos1, strand1 = r1.reference_end, '-'
                else:
                    pos1, strand1 = r1.reference_start, '+'
                
                if r2.is_reverse:
                    pos2, strand2 = r2.reference_end, '-'
                else:
                    pos2, strand2 = r2.reference_start, '+'
                
                chr1 = r1.reference_name
                chr2 = r2.reference_name
                
                # Ensure consistent ordering
                if (chr1 > chr2) or (chr1 == chr2 and pos1 > pos2):
                    chr1, chr2 = chr2, chr1
                    pos1, pos2 = pos2, pos1
                    strand1, strand2 = strand2, strand1
                
                score = min(r1.mapping_quality, r2.mapping_quality)
                
                bedpe.write(f"{chr1}\t{pos1}\t{pos1+1}\t{chr2}\t{pos2}\t{pos2+1}\t"
                           f"{read_name}\t{score}\t{strand1}\t{strand2}\n")
                
                stats['valid_pairs'] += 1
                if chr1 == chr2:
                    stats['intra_chromosomal'] += 1
                else:
                    stats['inter_chromosomal'] += 1
        
        # Cleanup
        os.remove(name_sorted)
        
        logger.info(f"  ✓ BEDPE generated: {stats['valid_pairs']:,} valid pairs")
        return dict(stats)
    
    def remove_duplicates(
        self,
        input_bedpe: str,
        output_bedpe: str
    ) -> int:
        """
        Remove duplicate PETs by coordinate.
        """
        logger.info(f"Removing duplicates: {input_bedpe}")
        
        seen = set()
        unique = 0
        duplicates = 0
        
        with open(input_bedpe) as inf, open(output_bedpe, 'w') as outf:
            for line in inf:
                fields = line.strip().split('\t')
                if len(fields) < 6:
                    continue
                
                key = (fields[0], int(fields[1]), fields[3], int(fields[4]))
                
                if key not in seen:
                    seen.add(key)
                    outf.write(line)
                    unique += 1
                else:
                    duplicates += 1
        
        logger.info(f"  ✓ Unique: {unique:,}, Duplicates: {duplicates:,}")
        return duplicates
    
    def map_paired_fastq(
        self,
        fastq_r1: str,
        fastq_r2: str,
        output_prefix: str,
        output_dir: str = None,
        keep_bam: bool = True,
        remove_duplicates: bool = True
    ) -> Dict:
        """
        Complete mapping workflow.
        
        Args:
            fastq_r1: R1 FASTQ file
            fastq_r2: R2 FASTQ file
            output_prefix: Output file prefix
            output_dir: Output directory
            keep_bam: Keep BAM files
            remove_duplicates: Deduplicate BEDPE
            
        Returns:
            Dictionary with all statistics
        """
        start_time = time.time()
        
        if output_dir is None:
            output_dir = str(Path(fastq_r1).parent)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Output files
        raw_bam = os.path.join(output_dir, f"{output_prefix}.bam")
        filtered_bam = os.path.join(output_dir, f"{output_prefix}.q{self.mapping_quality_cutoff}.bam")
        raw_stats = os.path.join(output_dir, f"{output_prefix}.flagstat.txt")
        filtered_stats = os.path.join(output_dir, f"{output_prefix}.q{self.mapping_quality_cutoff}.flagstat.txt")
        bedpe_file = os.path.join(output_dir, f"{output_prefix}.bedpe")
        dedup_bedpe = os.path.join(output_dir, f"{output_prefix}.dedup.bedpe")
        
        logger.info("=" * 60)
        logger.info("MAPPING WORKFLOW (v3)")
        logger.info("=" * 60)
        logger.info(f"Input R1: {fastq_r1}")
        logger.info(f"Input R2: {fastq_r2}")
        logger.info(f"Output dir: {output_dir}")
        logger.info("=" * 60)
        
        all_stats = {}
        
        # Step 1: BWA alignment
        logger.info("\n[Step 1] BWA Alignment")
        if self.use_bwa_mem:
            success = self.run_bwa_mem(fastq_r1, fastq_r2, raw_bam)
        else:
            success = self.run_bwa_aln(fastq_r1, fastq_r2, raw_bam)
        
        if not success:
            raise RuntimeError("BWA alignment failed")
        
        # Step 2: Get raw alignment stats
        logger.info("\n[Step 2] Raw Alignment Statistics")
        all_stats['raw'] = self.get_samtools_stats(raw_bam, raw_stats)
        
        # Step 3: Filter by MAPQ
        logger.info(f"\n[Step 3] Filter by MAPQ >= {self.mapping_quality_cutoff}")
        success = self.filter_bam_by_mapq(raw_bam, filtered_bam)
        if not success:
            raise RuntimeError("MAPQ filtering failed")
        
        # Step 4: Get filtered stats
        logger.info("\n[Step 4] Filtered Alignment Statistics")
        all_stats['filtered'] = self.get_samtools_stats(filtered_bam, filtered_stats)
        
        # Step 5: Convert to BEDPE
        logger.info("\n[Step 5] Convert to BEDPE")
        all_stats['bedpe'] = self.bam_to_bedpe(filtered_bam, bedpe_file)
        
        # Step 6: Deduplicate
        if remove_duplicates:
            logger.info("\n[Step 6] Remove Duplicates")
            dup_count = self.remove_duplicates(bedpe_file, dedup_bedpe)
            all_stats['duplicates_removed'] = dup_count
            final_output = dedup_bedpe
        else:
            final_output = bedpe_file
        
        # Cleanup
        if not keep_bam:
            for f in [raw_bam, raw_bam + '.bai', filtered_bam, filtered_bam + '.bai']:
                if os.path.exists(f):
                    os.remove(f)
        
        elapsed = time.time() - start_time
        all_stats['elapsed_seconds'] = elapsed
        
        logger.info("\n" + "=" * 60)
        logger.info("MAPPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total time: {elapsed:.1f}s")
        logger.info(f"Final output: {final_output}")
        logger.info("=" * 60)
        
        return all_stats


def main():
    """Command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Map ChIA-PET reads to reference genome (v3)"
    )
    parser.add_argument('--r1', required=True, help='R1 FASTQ file')
    parser.add_argument('--r2', required=True, help='R2 FASTQ file')
    parser.add_argument('--genome', required=True, help='BWA genome index')
    parser.add_argument('--output-prefix', required=True, help='Output prefix')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads')
    parser.add_argument('--mapq', type=int, default=30, help='Min mapping quality')
    parser.add_argument('--use-bwa-mem', action='store_true', help='Use BWA-MEM')
    parser.add_argument('--keep-bam', action='store_true', help='Keep BAM files')
    parser.add_argument('--no-dedup', action='store_true', help='Skip deduplication')
    
    args = parser.parse_args()
    
    # Use centralized logging (already configured by logger)
    from ..utils.logging import get_logger
    logger = get_logger(__name__)
    
    mapper = PETMapperV3(
        genome_index=args.genome,
        mapping_quality_cutoff=args.mapq,
        n_threads=args.threads,
        use_bwa_mem=args.use_bwa_mem
    )
    
    stats = mapper.map_paired_fastq(
        fastq_r1=args.r1,
        fastq_r2=args.r2,
        output_prefix=args.output_prefix,
        output_dir=args.output_dir,
        keep_bam=args.keep_bam,
        remove_duplicates=not args.no_dedup
    )
    
    print("\nFinal Statistics:")
    import json
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()
