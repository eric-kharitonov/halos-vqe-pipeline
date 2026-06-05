import json
from dataclasses import dataclass
from .binding_sites import CoordinationResult
from .protein_designer import ProteinDesignResult


@dataclass
class HandoffPackage:
    atom_id: str
    fasta: str
    ground_state_energy: float
    coordination: CoordinationResult
    protein: ProteinDesignResult
    candidate_rank: int
    binding_confidence: float

    def to_json(self) -> str:
        is_vqe = self.coordination.source == "vqe"
        return json.dumps({
            "atom_id": self.atom_id,
            "pipeline_version": "0.1.0",
            "candidate_rank": self.candidate_rank,
            "map_source": self.coordination.source,          # "vqe" | "literature"
            "binding_map": {
                "source": self.coordination.source,
                "method": (
                    "Quantum VQE 1-RDM orbital occupancies"
                    if is_vqe else
                    "Literature coordination chemistry — NO VQE (target too large to simulate)"
                ),
                # null when source != "vqe": there is deliberately no quantum energy for a proxy.
                "vqe_ground_state_energy_hartree": self.ground_state_energy,
                "geometry": self.coordination.geometry.value,
                "coordination_number": self.coordination.coordination_number,
                "empty_orbital_indices": self.coordination.empty_orbital_indices,
                "orbital_occupancies": self.coordination.orbital_occupancies,
                "mean_electron_deficiency": self.binding_confidence,
                "deficiency_note": (
                    "Mean fractional emptiness (1 - occupancy) of the binding orbitals — an "
                    "electron-deficiency measure, NOT a probability that the protein binds the metal."
                ),
            },
            "fasta": self.fasta,
            "sequence": self.protein.sequence,
            "num_binding_residues": self.protein.num_binding_residues,
            "binding_residues": self.protein.binding_residues,
            "binding_positions": self.protein.binding_positions,
            "design_notes": self.protein.design_notes,
            "next_step": (
                "Fold the FASTA with ESMFold (already wired into this pipeline) — or AlphaFold for a "
                "second opinion — and require mean pLDDT > 70 over the binding region before wet-lab "
                "synthesis. Then prime-edit the codon-optimized gene into D. radiodurans at a neutral "
                "intergenic locus (see the prime-edit stage). Binding affinity and in-cell expression "
                "are wet-lab outcomes, NOT predicted by this pipeline."
            ),
        }, indent=2)


def build_handoff(
    atom_id: str,
    ground_state_energy: float,
    coordination: CoordinationResult,
    protein: ProteinDesignResult,
    candidate_rank: int = 1,
) -> HandoffPackage:
    """Assemble the full pipeline output into a bio team handoff package."""
    binding_confidence = round(coordination.binding_strength_estimate, 3)

    return HandoffPackage(
        atom_id=atom_id,
        fasta=protein.fasta,
        ground_state_energy=ground_state_energy,
        coordination=coordination,
        protein=protein,
        candidate_rank=candidate_rank,
        binding_confidence=binding_confidence,
    )
