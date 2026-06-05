import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from pipeline.hamiltonians import load_hamiltonian
from pipeline.vqe_runner import run_vqe, VQEResult

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hamiltonians")

def test_h2_ground_state_within_tolerance():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert isinstance(result, VQEResult)
    assert abs(result.ground_state_energy - (-1.1373)) < 0.05

def test_result_has_convergence_history():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert len(result.convergence_history) > 0
    assert result.convergence_history[-1] == pytest.approx(result.ground_state_energy, abs=1e-6)

def test_result_has_optimal_params():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert result.optimal_params is not None
    assert len(result.optimal_params) > 0

def test_result_has_one_rdm():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert result.one_rdm is not None
    n = h.num_qubits
    assert result.one_rdm.shape == (n, n)

def test_lih_ground_state_within_tolerance():
    h = load_hamiltonian("lih", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert abs(result.ground_state_energy - (-7.8631)) < 0.1

def test_convergence_history_is_monotonic():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    hist = result.convergence_history
    assert all(hist[i] >= hist[i + 1] - 1e-9 for i in range(len(hist) - 1))
    assert hist[-1] == pytest.approx(result.ground_state_energy, abs=1e-9)
