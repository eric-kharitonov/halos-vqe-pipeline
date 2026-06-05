from dataclasses import dataclass
import numpy as np
import scipy.optimize as opt

from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.primitives import StatevectorEstimator

from .hamiltonians import HamiltonianData


@dataclass
class VQEResult:
    atom_id: str
    ground_state_energy: float          # in Hartree (total energy; nuclear repulsion folded in)
    optimal_params: np.ndarray
    convergence_history: list[float]    # best-so-far energy at each iteration (monotonic)
    one_rdm: np.ndarray                 # 1-particle reduced density matrix, shape (n, n)
    num_qubits: int
    num_iterations: int
    converged: bool


def _build_ansatz(num_qubits: int, reps: int = 3):
    """
    EfficientSU2 hardware-efficient ansatz, decomposed to basis gates.
    The decompose() call is REQUIRED: high-level library circuits like
    EfficientSU2 are not directly executable by the estimator/statevector
    backends in Qiskit 2.x. Decomposition preserves the free parameters.
    """
    return EfficientSU2(num_qubits, reps=reps, entanglement="linear").decompose()


def _compute_one_rdm(ansatz, optimal_params: np.ndarray, num_qubits: int) -> np.ndarray:
    """
    1-particle reduced density matrix from the optimal wavefunction.
    Diagonal (orbital occupations <n_p> = (1 - <Z_p>)/2) is exact and is the only
    part the binding-site extractor uses. Off-diagonal uses the
    (<X_pX_q> + <Y_pY_q>)/4 approximation (illustrative only).
    """
    bound = ansatz.assign_parameters(optimal_params)
    sv = Statevector(bound)

    rdm = np.zeros((num_qubits, num_qubits), dtype=complex)
    for p in range(num_qubits):
        z_op = SparsePauliOp.from_sparse_list([("Z", [p], 1.0)], num_qubits=num_qubits)
        rdm[p, p] = (1.0 - sv.expectation_value(z_op).real) / 2.0

        for q in range(p + 1, num_qubits):
            xx_op = SparsePauliOp.from_sparse_list([("XX", [p, q], 1.0)], num_qubits=num_qubits)
            yy_op = SparsePauliOp.from_sparse_list([("YY", [p, q], 1.0)], num_qubits=num_qubits)
            val = (sv.expectation_value(xx_op) + sv.expectation_value(yy_op)) / 4.0
            rdm[p, q] = val
            rdm[q, p] = val.conjugate()

    return rdm.real


def run_vqe(
    ham_data: HamiltonianData,
    reps: int = 3,
    optimizer: str = "COBYLA",
    max_iter: int = 1500,
) -> VQEResult:
    """
    Run VQE using the exact StatevectorEstimator (no shot noise) + a scipy optimizer.
    Returns ground-state energy, a monotonic best-so-far convergence history, and the 1-RDM.
    Defaults (reps=3, max_iter=1500, COBYLA, seed 42) reach chemical accuracy on the
    shipped H2 (4q) and LiH (6q) Hamiltonians.
    """
    n = ham_data.num_qubits
    ansatz = _build_ansatz(n, reps=reps)
    estimator = StatevectorEstimator()

    raw_history: list[float] = []

    def cost_fn(params: np.ndarray) -> float:
        result = estimator.run([(ansatz, ham_data.operator, params)]).result()
        energy = float(result[0].data.evs)
        raw_history.append(energy)
        return energy

    rng = np.random.default_rng(seed=42)
    x0 = rng.uniform(-0.1, 0.1, ansatz.num_parameters)

    scipy_result = opt.minimize(
        cost_fn,
        x0,
        method=optimizer,
        options={"maxiter": max_iter, "rhobeg": 0.5},
    )

    best_history: list[float] = []
    running_min = float("inf")
    for e in raw_history:
        running_min = min(running_min, e)
        best_history.append(running_min)

    best_energy = best_history[-1]
    optimal_params = scipy_result.x
    one_rdm = _compute_one_rdm(ansatz, optimal_params, n)

    return VQEResult(
        atom_id=ham_data.atom_id,
        ground_state_energy=best_energy,
        optimal_params=optimal_params,
        convergence_history=best_history,
        one_rdm=one_rdm,
        num_qubits=n,
        num_iterations=len(best_history),
        converged=scipy_result.success,
    )
