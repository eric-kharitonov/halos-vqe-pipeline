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
