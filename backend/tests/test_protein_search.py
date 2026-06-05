import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
import numpy as np
from qiskit.quantum_info import SparsePauliOp

from pipeline.protein_search import (
    ALPHABET,
    sequence_cost,
    run_qaoa_search,
    QAOASearchResult,
    _build_cost_hamiltonian,
    _decode,
)


def test_decode_roundtrip():
    # 2 residues, 4 qubits. index 0 -> first alphabet letter for both positions.
    assert _decode(0, 2) == ALPHABET[0] + ALPHABET[0]


def test_sequence_cost_rewards_strong_donors():
    # D/E are stronger O-donors than S/T, so a DE peptide must score lower (better).
    assert sequence_cost("DE", binding_strength=0.99) < sequence_cost("ST", binding_strength=0.99)


def test_adjacent_identical_penalty_breaks_ties():
    # Two adjacent identical residues incur a penalty, so DE beats DD even though
    # D is the single strongest donor.
    assert sequence_cost("DE", 0.99) < sequence_cost("DD", 0.99)


def test_cost_hamiltonian_is_diagonal_and_matches_cost_function():
    n_res = 2
    binding = 0.99
    op, diag = _build_cost_hamiltonian(n_res, binding)
    assert isinstance(op, SparsePauliOp)
    # Operator must be diagonal: its matrix diagonal equals the cost vector.
    mat = op.to_matrix()
    assert np.allclose(mat, np.diag(np.diag(mat)))           # off-diagonal is zero
    assert np.allclose(np.diag(mat).real, diag)              # diagonal == cost vector
    # And each diagonal entry equals the cost of the decoded sequence.
    for idx in range(2 ** (2 * n_res)):
        assert diag[idx] == pytest.approx(sequence_cost(_decode(idx, n_res), binding))


def test_search_space_size():
    result = run_qaoa_search(binding_strength=0.99, n_residues=2)
    assert result.search_space_size == len(ALPHABET) ** 2


def test_qaoa_finds_brute_force_optimum_2mer():
    # The honest validation: on a 16-candidate space, QAOA's best sequence must
    # reach the true (brute-force) minimum cost. Degeneracy-robust: compare cost.
    result = run_qaoa_search(binding_strength=0.99, n_residues=2)
    assert isinstance(result, QAOASearchResult)
    assert result.found_optimum is True
    assert result.best_cost == pytest.approx(result.brute_force_cost, abs=1e-6)
    assert len(result.ranked_candidates) > 0
    assert len(result.convergence_history) > 0
