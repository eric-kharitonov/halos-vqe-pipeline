import json
import os
from dataclasses import dataclass
from qiskit.quantum_info import SparsePauliOp

_DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hamiltonians"
)

@dataclass
class HamiltonianData:
    atom_id: str
    operator: SparsePauliOp
    nuclear_repulsion_energy: float
    known_ground_state_hartree: float | None
    num_qubits: int
    description: str
    reference: str

def load_hamiltonian(atom_id: str, data_dir: str = _DEFAULT_DATA_DIR) -> HamiltonianData:
    """Load a pre-computed Hamiltonian from JSON. Raises FileNotFoundError if not found."""
    filename = f"{atom_id}_sto3g.json"
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No pre-computed Hamiltonian for '{atom_id}' at {path}. "
            "Generate it with `python backend/generate_hamiltonians.py` (requires pennylane)."
        )
    with open(path) as f:
        data = json.load(f)

    pauli_list = [
        (term["pauli"], complex(term["coeff"]))
        for term in data["pauli_terms"]
    ]
    operator = SparsePauliOp.from_list(pauli_list)

    return HamiltonianData(
        atom_id=atom_id,
        operator=operator,
        nuclear_repulsion_energy=data["nuclear_repulsion_energy"],
        known_ground_state_hartree=data.get("known_ground_state_hartree"),
        num_qubits=data["num_qubits"],
        description=data["description"],
        reference=data["reference"],
    )
