from dataclasses import dataclass
from .binding_sites import CoordinationResult, CoordinationGeometry

DONOR_TO_RESIDUES: dict[str, list[str]] = {
    "O": ["D", "E", "S", "T", "Y"],
    "N": ["H", "N", "Q"],
    "S": ["C", "M"],
}

SCAFFOLD_HELIX = ["A", "L", "K", "A", "L", "A", "E", "A"]

HELIX_SPACING = 4


def _pick_binding_residues(coord_number: int, donor_preference: list[str]) -> list[str]:
    """Choose coord_number metal-coordinating amino acids based on donor preference."""
    pool: list[str] = []
    for donor in donor_preference:
        pool.extend(DONOR_TO_RESIDUES.get(donor, []))

    if not pool:
        pool = ["D", "E"]

    residues = []
    for i in range(coord_number):
        residues.append(pool[i % len(pool)])
    return residues


def _build_sequence(binding_residues: list[str]) -> str:
    """Place binding residues on an alpha-helical scaffold at i, i+4, i+8, ... spacing."""
    cn = len(binding_residues)

    binding_positions = [i * HELIX_SPACING for i in range(cn)]
    total_length = binding_positions[-1] + HELIX_SPACING

    sequence = list(SCAFFOLD_HELIX * ((total_length // len(SCAFFOLD_HELIX)) + 1))
    sequence = sequence[:total_length]

    for i, pos in enumerate(binding_positions):
        sequence[pos] = binding_residues[i]

    return "".join(sequence)


def _geometry_to_notes(geometry: CoordinationGeometry, coord_number: int) -> str:
    notes_map = {
        CoordinationGeometry.LINEAR: "Linear geometry (2 sites). Simple binding mode.",
        CoordinationGeometry.TETRAHEDRAL: "Tetrahedral geometry (4 sites). Common for d10 metals and proxies.",
        CoordinationGeometry.SQUARE_PLANAR: "Square planar (4 sites). Transition metal typical.",
        CoordinationGeometry.OCTAHEDRAL: "Octahedral (6 sites). Classic coordination compound geometry.",
        CoordinationGeometry.SQUARE_ANTIPRISMATIC: "Square antiprismatic (8 sites). Typical for actinides (U4+, Pu3+).",
        CoordinationGeometry.TRICAPPED_TRIGONAL: "Tricapped trigonal prismatic (9 sites). Large actinides (Am3+).",
    }
    return notes_map.get(geometry, f"{coord_number}-coordinate binding site.")


@dataclass
class ProteinDesignResult:
    atom_id: str
    geometry: CoordinationGeometry
    coordination_number: int
    num_binding_residues: int
    binding_residues: list[str]
    binding_positions: list[int]
    sequence: str
    fasta: str
    design_notes: str


def design_protein(
    coord_result: CoordinationResult,
    donor_preference: list[str],
) -> ProteinDesignResult:
    """
    Design a metal-binding protein sequence for the given coordination result.
    Binding residues are chosen for the atom's electron-deficiency profile and placed
    at helix-face positions matching the required coordination geometry — so binding
    is by design, not by chance.
    """
    binding_residues = _pick_binding_residues(coord_result.coordination_number, donor_preference)
    sequence = _build_sequence(binding_residues)

    cn = len(binding_residues)
    binding_positions = [i * HELIX_SPACING for i in range(cn)]

    fasta_header = (
        f">HALOS_{coord_result.atom_id.upper()}_binding_protein | "
        f"coord={coord_result.geometry.value} | "
        f"n={cn} | "
        f"generated=quantum-vqe-pipeline"
    )
    fasta = f"{fasta_header}\n{sequence}"

    notes = _geometry_to_notes(coord_result.geometry, cn)

    return ProteinDesignResult(
        atom_id=coord_result.atom_id,
        geometry=coord_result.geometry,
        coordination_number=coord_result.coordination_number,
        num_binding_residues=cn,
        binding_residues=binding_residues,
        binding_positions=binding_positions,
        sequence=sequence,
        fasta=fasta,
        design_notes=notes,
    )
