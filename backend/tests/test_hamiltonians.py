import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from qiskit.quantum_info import SparsePauliOp
from pipeline.hamiltonians import load_hamiltonian, HamiltonianData

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hamiltonians")

def test_load_h2_returns_hamiltonian_data():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    assert isinstance(h, HamiltonianData)
    assert h.atom_id == "h2"
    assert isinstance(h.operator, SparsePauliOp)

def test_h2_has_correct_qubit_count():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    assert h.operator.num_qubits == 4

def test_h2_has_offdiagonal_terms():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    labels = [str(p) for p in h.operator.paulis]
    assert any("X" in lbl or "Y" in lbl for lbl in labels)

def test_h2_known_ground_state_loaded():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    assert h.known_ground_state_hartree == pytest.approx(-1.137306, abs=1e-4)

def test_lih_has_six_qubits():
    h = load_hamiltonian("lih", data_dir=DATA_DIR)
    assert h.operator.num_qubits == 6

def test_unknown_atom_raises():
    with pytest.raises(FileNotFoundError):
        load_hamiltonian("xyz_unknown", data_dir=DATA_DIR)
