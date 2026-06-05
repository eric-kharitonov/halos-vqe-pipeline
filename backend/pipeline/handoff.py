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
        return json.dumps({
            "atom_id": self.atom_id,
            "candidate_rank": self.candidate_rank,
            "binding_confidence": self.binding_confidence,
            "fasta": self.fasta,
            "sequence": self.protein.sequence,
            "num_binding_residues": self.protein.num_binding_residues,
            "binding_residues": self.protein.binding_residues,
            "binding_positions": self.protein.binding_positions,
            "vqe": {
                "ground_state_energy_hartree": self.ground_state_energy,
            },
            "coordination": {
                "geometry": self.coordination.geometry.value,
                "coordination_number": self.coordination.coordination_number,
                "empty_orbital_indices": self.coordination.empty_orbital_indices,
                "orbital_occupancies": self.coordination.orbital_occupancies,
                "binding_strength_estimate": self.coordination.binding_strength_estimate,
            },
            "design_notes": self.protein.design_notes,
            "pipeline_version": "0.1.0",
            "next_step": (
                "Submit FASTA to AlphaFold2 (ColabFold) for structure prediction. "
                "pLDDT > 70 at binding region required to proceed to wet lab synthesis. "
                "Then prime-edit into D. radiodurans at DR_0906 locus."
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
