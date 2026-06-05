import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pipeline.atoms import get_atom, list_atoms, AtomConfig
from pipeline.hamiltonians import load_hamiltonian
from pipeline.vqe_runner import run_vqe
from pipeline.binding_sites import extract_binding_sites, estimate_coordination_from_literature
from pipeline.protein_designer import (
    design_protein,
    scaffold_binding_residues,
    build_foldable_construct,
)
from pipeline.protein_search import run_qaoa_search
from pipeline.handoff import build_handoff
from pipeline.folding import fold_sequence, FoldingError, InvalidSequenceError
from pipeline.prime_editing import design_prime_edit

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "hamiltonians")

app = FastAPI(title="HALOS VQE Pipeline", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize_atom(a: AtomConfig) -> dict:
    return {
        "id": a.id,
        "symbol": a.symbol,
        "name": a.name,
        "tier": a.tier.value,
        "badge": a.badge,
        "num_qubits": a.num_qubits,
        "qubits_are_estimate": a.qubits_are_estimate,
        "electrons": a.electrons,
        "coordination_class": a.coordination_class.value,
        "typical_coordination_number": a.typical_coordination_number,
        "donor_preference": a.donor_preference,
        "known_ground_state_hartree": a.known_ground_state_hartree,
        "runs_vqe": a.runs_vqe,
        "is_downstream_only": a.is_downstream_only,
        "is_locked": a.is_locked,
        "notes": a.notes,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/atoms")
def get_atoms():
    return [_serialize_atom(a) for a in list_atoms()]


@app.get("/atoms/{atom_id}")
def get_single_atom(atom_id: str):
    try:
        a = get_atom(atom_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown atom '{atom_id}'")
    return _serialize_atom(a)


@app.get("/pipeline/run/{atom_id}")
def run_full_pipeline(atom_id: str):
    """Run the pipeline as far as the target's tier allows.

    - runs_vqe targets (H₂, LiH, T): real/toy VQE -> binding map -> design.
    - downstream-only proxies (Cs⁺, Sr²⁺): SKIP VQE, estimate the binding map from
      literature coordination chemistry, then design (clearly marked source=literature).
    - locked targets (actinides): 422 — needs fault-tolerant hardware.
    """
    try:
        atom = get_atom(atom_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown atom '{atom_id}'")

    if atom.is_locked:
        raise HTTPException(
            status_code=422,
            detail=f"'{atom.symbol}' is locked — its electronic structure is beyond "
                   "classical or current quantum simulation. Needs fault-tolerant hardware.",
        )

    if atom.runs_vqe:
        try:
            ham_data = load_hamiltonian(atom_id, data_dir=DATA_DIR)
        except FileNotFoundError as e:
            raise HTTPException(status_code=422, detail=str(e))
        vqe_result = run_vqe(ham_data)
        coord_result = extract_binding_sites(vqe_result.one_rdm, atom_id=atom_id)
        ground_state_energy = vqe_result.ground_state_energy
        convergence_history = vqe_result.convergence_history
        num_iterations = vqe_result.num_iterations
    else:
        # Downstream-only proxy: no VQE, estimate the map from known coordination chemistry.
        coord_result = estimate_coordination_from_literature(
            atom_id, atom.typical_coordination_number
        )
        ground_state_energy = None
        convergence_history = []
        num_iterations = 0

    protein_result = design_protein(coord_result, donor_preference=atom.donor_preference)
    construct_seq, construct_positions = build_foldable_construct(protein_result.binding_residues)
    handoff = build_handoff(
        atom_id=atom_id,
        ground_state_energy=ground_state_energy,
        coordination=coord_result,
        protein=protein_result,
    )

    return {
        "atom_id": atom_id,
        "tier": atom.tier.value,
        "map_source": coord_result.source,            # "vqe" or "literature"
        "ground_state_energy": ground_state_energy,
        "known_ground_state": atom.known_ground_state_hartree,
        "convergence_history": convergence_history,
        "num_iterations": num_iterations,
        "orbital_occupancies": coord_result.orbital_occupancies,
        "empty_orbital_indices": coord_result.empty_orbital_indices,
        "coordination_number": coord_result.coordination_number,
        "geometry": coord_result.geometry.value,
        "binding_residues": protein_result.binding_residues,
        "binding_positions": protein_result.binding_positions,
        "sequence": protein_result.sequence,
        "fasta": protein_result.fasta,
        "foldable_construct": construct_seq,
        "foldable_binding_positions": construct_positions,
        "binding_confidence": handoff.binding_confidence,
        "handoff_json": handoff.to_json(),
    }


@app.get("/pipeline/fold")
def fold(sequence: str):
    """Predict the 3D fold of a sequence with ESMFold; return pLDDT confidence + PDB.

    This is the one genuinely-simulatable bio step (BPD Build 1). High pLDDT means the
    sequence folds confidently — NOT that the protein binds the metal or works in a cell.
    """
    try:
        result = fold_sequence(sequence)
    except InvalidSequenceError as e:
        # Bad input is the client's fault, not the upstream service's.
        raise HTTPException(status_code=400, detail=str(e))
    except FoldingError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {
        "sequence": result.sequence,
        "n_residues": result.n_residues,
        "mean_plddt": result.mean_plddt,
        "per_residue_plddt": result.per_residue_plddt,
        "pdb": result.pdb,
        "source": result.source,
    }


@app.get("/pipeline/prime-edit")
def prime_edit(protein: str):
    """Design the prime edit that writes the protein's gene into D. radiodurans.

    Codon-optimizes the protein for the GC-rich genome, designs a (simplified) pegRNA
    against a representative locus, and returns the before -> after DNA. This is the
    *design* of the edit (computable) — not a prediction of whether the cell survives.
    """
    try:
        plan = design_prime_edit(protein)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "locus_name": plan.locus_name,
        "protein": plan.protein,
        "gene_dna": plan.gene_dna,
        "gene_length_bp": plan.gene_length_bp,
        "gc_content": plan.gc_content,
        "spacer": plan.spacer,
        "pam": plan.pam,
        "pbs": plan.pbs,
        "rtt": plan.rtt,
        "before": plan.before,
        "after": plan.after,
        "insert_index": plan.insert_index,
    }


@app.get("/pipeline/qaoa-search")
def qaoa_search(
    binding_strength: float,
    n_residues: int = 2,
    atom_id: str = "h2",
    geometry: str = "linear",
):
    """QAOA search over peptide space for the best binder against a binding site.

    Takes the electron-deficiency (binding_strength) from a completed VQE run so it does
    not re-run VQE. Returns ranked candidates, the brute-force optimum for validation, and
    a self-contained `handoff_block` (the QAOA-recommended sequence scaffolded into a full
    FASTA) ready to be merged into the bio-team handoff package.
    """
    result = run_qaoa_search(binding_strength=binding_strength, n_residues=n_residues)

    # Turn QAOA's chosen core residues into a complete, AlphaFold-ready sequence.
    core_residues = list(result.best_sequence)
    scaffolded = scaffold_binding_residues(core_residues)
    fasta = (
        f">HALOS_{atom_id.upper()}_qaoa_binding_protein | "
        f"coord={geometry} | core={result.best_sequence} | search=qaoa | "
        f"reached_optimum={result.found_optimum}\n{scaffolded}"
    )

    ranked = [
        {"sequence": c.sequence, "cost": c.cost, "probability": c.probability}
        for c in result.ranked_candidates
    ]

    handoff_block = {
        "method": "QAOA (Quantum Approximate Optimization Algorithm)",
        "recommended_core_residues": core_residues,
        "recommended_sequence": scaffolded,
        "recommended_fasta": fasta,
        "best_cost": result.best_cost,
        "reached_global_optimum": result.found_optimum,
        "brute_force_optimum": result.brute_force_optimum,
        "brute_force_cost": result.brute_force_cost,
        "search_space_size": result.search_space_size,
        "n_qubits": result.n_qubits,
        "qaoa_reps": result.reps,
        "ranked_alternatives": ranked,
    }

    return {
        "n_residues": result.n_residues,
        "n_qubits": result.n_qubits,
        "reps": result.reps,
        "search_space_size": result.search_space_size,
        "alphabet": result.alphabet,
        "ranked_candidates": ranked,
        "best_sequence": result.best_sequence,
        "best_cost": result.best_cost,
        "brute_force_optimum": result.brute_force_optimum,
        "brute_force_cost": result.brute_force_cost,
        "found_optimum": result.found_optimum,
        "convergence_history": result.convergence_history,
        "recommended_sequence": scaffolded,
        "recommended_fasta": fasta,
        "handoff_block": handoff_block,
    }
