# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
"""Restriction Site Generator for HiChIP Analysis."""

import re
import logging
from typing import List, Dict, Tuple
from pathlib import Path

from .logging import get_logger

logger = get_logger(__name__)


class RestrictionSiteGenerator:
    """Generate restriction fragment coordinates from genome FASTA."""
    
    COMMON_ENZYMES = {
        'MboI': '^GATC',
        'HindIII': 'A^AGCTT',
        'DpnII': '^GATC',
        'BglII': 'A^GATCT',
        'Sau3AI': '^GATC',
        'Hinf1': 'G^ANTC',
        'NlaIII': 'CATG^',
        'AluI': 'AG^CT',
        'EcoRI': 'G^AATTC',
        'BamHI': 'G^GATCC',
        'PstI': 'CTGCA^G',
        'SalI': 'G^TCGAC',
        'XbaI': 'T^CTAGA'
    }
    
    def __init__(self, 
                 enzyme: str or List[str],
                 min_frag_size: int = 20,
                 max_frag_size: int = 1000000):
        """Initialize restriction site generator."""
        self.min_frag_size = min_frag_size
        self.max_frag_size = max_frag_size
        if isinstance(enzyme, str):
            enzyme = [enzyme]
        self.enzymes = []
        self.enzyme_names = []
        for enz in enzyme:
            site, name = self._parse_enzyme(enz)
            self.enzymes.append(site)
            self.enzyme_names.append(name)
        
        logger.info(f"RestrictionSiteGenerator initialized")
        logger.info(f"  Enzymes: {', '.join(self.enzyme_names)}")
        logger.info(f"  Recognition sites: {', '.join(self.enzymes)}")
        logger.info(f"  Fragment size range: {min_frag_size}-{max_frag_size}bp")
    
    def _parse_enzyme(self, enzyme: str) -> Tuple[str, str]:
        """Parse enzyme name or recognition site."""
        if enzyme in self.COMMON_ENZYMES:
            return self.COMMON_ENZYMES[enzyme], enzyme
        if '^' not in enzyme:
            raise ValueError(f"Recognition site must contain '^' to indicate cut position: {enzyme}")
        site_no_cut = enzyme.replace('^', '')
        if not all(c in 'ATCGN' for c in site_no_cut.upper()):
            raise ValueError(f"Recognition site contains invalid characters: {enzyme}")
        
        return enzyme.upper(), enzyme
    
    def _find_cut_position(self, recognition_site: str) -> int:
        """Find the cut position in recognition site."""
        cut_pos = recognition_site.index('^')
        return cut_pos
    
    def _find_restriction_sites(self, sequence: str, recognition_sites: List[str]) -> List[Tuple[int, int]]:
        """Find all restriction sites in a sequence."""
        sites = []
        for enzyme_idx, site in enumerate(recognition_sites):
            pattern = site.replace('N', '[ATCG]')
            pattern = pattern.replace('R', '[AG]')
            pattern = pattern.replace('Y', '[CT]')
            pattern = pattern.replace('W', '[AT]')
            pattern = pattern.replace('S', '[GC]')
            pattern = pattern.replace('M', '[AC]')
            pattern = pattern.replace('K', '[GT]')
            
            for match in re.finditer(pattern, sequence):
                sites.append((match.start(), enzyme_idx))
        sites.sort(key=lambda x: x[0])
        
        return sites
    
    def generate_sites(self,
                      genome_fasta: str,
                      output_file: str) -> Dict:
        """Generate restriction fragment file from genome FASTA."""
        logger.info(f"Input genome: {genome_fasta}")
        logger.info(f"Output file: {output_file}")
        cut_positions = [self._find_cut_position(site) for site in self.enzymes]
        recognition_sites = [site.replace('^', '') for site in self.enzymes]
        logger.info(f"Cut positions: {cut_positions}")
        logger.info(f"Recognition sites (no cut): {recognition_sites}")
        stats = {
            'total_fragments': 0,
            'filtered_fragments': 0,
            'chromosomes': 0,
            'total_sites': 0,
            'fragments_by_chr': {}
        }
        
        with open(output_file, 'w') as out_f:
            current_chr = None
            chr_sequence = []
            
            logger.info("\nProcessing genome FASTA...")
            with open(genome_fasta, 'r') as fasta_f:
                for line in fasta_f:
                    line = line.strip()
                    if line.startswith('>'):
                        if current_chr is not None and chr_sequence:
                            self._process_chromosome(
                                current_chr,
                                ''.join(chr_sequence),
                                recognition_sites,
                                cut_positions,
                                out_f,
                                stats
                            )
                        current_chr = line[1:].split()[0]
                        chr_sequence = []
                        stats['chromosomes'] += 1
                    else:
                        chr_sequence.append(line.upper())
                
                if current_chr is not None and chr_sequence:
                    self._process_chromosome(
                        current_chr,
                        ''.join(chr_sequence),
                        recognition_sites,
                        cut_positions,
                        out_f,
                        stats
                    )
        
        # Print summary
        logger.info("=" * 70)
        logger.info("RESTRICTION SITE GENERATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Chromosomes processed: {stats['chromosomes']}")
        logger.info(f"Total restriction sites: {stats['total_sites']:,}")
        logger.info(f"Total fragments: {stats['total_fragments']:,}")
        logger.info(f"Filtered fragments (size): {stats['filtered_fragments']:,}")
        logger.info(f"Final fragments: {stats['total_fragments'] - stats['filtered_fragments']:,}")
        logger.info(f"Output file: {output_file}")
        logger.info("=" * 70)
        
        return stats
    
    def _process_chromosome(self,
                           chrom: str,
                           sequence: str,
                           recognition_sites: List[str],
                           cut_positions: List[int],
                           out_file,
                           stats: Dict):
        """
        Process a single chromosome to output restriction FRAGMENTS.
        
        Outputs the genomic intervals BETWEEN consecutive restriction cuts.
        This is what HiChIP same-fragment removal needs - to check if both
        ends of a PET fall within the same fragment interval.
        
        Args:
            chrom: Chromosome name
            sequence: Chromosome sequence (uppercase)
            recognition_sites: List of recognition sites (no '^')
            cut_positions: List of cut positions for each site
            out_file: Output file handle
            stats: Statistics dictionary to update
        
        Reference: Main.java split_genome_byressite() and HiC-Pro digest_genome.py
        """
        chr_len = len(sequence)
        
        # Find all restriction sites
        sites = self._find_restriction_sites(sequence, recognition_sites)
        
        if not sites:
            logger.warning(f"  {chrom}: No restriction sites found (length: {chr_len:,}bp)")
            # Write entire chromosome as one fragment
            out_file.write(f"{chrom}\t0\t{chr_len}\n")
            stats['total_fragments'] += 1
            stats['fragments_by_chr'][chrom] = 1
            return
        
        cut_coords = []
        for site_pos, enzyme_idx in sites:
            actual_cut = site_pos + cut_positions[enzyme_idx]
            cut_coords.append(actual_cut)
        
        cut_coords = [0] + sorted(set(cut_coords)) + [chr_len]
        
        frag_count = 0
        for i in range(len(cut_coords) - 1):
            frag_start = cut_coords[i]
            frag_end = cut_coords[i + 1]
            frag_size = frag_end - frag_start
            
            if self.min_frag_size <= frag_size <= self.max_frag_size:
                out_file.write(f"{chrom}\t{frag_start}\t{frag_end}\n")
                frag_count += 1
            else:
                stats['filtered_fragments'] += 1
            
            stats['total_fragments'] += 1
        
        stats['total_sites'] += len(sites)
        stats['fragments_by_chr'][chrom] = frag_count
        
        logger.info(f"  {chrom}: {len(sites):,} sites → {frag_count:,} fragments (length: {chr_len:,}bp)")


def main():
    """Example usage of RestrictionSiteGenerator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate restriction fragment coordinates from genome FASTA'
    )
    parser.add_argument('--genome', required=True, help='Genome FASTA file')
    parser.add_argument('--enzyme', required=True, help='Enzyme name (MboI, HindIII) or site (^GATC)')
    parser.add_argument('--output', required=True, help='Output BED file')
    parser.add_argument('--min-size', type=int, default=20, help='Minimum fragment size (default: 20)')
    parser.add_argument('--max-size', type=int, default=1000000, help='Maximum fragment size (default: 1000000)')
    
    args = parser.parse_args()
    generator = RestrictionSiteGenerator(
        enzyme=args.enzyme,
        min_frag_size=args.min_size,
        max_frag_size=args.max_size
    )
    
    stats = generator.generate_sites(args.genome, args.output)
    
    print(f"\nGenerated {stats['total_fragments'] - stats['filtered_fragments']:,} restriction fragments")
    print(f"Output: {args.output}")


if __name__ == '__main__':
    main()
