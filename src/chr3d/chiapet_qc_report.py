#!/usr/bin/env python3
"""ChIA-PET Pipeline Quality Report Generator - Author: Rudra Joshi - Version: 2.0.0"""

import os, yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

def format_number(num, with_commas=False):
    if with_commas: return f"{int(num):,}"
    if num >= 1_000_000: return f"{num/1_000_000:.2f}M"
    elif num >= 1_000: return f"{num/1_000:.1f}K"
    return f"{int(num):,}"

def calc_percent(value, total): return (value / total) * 100 if total > 0 else 0.0

def create_bar(pct, width=26):
    pct = min(100, max(0, pct))
    filled = int(width * pct / 100)
    return f"[{'█' * filled}{'░' * (width - filled)}]"

def format_duration(seconds):
    if seconds < 60: return f"{seconds:.1f}s"
    elif seconds < 3600: return f"{int(seconds/60)}m {int(seconds%60)}s"
    return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m {int(seconds%60)}s"

def parse_qc_file(filepath):
    filepath = Path(filepath)
    if not filepath.exists(): return {}
    try:
        with open(filepath, 'r') as f: content = f.read()
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict): return data
        except: pass
        data, current_section = {}, None
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('='): continue
            if ':' in line:
                key, value = line.split(':', 1)
                key, value = key.strip(), value.strip()
                if not value:
                    current_section = key
                    data[current_section] = {}
                elif current_section:
                    try: data[current_section][key] = float(value) if '.' in value else int(value)
                    except: data[current_section][key] = value
                else:
                    try: data[key] = float(value) if '.' in value else int(value)
                    except: data[key] = value
        return data
    except: return {}

def assess_quality(value, thresholds, invert=False):
    if invert:
        if value <= thresholds['excellent']: return "✅ EXCELLENT"
        elif value <= thresholds['good']: return "✅ GOOD"
        return "❌ POOR"
    else:
        if value >= thresholds['excellent']: return "✅ EXCELLENT"
        elif value >= thresholds['good']: return "✅ GOOD"
        return "❌ POOR"

class ChIAPETReportGenerator:
    def __init__(self, qc_dir, sample_id, output_dir=None, genome="hg38", self_ligation_cutoff=8000, extension_length=500, threads=24):
        self.qc_dir = Path(qc_dir)
        self.sample_id = sample_id
        self.output_dir = output_dir or str(self.qc_dir.parent)
        self.genome = genome
        self.self_ligation_cutoff = self_ligation_cutoff
        self.extension_length = extension_length
        self.threads = threads
        
        self.linker_qc = parse_qc_file(self.qc_dir / f"{sample_id}_01_linker_filtering_qc.txt")
        self.mapping_qc = parse_qc_file(self.qc_dir / f"{sample_id}_02_mapping_qc.txt")
        self.purifying_qc = parse_qc_file(self.qc_dir / f"{sample_id}_03_purifying_qc.txt")
        self.categorization_qc = parse_qc_file(self.qc_dir / f"{sample_id}_04_categorization_qc.txt")
        self.peak_qc = parse_qc_file(self.qc_dir / f"{sample_id}_05_peak_calling_qc.txt")
        self.loop_qc = parse_qc_file(self.qc_dir / f"{sample_id}_06_loop_calling_qc.txt")
        
        self.timestamps = {k: getattr(self, f'{k}_qc', {}).get('Timestamp', 'N/A') for k in ['linker', 'mapping', 'purifying', 'categorization', 'peak', 'loop']}
        self.total_duration = sum(qc.get('timing', {}).get('total_seconds', 0) for qc in [self.linker_qc, self.mapping_qc, self.purifying_qc, self.categorization_qc, self.peak_qc, self.loop_qc])
    
    def _get_metrics(self):
        tr = self.linker_qc.get('total_reads', 0)
        vp = self.linker_qc.get('valid_pets', 0)
        vpairs = self.mapping_qc.get('valid_pairs', 0)
        dups = self.mapping_qc.get('duplicates', 0)
        unique = vpairs - dups if vpairs > 0 else 0
        am = self.purifying_qc.get('after_merge', unique)
        tc = self.categorization_qc.get('total', 0)
        ip = self.categorization_qc.get('ipet', 0)
        sp = self.categorization_qc.get('spet', 0)
        op = self.categorization_qc.get('opet', 0)
        ci = self.categorization_qc.get('cis', 0)
        tr2 = self.categorization_qc.get('trans', 0)
        np = self.peak_qc.get('num_peaks', 0)
        nl = self.loop_qc.get('significant_loops', self.loop_qc.get('num_significant_loops', 0))
        return {'total_reads': tr, 'valid_pets': vp, 'valid_pairs': vpairs, 'duplicates': dups, 'unique_pets': unique, 'after_merge': am, 'total_cat': tc, 'ipet': ip, 'spet': sp, 'opet': op, 'cis': ci, 'trans': tr2, 'num_peaks': np, 'num_loops': nl, 'linker_rate': calc_percent(vp, tr), 'map_rate': calc_percent(vpairs, vp), 'dup_rate': calc_percent(dups, vpairs), 'ipet_pct': calc_percent(ip, tc), 'spet_pct': calc_percent(sp, tc), 'opet_pct': calc_percent(op, tc), 'cis_trans_ratio': ci / tr2 if tr2 > 0 else 0}
    
    def _assess_overall(self):
        m = self._get_metrics()
        score = sum([m['linker_rate'] > 85, m['map_rate'] > 12, m['dup_rate'] < 40, 35 <= m['ipet_pct'] <= 45, 25 <= m['spet_pct'] <= 35, m['opet_pct'] < 30, m['cis_trans_ratio'] > 10, m['num_peaks'] > 3000, m['num_loops'] > 10000])
        if score >= 7: return "✅ EXCELLENT"
        elif score >= 5: return "⚠️  GOOD"
        return "❌ NEEDS REVIEW"
    
    def generate_report(self, output_file=None):
        m = self._get_metrics()
        L = []
        L.extend(["=" * 80, "║" + " " * 78 + "║", "║" + " " * 18 + "🧬 ChIA-PET PIPELINE QUALITY REPORT 🧬" + " " * 19 + "║", "║" + " " * 78 + "║", "=" * 80, ""])
        L.extend(["📊 Sample Information", "─" * 80, f"Sample ID:                          {self.sample_id}", f"Analysis Mode:                      ChIA-PET"])
        ts = [t for t in self.timestamps.values() if t != 'N/A']
        if ts: L.extend([f"Start Time:                         {ts[0]}", f"End Time:                           {ts[-1]}"])
        if self.total_duration > 0: L.append(f"Total Duration:                     {format_duration(self.total_duration)}")
        L.extend([f"Threads Used:                       {self.linker_qc.get('performance', {}).get('threads', self.threads)}", f"Reference Genome:                   {self.genome}", f"Self-Ligation Cutoff:               {self.self_ligation_cutoff:,} bp", f"Extension Length:                   {self.extension_length} bp", ""])
        L.extend(["=" * 80, " " * 26 + "📈 PIPELINE OVERVIEW" + " " * 26, "=" * 80, "", "Stage                    Input           Output          Pass Rate      Status", "─" * 80])
        s1 = "✅ PASS" if m['linker_rate'] > 85 else "⚠️  WARN" if m['linker_rate'] > 70 else "❌ FAIL"
        L.append(f"1. Linker Filtering      {format_number(m['total_reads']):>8} reads    {format_number(m['valid_pets']):>8} PETs   {m['linker_rate']:>5.1f}%         {s1}")
        s2 = "✅ PASS" if m['map_rate'] > 12 else "⚠️  WARN" if m['map_rate'] > 8 else "❌ FAIL"
        L.append(f"2. Genomic Mapping       {format_number(m['valid_pets']):>8} PETs     {format_number(m['valid_pairs']):>8} pairs  {m['map_rate']:>5.1f}%         {s2}")
        s3 = "✅ PASS" if m['dup_rate'] < 40 else "⚠️  WARN" if m['dup_rate'] < 60 else "❌ FAIL"
        L.append(f"3. Deduplication        {format_number(m['valid_pairs']):>8} pairs    {format_number(m['unique_pets']):>8} unique {100-m['dup_rate']:>5.1f}%         {s3}")
        if m['after_merge'] > 0:
            pr = calc_percent(m['after_merge'], m['unique_pets'])
            s4 = "✅ PASS" if pr > 95 else "⚠️  WARN"
            L.append(f"4. PET Purification      {format_number(m['unique_pets']):>8} PETs     {format_number(m['after_merge']):>8} valid  {pr:>5.1f}%         {s4}")
        if m['total_cat'] > 0: L.append(f"5. Categorization        {format_number(m['after_merge']):>8} PETs     Classified       100.0%         ✅ PASS")
        if m['num_peaks'] > 0 or m['spet'] > 0:
            s6 = "✅ PASS" if m['num_peaks'] > 3000 else "⚠️  WARN" if m['num_peaks'] > 1000 else "❌ FAIL"
            L.append(f"6. Peak Calling          {format_number(m['spet']):>8} sPETs    {format_number(m['num_peaks']):>8} peaks  N/A            {s6}")
        if m['num_loops'] > 0 or m['ipet'] > 0:
            s7 = "✅ PASS" if m['num_loops'] > 10000 else "⚠️  WARN" if m['num_loops'] > 5000 else "❌ FAIL"
            L.append(f"7. Loop Calling          {format_number(m['ipet']):>8} iPETs    {format_number(m['num_loops']):>8} loops  N/A            {s7}")
        L.extend(["", f"Overall Pipeline Status: {self._assess_overall()}", ""])
        L.extend(["=" * 80, " " * 20 + "🔬 STEP 1: LINKER FILTERING DETAILS" + " " * 25, "=" * 80, "", "📥 Input Data", "─" * 80, f"Total Read Pairs:                   {format_number(m['total_reads'], True)}", "", "🔍 Linker Detection", "─" * 80, f"Valid PETs (same linker):          {format_number(m['valid_pets'], True):>12}          {create_bar(m['linker_rate'])} {m['linker_rate']:.1f}%"])
        comp = self.linker_qc.get('linker_composition', {})
        if isinstance(comp, dict):
            for k, v in comp.items():
                if isinstance(v, (int, float)):
                    L.append(f"  ├─ {k}:             {format_number(v, True):>12}          ({calc_percent(v, m['valid_pets']):.1f}%)")
        L.extend(["", "❌ Filtered Out", "─" * 80])
        for key, label in [('failed_alignment_score', 'Low Alignment Score'), ('failed_tag_length', 'Tag Too Short/Long'), ('failed_ambiguous_linker', 'Ambiguous Linker')]:
            val = self.linker_qc.get(key, 0)
            if val > 0:
                pct = calc_percent(val, m['total_reads'])
                L.append(f"{label}:                {format_number(val, True):>12}          {create_bar(pct)} {pct:.1f}%")
        perf = self.linker_qc.get('performance', {})
        if perf:
            L.extend(["", "⚙️ Performance", "─" * 80])
            if 'reads_per_second' in perf: L.append(f"Processing Speed:                   {format_number(perf['reads_per_second'], True)} reads/sec")
            if 'alignments_per_second' in perf: L.append(f"Alignment Speed:                    {format_number(perf['alignments_per_second'], True)} alignments/sec")
            if 'simd' in perf: L.append(f"SIMD Acceleration:                  {perf['simd'].upper() if perf['simd'] != 'scalar' else 'Disabled'}")
            if 'threads' in perf: L.append(f"Threads:                            {perf['threads']}")
        timing = self.linker_qc.get('timing', {})
        if 'total_seconds' in timing: L.append(f"Processing Time:                    {format_duration(timing['total_seconds'])}")
        if m['linker_rate'] >= 85: L.extend(["", "✅ ASSESSMENT: EXCELLENT", f"   - {m['linker_rate']:.1f}% pass rate exceeds minimum 85% threshold"])
        elif m['linker_rate'] >= 70: L.extend(["", "⚠️  ASSESSMENT: GOOD", f"   - {m['linker_rate']:.1f}% pass rate is acceptable"])
        else: L.extend(["", "❌ ASSESSMENT: POOR", f"   - {m['linker_rate']:.1f}% pass rate is LOW"])
        L.append("")
        L.extend(["=" * 80, " " * 20 + "🗺️  STEP 2: GENOMIC MAPPING DETAILS" + " " * 22, "=" * 80, "", "📍 Alignment Summary", "─" * 80, f"Input Read Pairs:                   {format_number(m['valid_pets'], True)}", f"BWA Algorithm:                      BWA-MEM (paired-end)", f"Mapping Quality Cutoff:             ≥ 30 (uniquely mapped)", "", "🎯 Mapping Results", "─" * 80, f"Uniquely Mapped Pairs:             {format_number(m['valid_pairs'], True):>12}          {create_bar(m['map_rate'])} {m['map_rate']:.1f}%"])
        intra = self.mapping_qc.get('intra_chromosomal', 0)
        if m['valid_pairs'] > 0:
            L.append(f"  ├─ Both ends mapped (MQ≥30):     {format_number(m['valid_pairs'], True):>12}          (100%)")
            if intra > 0: L.append(f"  └─ Intra-chromosomal:            {format_number(intra, True):>12}          ({calc_percent(intra, m['valid_pairs']):.1f}%)")
        L.extend(["", "❌ Filtered Out", "─" * 80])
        unmapped = self.mapping_qc.get('unmapped', 0)
        low_q = self.mapping_qc.get('low_quality', 0)
        if unmapped > 0: L.append(f"Unmapped (one/both ends):          {format_number(unmapped, True):>12}          {create_bar(calc_percent(unmapped, m['valid_pets']))} {calc_percent(unmapped, m['valid_pets']):.1f}%")
        if low_q > 0: L.append(f"Low Mapping Quality (<30):         {format_number(low_q, True):>12}          {create_bar(calc_percent(low_q, m['valid_pets']))} {calc_percent(low_q, m['valid_pets']):.1f}%")
        L.extend(["", "*Note: ChIA-PET doesn't require \"proper pair\" - chromatin interactions have", "       diverse orientations unlike standard paired-end sequencing."])
        timing = self.mapping_qc.get('timing', {})
        if timing: L.extend(["", "⏱️ Performance", "─" * 80])
        if 'total_seconds' in timing: L.append(f"Alignment Time:                     {format_duration(timing['total_seconds'])}")
        if m['map_rate'] >= 12: L.extend(["", "✅ ASSESSMENT: EXCELLENT", f"   - {m['map_rate']:.1f}% mapping rate matches expected range (12-18%)"])
        elif m['map_rate'] >= 8: L.extend(["", "⚠️  ASSESSMENT: GOOD", f"   - {m['map_rate']:.1f}% mapping rate is acceptable"])
        else: L.extend(["", "❌ ASSESSMENT: POOR", f"   - {m['map_rate']:.1f}% mapping rate is LOW"])
        L.append("")
        L.extend(["=" * 80, " " * 24 + "🔄 STEP 3: PCR DEDUPLICATION" + " " * 28, "=" * 80, "", "📥 Input", "─" * 80, f"Total Mapped Pairs:                {format_number(m['valid_pairs'], True):>12}", "", "🧹 Deduplication Results", "─" * 80])
        if m['valid_pairs'] > 0:
            up = 100 - m['dup_rate']
            L.extend([f"Unique PETs (non-duplicate):        {format_number(m['unique_pets'], True):>12}          {create_bar(up)} {up:.1f}%", f"PCR Duplicates Removed:             {format_number(m['duplicates'], True):>12}          {create_bar(m['dup_rate'])} {m['dup_rate']:.1f}%", "", f"Duplication Rate:                   {m['dup_rate']:.1f}%", "", "📊 Complexity Assessment", "─" * 80])
            cx = "EXCELLENT" if m['dup_rate'] < 20 else "HIGH" if m['dup_rate'] < 40 else "MODERATE" if m['dup_rate'] < 60 else "LOW"
            L.append(f"Library Complexity:                 {cx}")
            if m['dup_rate'] < 40: L.extend(["", "✅ ASSESSMENT: GOOD", f"   - {m['dup_rate']:.1f}% duplication rate is acceptable (<40%)", f"   - {up:.1f}% unique pairs retained"])
            elif m['dup_rate'] < 60: L.extend(["", "⚠️  ASSESSMENT: MODERATE", f"   - {m['dup_rate']:.1f}% duplication rate is moderate"])
            else: L.extend(["", "❌ ASSESSMENT: POOR", f"   - {m['dup_rate']:.1f}% duplication rate is HIGH"])
        L.append("")
        L.extend(["=" * 80, " " * 24 + "🧬 STEP 4: PET PURIFICATION" + " " * 29, "=" * 80, "", "📥 Input", "─" * 80, f"Deduplicated PETs:                  {format_number(m['unique_pets'], True):>12}", "", "🔧 Purification (ChIA-PET Merging)", "─" * 80])
        if m['unique_pets'] > 0:
            mp = calc_percent(m['after_merge'], m['unique_pets'])
            L.extend([f"Valid PETs After Merge:             {format_number(m['after_merge'], True):>12}          {create_bar(mp)} {mp:.1f}%", f"Merge Distance:                     2 bp (default)"])
            if mp >= 95: L.extend(["", "✅ ASSESSMENT: EXCELLENT", f"   - {mp:.1f}% retention rate (minimal loss)"])
            else: L.extend(["", "⚠️  ASSESSMENT: GOOD", f"   - {mp:.1f}% retention rate"])
        L.append("")
        L.extend(["=" * 80, " " * 16 + "🏷️  STEP 5: PET CATEGORIZATION (KEY RESULTS)" + " " * 19, "=" * 80, "", "📥 Input", "─" * 80, f"Total Valid PETs:                   {format_number(m['total_cat'], True):>12}", "", "🔬 PET Classification by Interaction Type", "─" * 80, ""])
        if m['total_cat'] > 0:
            L.extend([f"📍 iPET (Inter-ligation Products) - Used for LOOP CALLING", f"    └─ Long-range chromatin interactions (>{self.self_ligation_cutoff//1000}kb or trans)", "", f"    Total iPETs:                    {format_number(m['ipet'], True):>12}          {create_bar(m['ipet_pct'])} {m['ipet_pct']:.1f}%", "", f"📍 sPET (Self-ligation Products) - Used for PEAK CALLING", f"    └─ Short-range self-ligated fragments (<{self.self_ligation_cutoff//1000}kb)", "", f"    Total sPETs:                    {format_number(m['spet'], True):>12}          {create_bar(m['spet_pct'])} {m['spet_pct']:.1f}%", "", f"📍 oPET (Other/Invalid Products) - FILTERED OUT", f"    └─ Invalid strand orientations", "", f"    Total oPETs:                    {format_number(m['opet'], True):>12}          {create_bar(m['opet_pct'])} {m['opet_pct']:.1f}%", "", "📊 Cis vs Trans Ratio", "─" * 80])
            cp = calc_percent(m['cis'], m['total_cat'])
            tp = calc_percent(m['trans'], m['total_cat'])
            L.extend([f"Cis Interactions:                   {format_number(m['cis'], True):>12}          {create_bar(cp)} {cp:.1f}%", f"Trans Interactions:                   {format_number(m['trans'], True):>12}          {create_bar(tp)} {tp:.1f}%"])
            if m['cis_trans_ratio'] > 0: L.extend(["", f"Cis/Trans Ratio:                    {m['cis_trans_ratio']:.1f}:1"])
            sc = sum([35 <= m['ipet_pct'] <= 45, 25 <= m['spet_pct'] <= 35, m['opet_pct'] < 30, m['cis_trans_ratio'] > 10])
            q = "EXCELLENT" if sc >= 3 else "GOOD" if sc >= 2 else "NEEDS REVIEW"
            L.extend(["", f"✅ ASSESSMENT: {q}", f"   - iPET ratio ({m['ipet_pct']:.1f}%): {'matches expected 35-45% range' if 35 <= m['ipet_pct'] <= 45 else 'outside expected range'}", f"   - sPET ratio ({m['spet_pct']:.1f}%): {'matches expected 25-35% range' if 25 <= m['spet_pct'] <= 35 else 'outside expected range'}", f"   - oPET ratio ({m['opet_pct']:.1f}%): {'within acceptable <30% threshold' if m['opet_pct'] < 30 else 'HIGH'}"])
            if m['cis_trans_ratio'] > 10: L.append(f"   - Cis/Trans ratio ({m['cis_trans_ratio']:.1f}:1): indicates strong enrichment")
            L.extend(["", "📖 INTERPRETATION:", "   • High iPET percentage: Good for detecting long-range loops", "   • Balanced sPET: Adequate for anchor peak identification", "   • Low oPET: High data quality and proper ligation"])
            if m['cis_trans_ratio'] > 10: L.append("   • High Cis/Trans: Successful chromatin interaction capture")
        L.append("")
        L.extend(["=" * 80, " " * 20 + "⛰️  STEP 6: PEAK CALLING (MACS3)" + " " * 25, "=" * 80, "", "📥 Input", "─" * 80, f"sPET Count:                         {format_number(m['spet'], True):>12}", f"Genome Size:                        hs (Homo sapiens)", f"Q-value Cutoff:                     0.05 (FDR 5%)", "", "🏔️ Peak Detection Results", "─" * 80, f"Significant Peaks Called:           {format_number(m['num_peaks'], True):>12} peaks", ""])
        if m['num_peaks'] >= 3000: L.extend(["✅ ASSESSMENT: EXCELLENT", f"   - {format_number(m['num_peaks'], True)} peaks is typical for ChIA-PET"])
        elif m['num_peaks'] >= 1000: L.extend(["⚠️  ASSESSMENT: GOOD", f"   - {format_number(m['num_peaks'], True)} peaks detected"])
        else: L.extend(["❌ ASSESSMENT: LOW", f"   - {format_number(m['num_peaks'], True)} peaks is below expected"])
        L.append("")
        L.extend(["=" * 80, " " * 20 + "🔗 STEP 7: LOOP CALLING (STATISTICAL)" + " " * 21, "=" * 80, "", "📥 Input", "─" * 80, f"iPET Count:                         {format_number(m['ipet'], True):>12}", f"Extension Length:                   {self.extension_length} bp", f"iPET Threshold:                     ≥ 2 PETs per cluster", f"FDR Cutoff:                         0.05 (5%)", "", "�� Loop Detection Results", "─" * 80])
        nc = self.loop_qc.get('num_clusters', 0)
        if nc > 0: L.append(f"Total Clusters Tested:              {format_number(nc, True):>12}")
        L.append(f"Significant Loops (FDR < 0.05):     {format_number(m['num_loops'], True):>12}")
        hc = self.loop_qc.get('high_confidence_loops', 0)
        if hc > 0: L.append(f"High Confidence (FDR < 0.01):       {format_number(hc, True):>12}")
        L.append("")
        if m['num_loops'] >= 10000: L.extend(["✅ ASSESSMENT: EXCELLENT", f"   - {format_number(m['num_loops'], True)} loops is robust for ChIA-PET"])
        elif m['num_loops'] >= 5000: L.extend(["⚠️  ASSESSMENT: GOOD", f"   - {format_number(m['num_loops'], True)} significant loops detected"])
        else: L.extend(["❌ ASSESSMENT: LOW", f"   - {format_number(m['num_loops'], True)} loops is below expected"])
        L.append("")
        L.extend(["=" * 80, " " * 28 + "⏱️  TIMING BREAKDOWN" + " " * 30, "=" * 80, "", "Pipeline Stage              Duration          % of Total    Throughput", "─" * 80])
        total = self.total_duration if self.total_duration > 0 else 1
        for name, qc, ic, unit in [("1. Linker Filtering", self.linker_qc, m['total_reads'], "reads/sec"), ("2. Genomic Mapping", self.mapping_qc, m['valid_pets'], "pairs/sec"), ("3. Categorization", self.categorization_qc, m['total_cat'], "PETs/sec")]:
            t = qc.get('timing', {}).get('total_seconds', 0)
            if t > 0:
                pct = calc_percent(t, total)
                tp = f"{int(ic/t):,} {unit}" if t > 0 else "N/A"
                L.append(f"{name:<28}{format_duration(t):>12}          {pct:>5.1f}%          {tp}")
        L.extend(["─" * 80, f"TOTAL PIPELINE TIME         {format_duration(total):>12}          100.0%", ""])
        L.extend(["=" * 80, " " * 24 + "🎯 QUALITY ASSESSMENT SUMMARY" + " " * 27, "=" * 80, "", "Metric                          Value           Threshold       Status", "─" * 80])
        L.append(f"Linker Pass Rate                {m['linker_rate']:>5.1f}%           > 85%           {assess_quality(m['linker_rate'], {'excellent': 85, 'good': 70, 'poor': 0})}")
        L.append(f"Mapping Rate                    {m['map_rate']:>5.1f}%           12-18%          {assess_quality(m['map_rate'], {'excellent': 12, 'good': 8, 'poor': 0})}")
        L.append(f"Duplication Rate                {m['dup_rate']:>5.1f}%           < 40%           {assess_quality(m['dup_rate'], {'excellent': 40, 'good': 60, 'poor': 100}, True)}")
        ips = "✅ EXCELLENT" if 35 <= m['ipet_pct'] <= 45 else "⚠️  GOOD" if 25 <= m['ipet_pct'] <= 50 else "❌ OUT OF RANGE"
        L.append(f"iPET Ratio                      {m['ipet_pct']:>5.1f}%           35-45%          {ips}")
        sps = "✅ EXCELLENT" if 25 <= m['spet_pct'] <= 35 else "⚠️  GOOD" if 20 <= m['spet_pct'] <= 40 else "❌ OUT OF RANGE"
        L.append(f"sPET Ratio                      {m['spet_pct']:>5.1f}%           25-35%          {sps}")
        L.append(f"oPET Ratio                      {m['opet_pct']:>5.1f}%           < 30%           {assess_quality(m['opet_pct'], {'excellent': 30, 'good': 40, 'poor': 100}, True)}")
        if m['cis_trans_ratio'] > 0: L.append(f"Cis/Trans Ratio                 {m['cis_trans_ratio']:>5.1f}:1          > 10:1          {assess_quality(m['cis_trans_ratio'], {'excellent': 10, 'good': 5, 'poor': 0})}")
        if m['num_peaks'] > 0:
            pks = "✅ EXCELLENT" if m['num_peaks'] > 3000 else "⚠️  GOOD" if m['num_peaks'] > 1000 else "❌ LOW"
            L.append(f"Peaks Called                    {format_number(m['num_peaks']):>8}           > 3,000         {pks}")
        if m['num_loops'] > 0:
            lps = "✅ EXCELLENT" if m['num_loops'] > 10000 else "⚠️  GOOD" if m['num_loops'] > 5000 else "❌ LOW"
            L.append(f"Significant Loops               {format_number(m['num_loops']):>8}           > 10,000        {lps}")
        overall = self._assess_overall()
        L.extend(["", "=" * 80])
        if "EXCELLENT" in overall: L.extend(["║" + " " * 78 + "║", "║" + " " * 19 + "🌟 OVERALL QUALITY: EXCELLENT 🌟" + " " * 24 + "║", "║" + " " * 78 + "║", "║   Your ChIA-PET data shows exceptional quality across all metrics.          ║", "║   Results are publication-ready with strong statistical confidence.         ║"])
        elif "GOOD" in overall: L.extend(["║" + " " * 78 + "║", "║" + " " * 21 + "✅ OVERALL QUALITY: GOOD ✅" + " " * 26 + "║", "║" + " " * 78 + "║", "║   Your ChIA-PET data shows good quality in most metrics.                    ║", "║   Results are suitable for downstream analysis.                             ║"])
        else: L.extend(["║" + " " * 78 + "║", "║" + " " * 18 + "⚠️  OVERALL QUALITY: NEEDS REVIEW ⚠️" + " " * 20 + "║", "║" + " " * 78 + "║", "║   Some quality metrics are below optimal ranges.                            ║", "║   Review individual sections for improvement recommendations.               ║"])
        L.extend(["║" + " " * 78 + "║", "=" * 80, "", "📊 Data Recommendation", "─" * 80])
        if "EXCELLENT" in overall or "GOOD" in overall: L.extend(["✅ Proceed with downstream analysis", "✅ Data suitable for biological interpretation"])
        else: L.append("⚠️  Review quality metrics before proceeding")
        L.extend(["", f"📝 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"📁 Output Directory: {self.output_dir}", f"🔬 Pipeline Version: Chr3D v3.2.0", "=" * 80])
        report = '\n'.join(L)
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f: f.write(report)
        return report

def generate_chiapet_report(qc_dir, sample_id, output_file=None, output_dir=None, genome="hg38", self_ligation_cutoff=8000, extension_length=500, threads=24):
    return ChIAPETReportGenerator(qc_dir=qc_dir, sample_id=sample_id, output_dir=output_dir, genome=genome, self_ligation_cutoff=self_ligation_cutoff, extension_length=extension_length, threads=threads).generate_report(output_file)

def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: python chiapet_qc_report.py <qc_dir> <sample_id> [output_file]")
        sys.exit(1)
    print(generate_chiapet_report(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))

if __name__ == "__main__":
    main()
