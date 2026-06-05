import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pipeline.atoms import AtomConfig, get_atom, list_atoms, CoordinationClass, Tier


def test_get_h2():
    atom = get_atom("h2")
    assert atom.symbol == "H₂"
    assert atom.num_qubits == 4
    assert atom.tier == Tier.REAL_VQE
    assert atom.runs_vqe is True
    assert atom.known_ground_state_hartree == pytest.approx(-1.1373, abs=0.01)


def test_get_lih():
    atom = get_atom("lih")
    assert atom.symbol == "LiH"
    assert atom.num_qubits == 6
    assert atom.tier == Tier.PRECOMPUTED


def test_tritium_is_toy():
    atom = get_atom("t")
    assert atom.tier == Tier.TOY
    assert atom.runs_vqe is True
    assert atom.num_qubits == 2


def test_list_atoms_includes_proxies_and_locked():
    keys = [a.id for a in list_atoms()]
    assert "h2" in keys
    assert "cs" in keys   # downstream-only proxy
    assert "sr" in keys
    assert "u" in keys    # locked actinide


def test_proxy_is_downstream_only():
    cs = get_atom("cs")
    assert cs.tier == Tier.PROXY
    assert cs.is_downstream_only is True
    assert cs.runs_vqe is False
    assert cs.qubits_are_estimate is True


def test_actinide_is_locked():
    u = get_atom("u")
    assert u.tier == Tier.LOCKED
    assert u.is_locked is True
    assert u.runs_vqe is False
    assert u.coordination_class == CoordinationClass.ACTINIDE


def test_badge_text():
    assert get_atom("h2").badge == "REAL VQE"
    assert get_atom("cs").badge == "PROXY"
    assert get_atom("u").badge == "LOCKED"


def test_unknown_atom_raises():
    with pytest.raises(KeyError):
        get_atom("xyz_unknown")
