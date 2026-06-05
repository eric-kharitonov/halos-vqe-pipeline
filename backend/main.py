import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pipeline.atoms import get_atom, list_atoms
from pipeline.hamiltonians import load_hamiltonian
from pipeline.vqe_runner import run_vqe
from pipeline.binding_sites import extract_binding_sites
from pipeline.protein_designer import design_protein
from pipeline.handoff import build_handoff

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "hamiltonians")

app = FastAPI(title="HALOS VQE Pipeline", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/atoms")
def get_atoms():
    atoms = list_atoms()
    return [
        {
            "id": a.id,
            "symbol": a.symbol,
            "name": a.name,
            "num_qubits": a.num_qubits,
            "coordination_class": a.coordination_class.value,
            "typical_coordination_number": a.typical_coordination_number,
            "donor_preference": a.donor_preference,
            "is_placeholder": a.is_placeholder,
            "notes": a.notes,
        }
        for a in atoms
    ]


@app.get("/atoms/{atom_id}")
def get_single_atom(atom_id: str):
    try:
        a = get_atom(atom_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown atom '{atom_id}'")
    return {
        "id": a.id,
        "symbol": a.symbol,
        "name": a.name,
        "num_qubits": a.num_qubits,
        "coordination_class": a.coordination_class.value,
        "typical_coordination_number": a.typical_coordination_number,
        "donor_preference": a.donor_preference,
        "known_ground_state_hartree": a.known_ground_state_hartree,
        "is_placeholder": a.is_placeholder,
        "notes": a.notes,
    }


@app.get("/pipeline/run/{atom_id}")
def run_full_pipeline(atom_id: str):
    """Run the complete VQE -> binding sites -> protein design pipeline."""
    try:
        atom = get_atom(atom_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown atom '{atom_id}'")

    if atom.is_placeholder:
        raise HTTPException(
            status_code=422,
            detail=f"'{atom_id}' is a placeholder — no Hamiltonian available yet. "
                   "Fault-tolerant quantum hardware required.",
        )

    try:
        ham_data = load_hamiltonian(atom_id, data_dir=DATA_DIR)
    except FileNotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e))

    vqe_result = run_vqe(ham_data)
    coord_result = extract_binding_sites(vqe_result.one_rdm, atom_id=atom_id)
    protein_result = design_protein(coord_result, donor_preference=atom.donor_preference)
    handoff = build_handoff(
        atom_id=atom_id,
        ground_state_energy=vqe_result.ground_state_energy,
        coordination=coord_result,
        protein=protein_result,
    )

    return {
        "atom_id": atom_id,
        "ground_state_energy": vqe_result.ground_state_energy,
        "known_ground_state": atom.known_ground_state_hartree,
        "convergence_history": vqe_result.convergence_history,
        "num_iterations": vqe_result.num_iterations,
        "orbital_occupancies": coord_result.orbital_occupancies,
        "empty_orbital_indices": coord_result.empty_orbital_indices,
        "coordination_number": coord_result.coordination_number,
        "geometry": coord_result.geometry.value,
        "binding_residues": protein_result.binding_residues,
        "binding_positions": protein_result.binding_positions,
        "sequence": protein_result.sequence,
        "fasta": protein_result.fasta,
        "binding_confidence": handoff.binding_confidence,
        "handoff_json": handoff.to_json(),
    }
