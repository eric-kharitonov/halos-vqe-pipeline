"""
Prime-editing design simulation (molecular level — the part that IS computable).

Given the designed protein, this:
  1. codon-optimizes it into a DNA coding sequence for D. radiodurans (a GC-rich,
     ~67% GC genome), using preferred high-GC codons;
  2. designs a (simplified) prime-editing guide RNA (pegRNA) against a representative
     insertion locus — spacer + PAM + primer-binding site (PBS) + RT template (RTT);
  3. produces the before -> after genomic sequence with the gene written in.

HONEST SCOPE: this simulates the *design of the edit* (real bioinformatics — BPD Day 3).
It does NOT predict whether the edited cell survives, expresses the protein, or functions.
That is emergent biology and stays wet-lab. The pegRNA design is simplified (PrimeDesign
does the rigorous version); the locus is representative, not a pull from the live genome.
"""
from dataclasses import dataclass

# Preferred codons for D. radiodurans (high-GC; GC-rich wobble positions).
PREFERRED_CODON = {
    "A": "GCC", "R": "CGC", "N": "AAC", "D": "GAC", "C": "TGC", "Q": "CAG",
    "E": "GAG", "G": "GGC", "H": "CAC", "I": "ATC", "L": "CTG", "K": "AAG",
    "M": "ATG", "F": "TTC", "P": "CCG", "S": "TCC", "T": "ACC", "W": "TGG",
    "Y": "TAC", "V": "GTC", "*": "TGA",
}

# Representative neutral insertion locus (intergenic), with an NGG PAM. Not the live
# genome — a fixed context so the edit is reproducible and inspectable.
LOCUS_NAME = "DR intergenic (representative neutral site)"
LOCUS_CONTEXT = (
    "GACCTGCGGTATCGCAGTTGCACCAGTCCGGTGAACTCGCAGGTCTGACCGTAGCATCGGT"
)
PAM = "CGG"  # the NGG PAM present in LOCUS_CONTEXT

VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")

_COMPLEMENT = str.maketrans("ACGT", "TGCA")


def reverse_complement(dna: str) -> str:
    return dna.translate(_COMPLEMENT)[::-1]


def codon_optimize(protein: str) -> str:
    """Amino-acid sequence -> DNA coding sequence using preferred D. radiodurans codons."""
    seq = "".join(PREFERRED_CODON.get(aa, "NNN") for aa in protein.upper())
    return "ATG" + seq + PREFERRED_CODON["*"]   # start codon + stop


def gc_content(dna: str) -> float:
    if not dna:
        return 0.0
    gc = sum(1 for b in dna if b in "GC")
    return round(100.0 * gc / len(dna), 1)


@dataclass
class PrimeEditPlan:
    locus_name: str
    protein: str
    gene_dna: str
    gene_length_bp: int
    gc_content: float
    spacer: str            # 20-nt protospacer (Cas9 nickase target)
    pam: str
    pbs: str               # primer binding site (~13 nt)
    rtt: str               # reverse-transcriptase template (encodes the insert)
    before: str            # locus before the edit
    after: str             # locus after the gene is written in
    insert_index: int


def design_prime_edit(protein: str) -> PrimeEditPlan:
    # Validate the protein so a bad input fails loudly instead of silently producing
    # NNN codons (unknown residues) that would read as a successful design.
    seq = "".join(protein.split()).upper()
    if not seq:
        raise ValueError("Empty protein sequence.")
    invalid = sorted(set(seq) - VALID_AA)
    if invalid:
        raise ValueError(f"Protein has non-standard residues: {invalid}")

    gene = codon_optimize(seq)

    # Locate the PAM, derive the protospacer (20 nt immediately 5' of the PAM).
    pam_idx = LOCUS_CONTEXT.find(PAM, 20)
    if pam_idx < 0:
        pam_idx = 23  # fallback so the demo always produces a plan
    spacer = LOCUS_CONTEXT[pam_idx - 20:pam_idx]

    # SpCas9 nickase cuts ~3 nt 5' of the PAM on the protospacer strand.
    nick = pam_idx - 3
    # PBS: reverse-complement of ~13 nt ending at the nick (primes reverse transcription).
    pbs = reverse_complement(LOCUS_CONTEXT[nick - 13:nick])
    # RTT: templates the new strand = insert + short downstream homology (rev-comp).
    downstream_homology = LOCUS_CONTEXT[nick:nick + 10]
    rtt = reverse_complement(gene + downstream_homology)

    before = LOCUS_CONTEXT
    after = LOCUS_CONTEXT[:nick] + gene + LOCUS_CONTEXT[nick:]

    return PrimeEditPlan(
        locus_name=LOCUS_NAME,
        protein=seq,
        gene_dna=gene,
        gene_length_bp=len(gene),
        gc_content=gc_content(gene),
        spacer=spacer,
        pam=PAM,
        pbs=pbs,
        rtt=rtt,
        before=before,
        after=after,
        insert_index=nick,
    )
