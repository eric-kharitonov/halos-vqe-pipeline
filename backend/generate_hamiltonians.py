"""
Generate verified molecular Hamiltonians as JSON for the HALOS VQE pipeline.

WHY THIS EXISTS:
PySCF (the usual quantum-chemistry integral engine) has no Windows wheel, so we
cannot compute molecular integrals with the standard Qiskit-Nature path here.
Instead we use PennyLane's pure-Python differentiable Hartree-Fock backend
(method="dhf") to compute the integrals and build the qubit Hamiltonian ONCE,
offline. We convert that Hamiltonian to a plain list of (Pauli-string, coeff)
terms and write it to JSON.

The runtime VQE pipeline (backend/pipeline/) is pure Qiskit — it only ever reads
these JSON files. PennyLane is a build-time data-generation dependency, not a
runtime one.

Each Hamiltonian's nuclear repulsion energy is already folded into the identity
term by PennyLane, so the operator's lowest eigenvalue IS the total ground-state
energy. We exact-diagonalize here and store that value as `known_ground_state_hartree`
so the VQE tests are self-consistent with the shipped operator.

Run:  python backend/generate_hamiltonians.py
"""
import json
import os
import numpy as np
import pennylane as qml
from pennylane import qchem

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "hamiltonians")

# Bohr per Angstrom
ANG_TO_BOHR = 1.8897259886


def pennylane_to_pauli_terms(H, num_qubits: int) -> list[dict]:
    """
    Convert a PennyLane Hamiltonian to a list of {"pauli": str, "coeff": float}.

    Uses the operator's PauliSentence representation. The Qiskit label convention
    places qubit 0 at the RIGHTMOST character, so position = num_qubits - 1 - wire.
    Qubit relabeling does not change the spectrum, but we follow Qiskit's
    convention so the operator is ordered correctly.
    """
    ps = H.pauli_rep  # PauliSentence: {PauliWord: coeff}
    terms = []
    for pauli_word, coeff in ps.items():
        label = ["I"] * num_qubits
        for wire, pauli_char in pauli_word.items():
            label[num_qubits - 1 - wire] = pauli_char
        terms.append({"pauli": "".join(label), "coeff": float(np.real(coeff))})
    return terms


def exact_ground_state(terms: list[dict], num_qubits: int) -> float:
    """Exact lowest eigenvalue of the operator built from terms (sanity check)."""
    from qiskit.quantum_info import SparsePauliOp
    op = SparsePauliOp.from_list([(t["pauli"], t["coeff"]) for t in terms])
    return float(np.linalg.eigvalsh(op.to_matrix()).min())


def build(atom_id, symbols, coords_ang, description, reference,
          active_electrons=None, active_orbitals=None):
    coords = np.array(coords_ang) * ANG_TO_BOHR
    kwargs = dict(method="dhf", basis="sto-3g")
    if active_electrons is not None:
        kwargs["active_electrons"] = active_electrons
        kwargs["active_orbitals"] = active_orbitals
    H, num_qubits = qchem.molecular_hamiltonian(symbols, coords, **kwargs)

    terms = pennylane_to_pauli_terms(H, num_qubits)
    gs = exact_ground_state(terms, num_qubits)

    data = {
        "atom_id": atom_id,
        "description": description,
        "reference": reference,
        "num_qubits": num_qubits,
        # Nuclear repulsion is folded into the identity term by the dhf backend;
        # the operator's ground state is already the TOTAL energy.
        "nuclear_repulsion_energy": 0.0,
        "pauli_terms": terms,
        "known_ground_state_hartree": round(gs, 6),
        "generator": "pennylane.qchem dhf (pure-Python HF), STO-3G",
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{atom_id}_sto3g.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  {atom_id}: {num_qubits} qubits, {len(terms)} terms, "
          f"ground state {gs:.6f} Ha -> {os.path.relpath(path)}")


def build_toy(atom_id, terms, description, reference):
    """Write a hand-specified toy Hamiltonian (no quantum chemistry backend).

    Used for illustrative targets like tritium where a rigorous open-shell
    calculation isn't the point. The ground state is exact-diagonalized so the
    VQE test stays self-consistent.
    """
    num_qubits = len(terms[0]["pauli"])
    gs = exact_ground_state(terms, num_qubits)
    data = {
        "atom_id": atom_id,
        "description": description,
        "reference": reference,
        "num_qubits": num_qubits,
        "nuclear_repulsion_energy": 0.0,
        "pauli_terms": terms,
        "known_ground_state_hartree": round(gs, 6),
        "generator": "hand-specified toy Hamiltonian",
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{atom_id}_sto3g.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  {atom_id}: {num_qubits} qubits (toy), ground state {gs:.6f} Ha -> {os.path.relpath(path)}")


def main():
    print("Generating verified Hamiltonians (PennyLane dhf -> Qiskit JSON)...")
    # H2 at 0.735 Angstrom — canonical VQE reference, full 4-qubit STO-3G
    build(
        atom_id="h2",
        symbols=["H", "H"],
        coords_ang=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.735]],
        description="H2 at R=0.735 Angstrom, STO-3G, full 4-qubit Jordan-Wigner. "
                    "Nuclear repulsion folded into identity term.",
        reference="O'Malley et al. (2016), Physical Review X 6, 031007 (reference energy)",
    )
    # LiH at 1.595 Angstrom — active space (2e, 3 orbitals) -> 6 qubits, VQE-tractable
    build(
        atom_id="lih",
        symbols=["Li", "H"],
        coords_ang=[[0.0, 0.0, 0.0], [0.0, 0.0, 1.595]],
        description="LiH at R=1.595 Angstrom, STO-3G, active space (2 electrons, "
                    "3 spatial orbitals) -> 6 qubits. Nuclear repulsion folded into "
                    "identity term. Ground state is the active-space exact value.",
        reference="Kandala et al. (2017), Nature 549, 242 (system reference)",
        active_electrons=2,
        active_orbitals=3,
    )
    # Tritium — toy single-orbital hydrogenic system (2 qubits). Tritium is
    # electronically hydrogen; this is illustrative, with a small XX coupling so
    # VQE has a non-trivial gradient to follow.
    build_toy(
        atom_id="t",
        terms=[
            {"pauli": "II", "coeff": -0.20},
            {"pauli": "IZ", "coeff": -0.15},
            {"pauli": "ZI", "coeff": -0.15},
            {"pauli": "ZZ", "coeff": 0.05},
            {"pauli": "XX", "coeff": -0.10},
        ],
        description="Toy hydrogenic single-orbital system for tritium (³H). 2 qubits. "
                    "Illustrative only — not a rigorous open-shell calculation.",
        reference="Toy (tritium is electronically hydrogen)",
    )
    print("Done.")


if __name__ == "__main__":
    main()
