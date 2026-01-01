"""
Restriction Site Generator for HiChIP Analysis

This module generates restriction fragment coordinates from a genome FASTA file
based on restriction enzyme recognition sites. This is a critical step for HiChIP
data processing to identify and remove same-fragment PETs.

Reference: ChIA-PET Tool V3 - Main.java split_genome_byressite() (lines 121-230)
"""

import re
import logging
from typing import List, Dict, Tuple
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RestrictionSiteGenerator:
    """
    Generate restriction fragment coordinates from genome FASTA.
    
    This class parses restriction enzyme recognition sites and scans a genome
    FASTA file to identify all restriction sites, creating fragments between
    consecutive cut positions.
    
    Reference: ChIA-PET Tool V3 Main.java split_genome_byressite()
    """
    
    # Common restriction enzymes and their recognition sites
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
        """
        Initialize restriction site generator.
        
        Args:
            enzyme: Enzyme name (e.g., 'MboI') or recognition site (e.g., '^GATC')
                   Can be a list for multiple enzymes (e.g., ['MboI', 'HindIII'])
            min_frag_size: Minimum fragment length to keep (default: 20bp)
            max_frag_size: Maximum fragment length to keep (default: 1Mb)
        """
        self.min_frag_size = min_frag_size
        self.max_frag_size = max_frag_size
        
        # Parse enzyme(s)
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
        """
        Parse enzyme name or recognition site.
        
        Args:
            enzyme: Enzyme name (e.g., 'MboI') or site (e.g., '^GATC')
        
        Returns:
            Tuple of (recognition_site, enzyme_name)
        
        Examples:
            'MboI' -> ('^GATC', 'MboI')
            '^GATC' -> ('^GATC', '^GATC')
            'A^AGCTT' -> ('A^AGCTT', 'A^AGCTT')
        """
        # Check if it's a known enzyme name
        if enzyme in self.COMMON_ENZYMES:
            return self.COMMON_ENZYMES[enzyme], enzyme
        
        # Otherwise, treat as recognition site
        if '^' not in enzyme:
            raise ValueError(f"Recognition site must contain '^' to indicate cut position: {enzyme}")
        
        # Validate recognition site
        site_no_cut = enzyme.replace('^', '')
        if not all(c in 'ATCGN' for c in site_no_cut.upper()):
            raise ValueError(f"Recognition site contains invalid characters: {enzyme}")
        
        return enzyme.upper(), enzyme
    
    def _find_cut_position(self, recognition_site: str) -> int:
        """
        Find the cut position in recognition site.
        
        Args:
            recognition_site: Site with '^' indicating cut (e.g., '^GATC', 'A^AGCTT')
        
        Returns:
            Position of cut (0-indexed)
        
        Reference: Main.java findstartinres() (lines 72-80)
        """
        cut_pos = recognition_site.index('^')
        return cut_pos
    
    def _find_restriction_sites(self, sequence: str, recognition_sites: List[str]) -> List[Tuple[int, int]]:
        """
        Find all restriction sites in a sequence.
        
        Args:
            sequence: DNA sequence (uppercase)
            recognition_sites: List of recognition sites with '^' removed
        
        Returns:
            List of (position, enzyme_index) tuples sorted by position
        
        Reference: Main.java findsmIndex() (lines 94-118)
        """
        sites = []
        
        for enzyme_idx, site in enumerate(recognition_sites):
            # Handle degenerate bases (N = any base, R = A or G, etc.)
            # For simplicity, we'll use regex patterns
            pattern = site.replace('N', '[ATCG]')
            pattern = pattern.replace('R', '[AG]')
            pattern = pattern.replace('Y', '[CT]')
            pattern = pattern.replace('W', '[AT]')
            pattern = pattern.replace('S', '[GC]')
            pattern = pattern.replace('M', '[AC]')
            pattern = pattern.replace('K', '[GT]')
            
            # Find all matches
            for match in re.finditer(pattern, sequence):
                sites.append((match.start(), enzyme_idx))
        
        # Sort by position
        sites.sort(key=lambda x: x[0])
        
        return sites
    
    def generate_sites(self,
                      genome_fasta: str,
                      output_file: str) -> Dict:
        """
        Generate restriction fragment file from genome FASTA.
        
        Args:
            genome_fasta: Path to genome FASTA file
            output_file: Path to output BED file
        
        Returns:
            Statistics dictionary with fragment counts
        
        Reference: Main.java split_genome_byressite() (lines 121-230)
        """
        logger.info("=" * 70)
        logger.info("RESTRICTION SITE GENERATION")
        logger.info("=" * 70)
        logger.info(f"Input genome: {genome_fasta}")
        logger.info(f"Output file: {output_file}")
        
        # Prepare recognition sites (remove '^')
        cut_positions = [self._find_cut_position(site) for site in self.enzymes]
        recognition_sites = [site.replace('^', '') for site in self.enzymes]
        
        logger.info(f"Cut positions: {cut_positions}")
        logger.info(f"Recognition sites (no cut): {recognition_sites}")
        
        # Statistics
        stats = {
            'total_fragments': 0,
            'filtered_fragments': 0,
            'chromosomes': 0,
            'total_sites': 0,
            'fragments_by_chr': {}
        }
        
        # Open output file
        with open(output_file, 'w') as out_f:
            # Read genome FASTA
            current_chr = None
            chr_sequence = []
            
            logger.info("\nProcessing genome FASTA...")
            
            with open(genome_fasta, 'r') as fasta_f:
                for line in fasta_f:
                    line = line.strip()
                    
                    if line.startswith('>'):
                        # Process previous chromosome
                        if current_chr is not None and chr_sequence:
                            self._process_chromosome(
                                current_chr,
                                ''.join(chr_sequence),
                                recognition_sites,
                                cut_positions,
                                out_f,
                                stats
                            )
                        
                        # Start new chromosome
                        current_chr = line[1:].split()[0]  # Get first word after '>'
                        chr_sequence = []
                        stats['chromosomes'] += 1
                        
                    else:
                        # Append sequence
                        chr_sequence.append(line.upper())
                
                # Process last chromosome
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
        
        # Calculate actual cut positions (adjust for cut offset within recognition site)
        cut_coords = []
        for site_pos, enzyme_idx in sites:
            actual_cut = site_pos + cut_positions[enzyme_idx]
            cut_coords.append(actual_cut)
        
        # Add chromosome boundaries and sort
        cut_coords = [0] + sorted(set(cut_coords)) + [chr_len]
        
        # Generate fragments between consecutive cuts
        frag_count = 0
        for i in range(len(cut_coords) - 1):
            frag_start = cut_coords[i]
            frag_end = cut_coords[i + 1]
            frag_size = frag_end - frag_start
            
            # Apply size filters
            if self.min_frag_size <= frag_size <= self.max_frag_size:
                out_file.write(f"{chrom}\t{frag_start}\t{frag_end}\n")
                frag_count += 1
            else:
                stats['filtered_fragments'] += 1
            
            stats['total_fragments'] += 1
        
        # Update statistics
        stats['total_sites'] += len(sites)
        stats['fragments_by_chr'][chrom] = frag_count
        
        logger.info(f"  {chrom}: {len(sites):,} sites → {frag_count:,} fragments (length: {chr_len:,}bp)")


def main():
    """
    Example usage of RestrictionSiteGenerator.
    """
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
    
    # Create generator
    generator = RestrictionSiteGenerator(
        enzyme=args.enzyme,
        min_frag_size=args.min_size,
        max_frag_size=args.max_size
    )
    
    # Generate sites
    stats = generator.generate_sites(args.genome, args.output)
    
    print(f"\nGenerated {stats['total_fragments'] - stats['filtered_fragments']:,} restriction fragments")
    print(f"Output: {args.output}")


if __name__ == '__main__':
    main()
