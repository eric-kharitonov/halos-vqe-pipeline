import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest, json
from pipeline.handoff import build_handoff, HandoffPackage
from pipeline.binding_sites import CoordinationResult, CoordinationGeometry
from pipeline.protein_designer import ProteinDesignResult

def _make_protein_result(atom_id="h2"):
    return ProteinDesignResult(
        atom_id=atom_id,
        geometry=CoordinationGeometry.LINEAR,
        coordination_number=2,
        num_binding_residues=2,
        binding_residues=["D", "E"],
        binding_positions=[0, 4],
        sequence="DALKALAEALKALEE",
        fasta=f">HALOS_{atom_id.upper()}_binding_protein\nDALKALAEALKALEE",
        design_notes="Linear geometry.",
    )

def _make_coord_result(atom_id="h2"):
    return CoordinationResult(
        atom_id=atom_id,
        orbital_occupancies=[0.05, 0.95],
        empty_orbital_indices=[0],
        coordination_number=2,
        geometry=CoordinationGeometry.LINEAR,
        binding_strength_estimate=0.95,
    )

def test_build_handoff_returns_package():
    coord = _make_coord_result()
    protein = _make_protein_result()
    pkg = build_handoff(
        atom_id="h2",
        ground_state_energy=-1.1373,
        coordination=coord,
        protein=protein,
    )
    assert isinstance(pkg, HandoffPackage)

def test_handoff_json_is_valid():
    coord = _make_coord_result()
    protein = _make_protein_result()
    pkg = build_handoff("h2", -1.1373, coord, protein)
    serialized = pkg.to_json()
    parsed = json.loads(serialized)
    assert parsed["atom_id"] == "h2"
    assert "fasta" in parsed
    assert "coordination" in parsed
    assert "vqe" in parsed

def test_handoff_contains_fasta():
    coord = _make_coord_result()
    protein = _make_protein_result()
    pkg = build_handoff("h2", -1.1373, coord, protein)
    assert pkg.fasta.startswith(">")

def test_handoff_ranking_field_exists():
    coord = _make_coord_result()
    protein = _make_protein_result()
    pkg = build_handoff("h2", -1.1373, coord, protein)
    parsed = json.loads(pkg.to_json())
    assert "candidate_rank" in parsed
    assert "binding_confidence" in parsed
