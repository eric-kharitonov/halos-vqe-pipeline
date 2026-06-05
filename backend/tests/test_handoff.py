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
    assert "binding_map" in parsed
    assert parsed["map_source"] == "vqe"

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
    # The electron-deficiency measure lives in binding_map, honestly named (not "confidence").
    assert "mean_electron_deficiency" in parsed["binding_map"]

def test_vqe_handoff_carries_energy():
    coord = _make_coord_result()  # default source="vqe"
    protein = _make_protein_result()
    parsed = json.loads(build_handoff("h2", -1.1373, coord, protein).to_json())
    assert parsed["map_source"] == "vqe"
    assert parsed["binding_map"]["vqe_ground_state_energy_hartree"] == -1.1373
    assert parsed["binding_map"]["source"] == "vqe"

def test_proxy_handoff_marks_literature_and_no_energy():
    # A proxy (Cs⁺/Sr²⁺) handoff must NOT claim a VQE energy — it ran no VQE.
    coord = CoordinationResult(
        atom_id="cs",
        orbital_occupancies=[0.05] * 8 + [0.95] * 2,
        empty_orbital_indices=list(range(8)),
        coordination_number=8,
        geometry=CoordinationGeometry.SQUARE_ANTIPRISMATIC,
        binding_strength_estimate=0.9,
        source="literature",
    )
    protein = _make_protein_result(atom_id="cs")
    parsed = json.loads(build_handoff("cs", None, coord, protein).to_json())
    assert parsed["map_source"] == "literature"
    assert parsed["binding_map"]["vqe_ground_state_energy_hartree"] is None
    assert "NO VQE" in parsed["binding_map"]["method"]

def test_handoff_next_step_is_not_stale():
    coord = _make_coord_result()
    protein = _make_protein_result()
    next_step = json.loads(build_handoff("h2", -1.1373, coord, protein).to_json())["next_step"]
    assert "ESMFold" in next_step          # the tool actually wired into the pipeline
    assert "DR_0906" not in next_step       # the old hard-coded locus is gone
