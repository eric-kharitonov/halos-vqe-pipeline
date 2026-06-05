import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pipeline.atoms import AtomConfig, get_atom, list_atoms, CoordinationClass

def test_get_h2():
    atom = get_atom("h2")
    assert atom.symbol == "H₂"
    assert atom.num_qubits == 4
    assert atom.known_ground_state_hartree == pytest.approx(-1.1373, abs=0.01)

def test_get_lih():
    atom = get_atom("lih")
    assert atom.symbol == "LiH"
    assert atom.num_qubits == 6

def test_list_atoms_includes_proxies():
    atoms = list_atoms()
    keys = [a.id for a in atoms]
    assert "h2" in keys
    assert "lih" in keys
    assert "ce3" in keys

def test_actinide_placeholder():
    atom = get_atom("u238")
    assert atom.is_placeholder is True
    assert atom.coordination_class == CoordinationClass.ACTINIDE

def test_unknown_atom_raises():
    with pytest.raises(KeyError):
        get_atom("xyz_unknown")
