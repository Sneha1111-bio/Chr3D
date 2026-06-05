#!/usr/bin/env python3
# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
# This software was developed with support from the National Science Foundation under CAREER Award DBI-2239350.
"""Hi-C Pipeline Quality Report Generator."""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple


def format_number(num: float) -> str:
    """Format large numbers with M, K suffixes."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{int(num)}"


def calc_percent(value: float, total: float) -> float:
    """Calculate percentage as float."""
    if total == 0:
        return 0.0
    return (value / total) * 100


def create_progress_bar(percentage: float, width: int = 40, fill: str = '█', empty: str = '░') -> str:
    """Create a progress bar."""
    percentage = min(100, max(0, percentage))
    filled = int(width * percentage / 100)
    bar = fill * filled + empty * (width - filled)
    return f"[{bar}] {percentage:.1f}%"


def format_stat_line(label: str, value: str, percentage: Optional[float] = None, 
                     bar: bool = False, bar_width: int = 40) -> str:
    """Format a statistic line."""
    if bar and percentage is not None:
        bar_vis = create_progress_bar(percentage, width=bar_width)
        return f"{label:<35} {value:>12}  {bar_vis}"
    elif percentage is not None:
        return f"{label:<35} {value:>12}  ({percentage:.1f}%)"
    else:
        return f"{label:<35} {value:>12}"


def parse_samtools_stats(stats_file: str) -> Dict[str, Any]:
    """Parse samtools stats output file."""
    stats = {}
    
    if not os.path.exists(stats_file):
        return stats
    
    with open(stats_file, 'r') as f:
        for line in f:
            if line.startswith('SN\t'):
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    key = parts[1].rstrip(':')
                    value = parts[2]
                    try:
                        if '.' in value or 'e' in value.lower():
                            stats[key] = float(value)
                        else:
                            stats[key] = int(value)
                    except ValueError:
                        stats[key] = value
    
    return stats


def parse_pairtools_stats(stats_file: str) -> Dict[str, Any]:
    """Parse pairtools stats output file."""
    stats = {}
    
    if not os.path.exists(stats_file):
        return stats
    
    with open(stats_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('\t')
            if len(parts) >= 2:
                key = parts[0]
                value = parts[1]
                try:
                    if '.' in value or 'e' in value.lower():
                        stats[key] = float(value)
                    else:
                        stats[key] = int(value)
                except ValueError:
                    stats[key] = value
    
    return stats


def generate_hic_qc_report(
    qc_dir: str,
    sample_id: str,
    output_file: Optional[str] = None,
    timing_info: Optional[Dict[str, Any]] = None
) -> str:
    """Generate a comprehensive Hi-C QC report."""
    qc_dir = Path(qc_dir)
    bam_stats_file = qc_dir / f"{sample_id}_bam.stats"
    pairs_stats_file = qc_dir / f"{sample_id}_pairs.stats"
    dedup_stats_file = qc_dir / f"{sample_id}_dedup.stats"
    
    bam_stats = parse_samtools_stats(str(bam_stats_file))
    pairs_stats = parse_pairtools_stats(str(pairs_stats_file))
    dedup_stats = parse_pairtools_stats(str(dedup_stats_file))
    lines = []
    lines.append("=" * 80)
    lines.append("║" + " " * 78 + "║")
    title = "HI-C PIPELINE QUALITY REPORT"
    padding = (78 - len(title)) // 2
    lines.append("║" + " " * padding + title + " " * (78 - padding - len(title)) + "║")
    lines.append("║" + " " * 78 + "║")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"📊 Sample: {sample_id}")
    
    if timing_info:
        lines.append(f"🕐 Start:  {timing_info.get('start_time', 'N/A')}")
        lines.append(f"🕐 End:    {timing_info.get('end_time', 'N/A')}")
        lines.append(f"⚙️  Threads: {timing_info.get('threads', 'N/A')}")
        if 'total_duration_formatted' in timing_info:
            lines.append(f"⏱️  Duration: {timing_info['total_duration_formatted']}")
    
    if bam_stats:
        lines.append("")
        lines.append("=" * 80)
        lines.append("=" + " " * 26 + "ALIGNMENT STATISTICS" + " " * 26 + "=")
        lines.append("=" * 80)
        
        total_sequences = bam_stats.get('raw total sequences', 0)
        reads_mapped = bam_stats.get('reads mapped', 0)
        reads_unmapped = bam_stats.get('reads unmapped', 0)
        reads_mq0 = bam_stats.get('reads MQ0', 0)
        error_rate = bam_stats.get('error rate', 0)
        avg_quality = bam_stats.get('average quality', 0)
        insert_size_avg = bam_stats.get('insert size average', 0)
        insert_size_std = bam_stats.get('insert size standard deviation', 0)
        inward_pairs = bam_stats.get('inward oriented pairs', 0)
        outward_pairs = bam_stats.get('outward oriented pairs', 0)
        other_orientation = bam_stats.get('pairs with other orientation', 0)
        diff_chromosomes = bam_stats.get('pairs on different chromosomes', 0)
        lines.append("")
        lines.append("📈 Read Mapping Overview")
        lines.append("-" * 80)
        
        mapping_rate = calc_percent(reads_mapped, total_sequences)
        lines.append(format_stat_line("Total Sequences", format_number(total_sequences)))
        lines.append(format_stat_line("Reads Mapped", format_number(reads_mapped), mapping_rate, bar=True))
        lines.append(format_stat_line("Reads Unmapped", format_number(reads_unmapped), 
                                      calc_percent(reads_unmapped, total_sequences), bar=True))
        lines.append(format_stat_line("Mapping Quality = 0", format_number(reads_mq0),
                                      calc_percent(reads_mq0, reads_mapped), bar=True))
        lines.append("")
        lines.append("🎯 Quality Metrics")
        lines.append("-" * 80)
        lines.append(format_stat_line("Average Quality Score", f"{avg_quality:.1f}"))
        lines.append(format_stat_line("Error Rate", f"{error_rate*100:.2f}%"))
        lines.append(format_stat_line("Average Insert Size", f"{insert_size_avg:.1f} bp"))
        lines.append(format_stat_line("Insert Size Std Dev", f"{insert_size_std:.1f} bp"))
        lines.append("")
        lines.append("🔄 Pair Orientation")
        lines.append("-" * 80)
        total_oriented = inward_pairs + outward_pairs + other_orientation
        if total_oriented > 0:
            lines.append(format_stat_line("Inward Pairs (→ ←)", format_number(inward_pairs),
                                          calc_percent(inward_pairs, total_oriented), bar=True, bar_width=35))
            lines.append(format_stat_line("Outward Pairs (← →)", format_number(outward_pairs),
                                          calc_percent(outward_pairs, total_oriented), bar=True, bar_width=35))
            lines.append(format_stat_line("Other Orientation", format_number(other_orientation),
                                          calc_percent(other_orientation, total_oriented), bar=True, bar_width=35))
        lines.append(format_stat_line("Different Chromosomes", format_number(diff_chromosomes)))
    
    pair_data = dedup_stats if dedup_stats else pairs_stats
    if pair_data:
        lines.append("")
        lines.append("=" * 80)
        lines.append("=" + " " * 28 + "PAIRS STATISTICS" + " " * 28 + "=")
        lines.append("=" * 80)
        
        total_pairs = pair_data.get('total', 0)
        mapped_pairs = pair_data.get('total_mapped', 0)
        unmapped_pairs = pair_data.get('total_unmapped', 0)
        single_sided = pair_data.get('total_single_sided_mapped', 0)
        total_dups = pair_data.get('total_dups', 0)
        total_nodups = pair_data.get('total_nodups', 0)
        cis_contacts = pair_data.get('cis', 0)
        trans_contacts = pair_data.get('trans', 0)
        
        cis_1kb = pair_data.get('cis_1kb+', 0)
        cis_2kb = pair_data.get('cis_2kb+', 0)
        cis_4kb = pair_data.get('cis_4kb+', 0)
        cis_10kb = pair_data.get('cis_10kb+', 0)
        cis_20kb = pair_data.get('cis_20kb+', 0)
        cis_40kb = pair_data.get('cis_40kb+', 0)
        
        frac_cis = pair_data.get('summary/frac_cis', 0)
        cis_short = pair_data.get('cis_1kb', 0)
        lines.append("")
        lines.append("📊 Pair Processing")
        lines.append("-" * 80)
        lines.append(format_stat_line("Total Pairs", format_number(total_pairs)))
        lines.append(format_stat_line("Mapped Pairs", format_number(mapped_pairs),
                                      calc_percent(mapped_pairs, total_pairs), bar=True))
        lines.append(format_stat_line("Unmapped Pairs", format_number(unmapped_pairs),
                                      calc_percent(unmapped_pairs, total_pairs), bar=True))
        lines.append(format_stat_line("Single-Sided Mapped", format_number(single_sided),
                                      calc_percent(total_nodups, total_pairs), bar=True))
        if 'summary/frac_dups' in pair_data:
            lines.append("🔍 Duplicate Analysis")
            lines.append("-" * 80)
            lines.append(format_stat_line("Total Duplicates", format_number(total_dups),
                                          calc_percent(total_dups, mapped_pairs), bar=True))
            lines.append(format_stat_line("Non-Duplicates", format_number(total_nodups),
                                          calc_percent(total_nodups, mapped_pairs), bar=True))
            lines.append(format_stat_line("Unique Pairs", format_number(total_nodups), 100 - pair_data['summary/frac_dups'], bar=True))
        lines.append("")
        lines.append("🧬 Interaction Type")
        lines.append("-" * 80)
        lines.append(format_stat_line("Cis (same chromosome)", format_number(cis_contacts),
                                      calc_percent(cis_contacts, total_nodups), bar=True))
        lines.append(format_stat_line("Trans (different chromosome)", format_number(trans_contacts),
                                      calc_percent(trans_contacts, total_nodups), bar=True))
        
        if trans_contacts > 0:
            cis_trans_ratio = cis_contacts / trans_contacts
            lines.append("")
            lines.append(f"{'Cis/Trans Ratio:':<35} {cis_trans_ratio:.2f}:1")
        lines.append("")
        lines.append("📏 Distance Distribution (Cis Contacts)")
        lines.append("-" * 80)
        if total_nodups > 0:
            lines.append(format_stat_line("≥ 1 KB", format_number(cis_1kb),
                                          calc_percent(cis_1kb, total_nodups), bar=True, bar_width=35))
            lines.append(format_stat_line("≥ 2 KB", format_number(cis_2kb),
                                          calc_percent(cis_2kb, total_nodups), bar=True, bar_width=35))
            lines.append(format_stat_line("≥ 4 KB", format_number(cis_4kb),
                                          calc_percent(cis_4kb, total_nodups), bar=True, bar_width=35))
            lines.append(format_stat_line("≥ 10 KB", format_number(cis_10kb),
                                          calc_percent(cis_10kb, total_nodups), bar=True, bar_width=35))
            lines.append(format_stat_line("≥ 20 KB", format_number(cis_20kb),
                                          calc_percent(cis_20kb, total_nodups), bar=True, bar_width=35))
            lines.append(format_stat_line("≥ 40 KB", format_number(cis_40kb),
                                          calc_percent(cis_40kb, total_nodups), bar=True, bar_width=35))
    
    if timing_info and 'timing' in timing_info:
        lines.append("")
        lines.append("=" * 80)
        lines.append("=" + " " * 28 + "TIMING SUMMARY" + " " * 28 + "=")
        lines.append("=" * 80)
        
        timing = timing_info['timing']
        lines.append("")
        lines.append("⏱️  Step Timing")
        lines.append("-" * 80)
        
        if 'step1_alignment' in timing:
            lines.append(format_stat_line("Step 1 - BWA MEM Alignment", 
                                          _format_duration(timing['step1_alignment'])))
        if 'step2_sam_processing' in timing:
            lines.append(format_stat_line("Step 2 - SAM/BAM Processing",
                                          _format_duration(timing['step2_sam_processing'])))
        if 'step3_pairs_processing' in timing:
            lines.append(format_stat_line("Step 3 - Pairs Processing",
                                          _format_duration(timing['step3_pairs_processing'])))
        if 'step4_contact_matrix' in timing:
            lines.append(format_stat_line("Step 4 - Contact Matrix",
                                          _format_duration(timing['step4_contact_matrix'])))
        
        lines.append("-" * 80)
        if 'total' in timing:
            lines.append(format_stat_line("TOTAL", _format_duration(timing['total'])))
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("=" + " " * 27 + "QUALITY ASSESSMENT" + " " * 27 + "=")
    lines.append("=" * 80)
    mapping_rate = calc_percent(bam_stats.get('reads mapped', 0), 
                                bam_stats.get('raw total sequences', 1)) if bam_stats else 0
    frac_dups = pair_data.get('summary/frac_dups', 0) if pair_data else 0
    frac_cis = pair_data.get('summary/frac_cis', 0) if pair_data else 0
    
    mapping_quality = "✅ EXCELLENT" if mapping_rate > 95 else "⚠️  GOOD" if mapping_rate > 85 else "❌ POOR"
    dup_quality = "✅ EXCELLENT" if frac_dups < 0.1 else "⚠️  MODERATE" if frac_dups < 0.3 else "❌ HIGH"
    cis_quality = "✅ EXCELLENT" if frac_cis > 0.6 else "⚠️  MODERATE" if frac_cis > 0.4 else "❌ LOW"
    
    lines.append("")
    lines.append("🎯 Key Metrics")
    lines.append("-" * 80)
    lines.append(f"{'Mapping Rate:':<35} {mapping_quality:<20} ({mapping_rate:.1f}%)")
    lines.append(f"{'Duplication Rate:':<35} {dup_quality:<20} ({frac_dups*100:.1f}%)")
    lines.append(f"{'Cis Contact Fraction:':<35} {cis_quality:<20} ({frac_cis*100:.1f}%)")
    overall_score = 0
    if mapping_rate > 90:
        overall_score += 1
    if frac_dups < 0.15:
        overall_score += 1
    if frac_cis > 0.55:
        overall_score += 1
    
    lines.append("")
    lines.append("=" * 80)
    if overall_score == 3:
        lines.append("║" + " " * 20 + "🌟 OVERALL QUALITY: EXCELLENT 🌟" + " " * 24 + "║")
    elif overall_score == 2:
        lines.append("║" + " " * 21 + "✅ OVERALL QUALITY: GOOD ✅" + " " * 26 + "║")
    else:
        lines.append("║" + " " * 18 + "⚠️  OVERALL QUALITY: NEEDS REVIEW ⚠️" + " " * 20 + "║")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"📝 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    
    report = '\n'.join(lines)
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
    
    return report


def _format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes ({seconds:.0f}s)"
    else:
        hours = seconds / 3600
        minutes = (seconds % 3600) / 60
        return f"{hours:.1f} hours ({int(hours)}h {int(minutes)}m)"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python qc_report.py <qc_dir> <sample_id> [output_file]")
        sys.exit(1)
    
    qc_dir = sys.argv[1]
    sample_id = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    report = generate_hic_qc_report(qc_dir, sample_id, output_file)
    print(report)
