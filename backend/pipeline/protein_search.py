"""
QAOA-based protein sequence search (QPD Build 2, quantum component).

Where the protein *designer* (protein_designer.py) deterministically places residues,
this module *searches* a space of short peptides for the lowest-cost binder using the
Quantum Approximate Optimization Algorithm (QAOA) on Qiskit.

How QAOA is used here
---------------------
1. Encode each candidate peptide as a bitstring. Residues come from a 4-letter O-donor
   alphabet, so each position is 2 qubits (BITS_PER_RESIDUE). An n-residue peptide is a
   2n-qubit problem with len(ALPHABET)**n candidates.
2. Build a DIAGONAL cost Hamiltonian H_C whose eigenvalue on a basis state |z> equals the
   binding cost of the peptide that z encodes. The optimal peptide is therefore the ground
   state of H_C. The cost rewards strong donors at an electron-deficient site and penalises
   adjacent identical residues (the interaction term that makes the problem non-trivial).
3. Build the QAOA circuit (QAOAAnsatz): p alternating layers of exp(-i*gamma*H_C) (phase
   separation) and exp(-i*beta*H_mixer) (mixing). A classical optimizer (COBYLA) tunes the
   2p angles to minimise <H_C>.
4. Sample the optimised state; the most probable bitstring decodes to the recommended
   sequence. Because the space is tiny we also brute-force the true optimum and report
   whether QAOA reached it (honest validation, not a black box).

The `binding_strength` input is the electron deficiency at the empty orbital(s), taken
from the VQE 1-RDM via binding_sites.py — so this genuinely searches "against the binding
map" the VQE produced.
"""
from dataclasses import dataclass
import numpy as np
import scipy.optimize as opt

from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.primitives import StatevectorEstimator

# O-donor residue alphabet, 2-bit binary encoded (00->D, 01->E, 10->S, 11->T)
ALPHABET = ["D", "E", "S", "T"]
# Relative O-donor strength: carboxylates (D, E) bind hard cations better than hydroxyls (S, T)
DONOR_STRENGTH = {"D": 1.0, "E": 0.95, "S": 0.60, "T": 0.55}
# Penalty for two adjacent identical residues (electrostatic repulsion / favour diversity)
ADJACENT_IDENTICAL_PENALTY = 0.3
BITS_PER_RESIDUE = 2
MAX_RESIDUES = 3  # keep the demo to <= 6 qubits


def _decode(index: int, n_residues: int) -> str:
    """Decode an integer basis-state index into a residue sequence.

    Qubit q holds bit q (Qiskit little-endian). Residue r uses qubits [2r, 2r+1].
    """
    seq = []
    for r in range(n_residues):
        value = ((index >> (BITS_PER_RESIDUE * r)) & 1) + 2 * ((index >> (BITS_PER_RESIDUE * r + 1)) & 1)
        seq.append(ALPHABET[value])
    return "".join(seq)


def sequence_cost(sequence: str, binding_strength: float) -> float:
    """Binding cost of a peptide (lower = better).

    Reward term: strong donors at a high-deficiency site -> more negative.
    Penalty term: adjacent identical residues add ADJACENT_IDENTICAL_PENALTY.
    """
    cost = sum(-binding_strength * DONOR_STRENGTH[a] for a in sequence)
    cost += sum(
        ADJACENT_IDENTICAL_PENALTY
        for i in range(len(sequence) - 1)
        if sequence[i] == sequence[i + 1]
    )
    return cost


def _build_cost_hamiltonian(n_residues: int, binding_strength: float):
    """Build the diagonal cost Hamiltonian H_C as a SparsePauliOp.

    Returns (operator, diag) where diag[z] = sequence_cost(decode(z)). The Pauli-Z
    decomposition of a diagonal operator is its Walsh-Hadamard transform (exact).
    """
    n = BITS_PER_RESIDUE * n_residues
    dim = 2 ** n
    diag = np.array([sequence_cost(_decode(z, n_residues), binding_strength) for z in range(dim)])

    labels, coeffs = [], []
    for subset in range(dim):
        # Walsh-Hadamard coefficient for the Z-string selected by `subset`
        signs = np.array([-1 if bin(subset & z).count("1") & 1 else 1 for z in range(dim)])
        w = float(np.dot(diag, signs)) / dim
        if abs(w) > 1e-9:
            # qubit 0 must be the rightmost character in a Qiskit Pauli label
            label = "".join("Z" if (subset >> q) & 1 else "I" for q in range(n))[::-1]
            labels.append(label)
            coeffs.append(w)
    return SparsePauliOp(labels, coeffs), diag


def _brute_force_optimum(diag: np.ndarray, n_residues: int):
    """Exact optimum over the whole (tiny) space: (sequence, cost)."""
    idx = int(np.argmin(diag))
    return _decode(idx, n_residues), float(diag[idx])


@dataclass
class QAOACandidate:
    sequence: str
    cost: float
    probability: float


@dataclass
class QAOASearchResult:
    n_residues: int
    n_qubits: int
    reps: int
    search_space_size: int
    ranked_candidates: list[QAOACandidate]   # top candidates by measurement probability
    best_sequence: str
    best_cost: float
    brute_force_optimum: str
    brute_force_cost: float
    found_optimum: bool                      # did QAOA reach the true minimum cost?
    convergence_history: list[float]         # best-so-far <H_C> per iteration (monotonic)
    alphabet: list[str]


def run_qaoa_search(
    binding_strength: float,
    n_residues: int = 2,
    reps: int = 3,
    maxiter: int = 300,
    seed: int = 7,
    top_k: int = 5,
) -> QAOASearchResult:
    """Search peptide space with QAOA for the lowest-cost binder against a binding site.

    binding_strength: electron deficiency at the empty orbital(s) (0-1), from the VQE 1-RDM.
    n_residues: peptide length (clamped to MAX_RESIDUES to stay <= 6 qubits).
    """
    n_residues = max(1, min(n_residues, MAX_RESIDUES))
    n_qubits = BITS_PER_RESIDUE * n_residues

    cost_op, diag = _build_cost_hamiltonian(n_residues, binding_strength)
    ansatz = QAOAAnsatz(cost_operator=cost_op, reps=reps).decompose()
    estimator = StatevectorEstimator()

    raw_history: list[float] = []

    def objective(params: np.ndarray) -> float:
        energy = float(estimator.run([(ansatz, cost_op, params)]).result()[0].data.evs)
        raw_history.append(energy)
        return energy

    rng = np.random.default_rng(seed)
    x0 = rng.uniform(0.0, np.pi, ansatz.num_parameters)
    scipy_result = opt.minimize(objective, x0, method="COBYLA", options={"maxiter": maxiter})

    # Monotonic best-so-far history for a clean convergence chart.
    best_history, running_min = [], float("inf")
    for e in raw_history:
        running_min = min(running_min, e)
        best_history.append(running_min)

    # Sample the optimised state; rank candidates by measurement probability.
    final_state = Statevector(ansatz.assign_parameters(scipy_result.x))
    probs = final_state.probabilities()
    order = np.argsort(probs)[::-1][:top_k]
    ranked = [
        QAOACandidate(
            sequence=_decode(int(idx), n_residues),
            cost=float(diag[int(idx)]),
            probability=float(probs[int(idx)]),
        )
        for idx in order
    ]

    best = ranked[0]
    bf_seq, bf_cost = _brute_force_optimum(diag, n_residues)
    found = abs(best.cost - bf_cost) < 1e-6

    return QAOASearchResult(
        n_residues=n_residues,
        n_qubits=n_qubits,
        reps=reps,
        search_space_size=len(ALPHABET) ** n_residues,
        ranked_candidates=ranked,
        best_sequence=best.sequence,
        best_cost=best.cost,
        brute_force_optimum=bf_seq,
        brute_force_cost=bf_cost,
        found_optimum=found,
        convergence_history=best_history,
        alphabet=list(ALPHABET),
    )
