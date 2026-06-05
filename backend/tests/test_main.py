import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200

def test_list_atoms():
    r = client.get("/atoms")
    assert r.status_code == 200
    atoms = r.json()
    assert isinstance(atoms, list)
    ids = [a["id"] for a in atoms]
    assert "h2" in ids
    assert "u238" in ids

def test_get_single_atom():
    r = client.get("/atoms/h2")
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "H₂"

def test_get_unknown_atom_returns_404():
    r = client.get("/atoms/xyz_unknown")
    assert r.status_code == 404

def test_full_pipeline_h2():
    r = client.get("/pipeline/run/h2", timeout=120)
    assert r.status_code == 200
    data = r.json()
    assert "ground_state_energy" in data
    assert abs(data["ground_state_energy"] - (-1.1373)) < 0.05
    assert "fasta" in data
    assert data["fasta"].startswith(">")


def test_qaoa_search_endpoint():
    r = client.get("/pipeline/qaoa-search", params={"binding_strength": 0.99, "n_residues": 2}, timeout=120)
    assert r.status_code == 200
    data = r.json()
    assert data["search_space_size"] == 16
    assert data["found_optimum"] is True
    assert data["best_cost"] == pytest.approx(data["brute_force_cost"], abs=1e-6)
    assert len(data["ranked_candidates"]) > 0


def test_qaoa_search_returns_handoff_block():
    r = client.get(
        "/pipeline/qaoa-search",
        params={"binding_strength": 0.99, "n_residues": 2, "atom_id": "h2", "geometry": "linear"},
        timeout=120,
    )
    assert r.status_code == 200
    block = r.json()["handoff_block"]
    assert block["recommended_fasta"].startswith(">")
    assert block["reached_global_optimum"] is True
    # The scaffolded sequence must contain QAOA's chosen core residues.
    for residue in block["recommended_core_residues"]:
        assert residue in block["recommended_sequence"]
    assert len(block["ranked_alternatives"]) > 0
