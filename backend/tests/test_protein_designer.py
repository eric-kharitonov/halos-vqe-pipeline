import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from pipeline.binding_sites import CoordinationResult, CoordinationGeometry
from pipeline.protein_designer import design_protein, ProteinDesignResult, scaffold_binding_residues


def test_scaffold_binding_residues_contains_residues():
    seq = scaffold_binding_residues(["D", "E"])
    assert seq[0] == "D"      # first binding residue at helix position 0
    assert "E" in seq
    assert len(seq) >= 8      # scaffolded to a full helix turn past the last residue


def _coord_result(coord_number: int, geometry: CoordinationGeometry, donors: list[str], atom_id: str = "test"):
    return CoordinationResult(
        atom_id=atom_id,
        orbital_occupancies=[0.05] * coord_number + [0.95] * (6 - coord_number),
        empty_orbital_indices=list(range(coord_number)),
        coordination_number=coord_number,
        geometry=geometry,
        binding_strength_estimate=0.9,
    )

def test_design_returns_protein_result():
    coord = _coord_result(2, CoordinationGeometry.LINEAR, ["O"])
    result = design_protein(coord, donor_preference=["O"])
    assert isinstance(result, ProteinDesignResult)

def test_binding_residues_count_matches_coord_number():
    for cn in [2, 4, 6]:
        coord = _coord_result(cn, CoordinationGeometry.OCTAHEDRAL, ["O"])
        result = design_protein(coord, donor_preference=["O"])
        assert result.num_binding_residues == cn

def test_fasta_sequence_contains_binding_residues():
    coord = _coord_result(4, CoordinationGeometry.TETRAHEDRAL, ["O"])
    result = design_protein(coord, donor_preference=["O"])
    o_donors = set("DESTYN")
    binding_residues_in_seq = [aa for aa in result.sequence if aa in o_donors]
    assert len(binding_residues_in_seq) >= 4

def test_fasta_output_format():
    coord = _coord_result(4, CoordinationGeometry.TETRAHEDRAL, ["O"])
    result = design_protein(coord, donor_preference=["O"])
    assert result.fasta.startswith(">")
    lines = result.fasta.strip().split("\n")
    assert len(lines) == 2
    assert all(c.isalpha() for c in lines[1])

def test_h2_linear_uses_two_residues():
    coord = _coord_result(2, CoordinationGeometry.LINEAR, ["O", "N"], atom_id="h2")
    result = design_protein(coord, donor_preference=["O", "N"])
    assert result.num_binding_residues == 2

def test_vqe_fasta_is_stamped_quantum():
    coord = _coord_result(2, CoordinationGeometry.LINEAR, ["O"])  # default source="vqe"
    result = design_protein(coord, donor_preference=["O"])
    assert "generated=quantum-vqe-pipeline" in result.fasta

def test_proxy_fasta_is_not_stamped_quantum():
    # A literature-sourced proxy must NOT claim it came from VQE.
    coord = CoordinationResult(
        atom_id="cs",
        orbital_occupancies=[0.05] * 8 + [0.95] * 2,
        empty_orbital_indices=list(range(8)),
        coordination_number=8,
        geometry=CoordinationGeometry.SQUARE_ANTIPRISMATIC,
        binding_strength_estimate=0.9,
        source="literature",
    )
    result = design_protein(coord, donor_preference=["O"])
    assert "generated=literature-coordination" in result.fasta
    assert "quantum-vqe" not in result.fasta
