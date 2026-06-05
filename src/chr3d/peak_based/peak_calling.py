#!/usr/bin/env python3
# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
# This software was developed with support from the National Science Foundation under CAREER Award DBI-2239350.
"""ChIA-PET Peak Calling using MACS3."""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, List
import pandas as pd

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PeakCaller:
    """Peak calling using MACS3 with multiple input format support."""
    
    def __init__(self,
                 genome_size: str = 'hs',
                 qvalue_cutoff: float = 0.05,
                 keep_dup: str = "all",
                 build_model: bool = True,
                 broad: bool = True,
                 macs3_path: str = 'macs3',
                 conda_env: Optional[str] = 'rowan-hic'):
        """Initialize peak caller."""
        self.genome_size = genome_size
        self.qvalue_cutoff = qvalue_cutoff
        self.keep_dup = keep_dup
        self.build_model = build_model
        self.broad = broad
        self.macs3_path = macs3_path
        self.conda_env = conda_env
        
        logger.info("Peak Caller initialized")
        logger.info(f"  Genome size: {genome_size}")
        logger.info(f"  Q-value cutoff: {qvalue_cutoff}")
        logger.info(f"  Keep duplicates: {keep_dup}")
        logger.info(f"  Build model: {build_model}")
        logger.info(f"  Broad peaks: {broad}")
        logger.info(f"  MACS3 path: {macs3_path}")
        if conda_env:
            logger.info(f"  Conda environment: {conda_env}")
    
    def bedpe_to_bed(self, bedpe_file: str, output_bed: str) -> str:
        """Convert BEDPE to BED format (both anchors)."""
        logger.info(f"Converting BEDPE to BED format (both anchors)...")
        logger.info(f"  Input: {bedpe_file}")
        logger.info(f"  Output: {output_bed}")
        df = pd.read_csv(bedpe_file, sep='\t', header=None, comment='#',
                        usecols=list(range(10)),
                        names=['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2',
                              'name', 'score', 'strand1', 'strand2'])

        # Drop rows missing any of the required coordinate columns only
        df = df.dropna(subset=['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2'])
        logger.info(f"  Loaded {len(df):,} BEDPE entries")
        bed1 = df[['chr1', 'start1', 'end1']].copy()
        bed1.columns = ['chr', 'start', 'end']
        bed2 = df[['chr2', 'start2', 'end2']].copy()
        bed2.columns = ['chr', 'start', 'end']
        bed_combined = pd.concat([bed1, bed2], ignore_index=True)
        bed_combined = bed_combined.sort_values(['chr', 'start'])
        bed_combined.to_csv(output_bed, sep='\t', header=False, index=False)
        
        logger.info(f"  Generated {len(bed_combined):,} BED entries ({len(df)*2:,} anchors)")
        
        return output_bed
    
    def validate_bedpe(self, bedpe_file: str) -> int:
        """Validate BEDPE file format and count entries."""
        logger.info(f"Validating BEDPE file: {bedpe_file}")
        df = pd.read_csv(bedpe_file, sep='\t', header=None, comment='#',
                        usecols=list(range(10)),
                        names=['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2',
                              'name', 'score', 'strand1', 'strand2'])

        # Drop rows missing any of the required coordinate columns only
        df = df.dropna(subset=['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2'])
        num_entries = len(df)
        logger.info(f"  Found {num_entries:,} BEDPE entries")
        logger.info(f"  Sample entry:")
        if len(df) > 0:
            sample = df.iloc[0]
            logger.info(f"    {sample['chr1']}:{int(sample['start1'])}-{int(sample['end1'])} ({sample['strand1']}) <-> "
                       f"{sample['chr2']}:{int(sample['start2'])}-{int(sample['end2'])} ({sample['strand2']})")
        
        return num_entries
    
    def run_macs3(self,
                  input_file: str,
                  output_prefix: str,
                  format: str = 'BED') -> Dict:
        """Run MACS3 peak calling."""
        logger.info("=" * 70)
        logger.info("Running MACS3 Peak Calling")
        logger.info("=" * 70)
        logger.info(f"  Input: {input_file}")
        logger.info(f"  Format: {format}")
        output_dir = Path(output_prefix).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            'macs3', 'callpeak',
            '-t', input_file,
            '-f', format,
            '-g', self.genome_size,
            '-n', Path(output_prefix).name,
            '--outdir', str(output_dir),
            '-q', str(self.qvalue_cutoff),
            '--keep-dup', self.keep_dup
        ]
        if not self.build_model or True:
            cmd.extend(['--nomodel', '--extsize', '200'])
        if self.broad:
            cmd.append('--broad')
        import shutil
        macs3_available = shutil.which('macs3') is not None
        
        if self.conda_env and not macs3_available:
            cmd = ['conda', 'run', '-n', self.conda_env] + cmd
        elif not macs3_available:
            logger.warning("MACS3 not found in PATH. Trying without conda wrapper...")
        
        logger.info(f"MACS3 command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("MACS3 completed successfully")
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(f"  {line}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"MACS3 failed with error code {e.returncode}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise
        stats = self._parse_macs3_output(output_dir, Path(output_prefix).name)
        
        return stats
    
    def _parse_macs3_output(self, output_dir: Path, name: str) -> Dict:
        """Parse MACS3 output files and extract statistics."""
        stats = {
            'output_dir': str(output_dir),
            'name': name
        }
        if self.broad:
            peaks_file = output_dir / f"{name}_peaks.broadPeak"
            xls_file = output_dir / f"{name}_peaks.broadPeak.xls"
        else:
            peaks_file = output_dir / f"{name}_peaks.narrowPeak"
            summits_file = output_dir / f"{name}_summits.bed"
            xls_file = output_dir / f"{name}_peaks.xls"

        if peaks_file.exists():
            if self.broad:
                peaks_df = pd.read_csv(peaks_file, sep='\t', header=None,
                                      names=['chr', 'start', 'end', 'name', 'score',
                                            'strand', 'signalValue', 'pValue', 'qValue'])
            else:
                peaks_df = pd.read_csv(peaks_file, sep='\t', header=None,
                                      names=['chr', 'start', 'end', 'name', 'score',
                                            'strand', 'signalValue', 'pValue', 'qValue', 'peak'])
            stats['num_peaks'] = len(peaks_df)
            stats['peaks_file'] = str(peaks_file)

            logger.info(f"  Identified {len(peaks_df):,} peaks")
            logger.info(f"  Peaks file: {peaks_file}")

        if not self.broad and summits_file.exists():
            stats['summits_file'] = str(summits_file)
            logger.info(f"  Summits file: {summits_file}")

        if xls_file.exists():
            stats['xls_file'] = str(xls_file)
            logger.info(f"  XLS file: {xls_file}")

        return stats
    
    def call_peaks_from_bam(self, bam_file: str, output_prefix: str) -> Dict:
        """
        Peak calling from BAM file (Method A - Highest Quality).
        
        This is the "correct" method from reference: uses sorted BAM with
        duplicate removal and model building.
        
        Args:
            bam_file: Input sorted BAM file
            output_prefix: Output prefix for results
            
        Returns:
            Dictionary with peak calling statistics
        """
        logger.info("=" * 70)
        logger.info("STEP 5: PEAK CALLING (BAM-based - Highest Quality)")
        logger.info("=" * 70)
        logger.info(f"Input BAM file: {bam_file}")
        logger.info(f"Output prefix: {output_prefix}")
        logger.info(f"Method: BAM with duplicate removal and model building")
        
        # Create output directory
        output_dir = Path(output_prefix).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        import pysam
        with pysam.AlignmentFile(bam_file, 'rb') as bam:
            has_reads = any(True for _ in bam.fetch())
        if not has_reads:
            logger.warning("  BAM file is empty — skipping MACS3 peak calling")
            return {'input_file': bam_file, 'method': 'BAM-based (highest quality)',
                    'num_peaks': 0, 'skipped': True, 'reason': 'empty BAM'}

        stats = self.run_macs3(bam_file, output_prefix, format='BAM')

        # Add input info
        stats['input_file'] = bam_file
        stats['method'] = 'BAM-based (highest quality)'
        
        # Final summary
        self._log_summary(stats)
        
        return stats
    
    def call_peaks_from_bedpe(self, bedpe_file: str, output_prefix: str, 
                              method: str = 'BED') -> Dict:
        """
        Peak calling from BEDPE file.
        
        Supports two methods:
        - 'BED': Convert BEDPE to BED (both anchors) - Standard ChIA-PET
        - 'BEDPE': Use BEDPE directly - Simple approach
        
        Args:
            bedpe_file: Input BEDPE file (sPET or all valid pairs)
            output_prefix: Output prefix for results
            method: 'BED' or 'BEDPE' (default: 'BED')
            
        Returns:
            Dictionary with peak calling statistics
        """
        logger.info("=" * 70)
        logger.info(f"STEP 5: PEAK CALLING ({method}-based)")
        logger.info("=" * 70)
        logger.info(f"Input BEDPE file: {bedpe_file}")
        logger.info(f"Output prefix: {output_prefix}")
        logger.info(f"Method: {method} conversion")
        
        # Create output directory
        output_dir = Path(output_prefix).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        num_entries = self.validate_bedpe(bedpe_file)
        
        if method == 'BED':
            bed_file = f"{output_prefix}.for_macs.bed"
            self.bedpe_to_bed(bedpe_file, bed_file)
            stats = self.run_macs3(bed_file, output_prefix, format='BED')
            stats['bed_file'] = bed_file
        else:
            stats = self.run_macs3(bedpe_file, output_prefix, format='BEDPE')
        
        stats['input_file'] = bedpe_file
        stats['num_entries'] = num_entries
        stats['method'] = f'{method}-based'
        self._log_summary(stats)
        return stats

    def _parse_macs3_output(self, output_dir: Path, name: str) -> Dict:
        """Parse MACS3 output files and extract statistics."""
        stats = {
            'output_dir': str(output_dir),
            'name': name
        }
        if self.broad:
            peaks_file = output_dir / f"{name}_peaks.broadPeak"
            xls_file = output_dir / f"{name}_peaks.broadPeak.xls"
        else:
            peaks_file = output_dir / f"{name}_peaks.narrowPeak"
            summits_file = output_dir / f"{name}_summits.bed"
            xls_file = output_dir / f"{name}_peaks.xls"

        if peaks_file.exists():
            if self.broad:
                peaks_df = pd.read_csv(peaks_file, sep='\t', header=None,
                                      names=['chr', 'start', 'end', 'name', 'score',
                                            'strand', 'signalValue', 'pValue', 'qValue'])
            else:
                peaks_df = pd.read_csv(peaks_file, sep='\t', header=None,
                                      names=['chr', 'start', 'end', 'name', 'score',
                                            'strand', 'signalValue', 'pValue', 'qValue', 'peak'])
            stats['num_peaks'] = len(peaks_df)
            stats['peaks_file'] = str(peaks_file)

            logger.info(f"  Identified {len(peaks_df):,} peaks")
            logger.info(f"  Peaks file: {peaks_file}")

        if not self.broad and summits_file.exists():
            stats['summits_file'] = str(summits_file)
            logger.info(f"  Summits file: {summits_file}")

        if xls_file.exists():
            stats['xls_file'] = str(xls_file)
            logger.info(f"  XLS file: {xls_file}")
        return stats

    def call_peaks(self, input_file: str, output_prefix: str, 
                   input_format: str = 'auto') -> Dict:
        """Auto-detect format and call peaks."""
        if input_format == 'auto':
            if input_file.endswith('.bam'):
                input_format = 'BAM'
            elif input_file.endswith(('.bedpe', '.spet', '.ipet')):
                input_format = 'BED'  
            elif input_file.endswith('.bed'):
                input_format = 'BED'
            else:
                raise ValueError(f"Cannot auto-detect format for: {input_file}")
    
        if input_format == 'BAM':
            return self.call_peaks_from_bam(input_file, output_prefix)
        elif input_format in ['BEDPE', 'BED']:
            method = 'BED' if input_format in ['BEDPE', 'BED'] else input_format
            return self.call_peaks_from_bedpe(input_file, output_prefix, method=method)
        else:
            raise ValueError(f"Cannot auto-detect format for: {input_file}")

    def _log_summary(self, stats: Dict):
        """Log peak calling summary."""
        logger.info("=" * 70)
        logger.info("PEAK CALLING COMPLETE")
        logger.info("=" * 70)
        if 'num_entries' in stats:
            logger.info(f"Input entries: {stats['num_entries']:,}")
        if 'num_peaks' in stats:
            logger.info(f"Total peaks identified: {stats['num_peaks']:,}")
        logger.info(f"Method: {stats.get('method', 'unknown')}")
        logger.info(f"Output files:")
        for key in ['peaks_file', 'summits_file', 'xls_file']:
            if key in stats:
                logger.info(f"  {key}: {stats[key]}")
        logger.info("=" * 70)


def main():
    """Command-line interface for peak calling."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ChIA-PET Peak Calling (Step 5)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python -m chr3d.peak_calling \\
      input.spet \\
      output_prefix
  
  # With custom parameters
  python -m chr3d.peak_calling \\
      input.spet \\
      output_prefix \\
      --genome-size hs \\
      --qvalue 0.01 \\
      --conda-env rowan-hic
        """
    )
    
    parser.add_argument('input_file', help='Input file (BAM, BEDPE, or sPET)')
    parser.add_argument('output_prefix', help='Output prefix for peak files')
    
    parser.add_argument('--genome-size', '-g', default='hs',
                       help='Genome size (hs=human, mm=mouse, or integer) (default: hs)')
    parser.add_argument('--qvalue', '-q', type=float, default=0.05,
                       help='Q-value cutoff (default: 0.05)')
    parser.add_argument('--keep-dup', default='all',
                       help='Duplicate handling: "1"=remove, "all"=keep all (default: all)')
    parser.add_argument('--no-model', action='store_true',
                       help='Do not build MACS3 shift model')
    parser.add_argument('--no-broad', action='store_true',
                       help='Call narrow peaks instead of broad peaks')
    parser.add_argument('--method', choices=['auto', 'BAM', 'BED', 'BEDPE'], default='auto',
                       help='Input format/method (default: auto-detect)')
    parser.add_argument('--conda-env', default='rowan-hic',
                       help='Conda environment name (default: rowan-hic)')
    parser.add_argument('--no-conda', action='store_true',
                       help='Do not use conda environment')
    
    args = parser.parse_args()
    
    peak_caller = PeakCaller(
        genome_size=args.genome_size,
        qvalue_cutoff=args.qvalue,
        keep_dup=args.keep_dup,
        build_model=not args.no_model,
        broad=not args.no_broad,
        conda_env=None if args.no_conda else args.conda_env
    )
    
    try:
        stats = peak_caller.call_peaks(args.input_file, args.output_prefix, 
                                      input_format=args.method)
        logger.info("Peak calling completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Peak calling failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
