import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from pipeline.prime_editing import (
    codon_optimize,
    reverse_complement,
    gc_content,
    design_prime_edit,
)


def test_reverse_complement():
    assert reverse_complement("ATGC") == "GCAT"


def test_codon_optimize_starts_and_stops():
    dna = codon_optimize("DE")
    assert dna.startswith("ATG")          # start codon
    assert dna.endswith("TGA")            # stop codon
    assert "GAC" in dna and "GAG" in dna  # D and E preferred codons
    assert len(dna) == 3 * (2 + 2)        # ATG + 2 residues + stop


def test_gc_content_is_high_for_dr():
    # D. radiodurans preferred codons are GC-rich -> coding sequence should be > 55% GC.
    dna = codon_optimize("ALKALAEADE")
    assert gc_content(dna) > 55


def test_design_prime_edit_inserts_gene():
    plan = design_prime_edit("DE")
    assert len(plan.spacer) == 20
    assert plan.pam == "CGG"
    assert plan.gene_dna in plan.after          # the gene is written into the locus
    assert plan.gene_dna not in plan.before     # but not present before the edit
    assert len(plan.after) == len(plan.before) + plan.gene_length_bp
    assert len(plan.pbs) == 13


def test_design_prime_edit_rejects_nonstandard_residues():
    # Unknown residues must fail loudly, not silently emit NNN codons.
    with pytest.raises(ValueError):
        design_prime_edit("DEZ1")


def test_design_prime_edit_rejects_empty():
    with pytest.raises(ValueError):
        design_prime_edit("   ")
