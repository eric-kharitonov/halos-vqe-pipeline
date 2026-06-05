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


def scaffold_binding_residues(binding_residues: list[str]) -> str:
    """Public: place a list of binding residues on the alpha-helical scaffold.

    Used to turn QAOA-selected core residues into a full, AlphaFold-ready sequence.
    """
    return _build_sequence(binding_residues)


# N-terminal scaffold length before the first binding residue, for foldable constructs.
_CONSTRUCT_LEAD = 8


def build_foldable_construct(
    binding_residues: list[str], min_length: int = 36
) -> tuple[str, list[int]]:
    """Embed the binding motif in a longer α-helical construct suitable for folding.

    The minimal designed motif is only ~8 residues — too short for ESMFold/AlphaFold to
    give a meaningful structure. This wraps the binding residues (still on one helix face,
    i, i+4, …) in N- and C-terminal scaffold so the whole construct is long enough to fold.

    Returns (sequence, binding_positions) where binding_positions index into the construct.
    """
    cn = len(binding_residues)
    binding_positions = [_CONSTRUCT_LEAD + i * HELIX_SPACING for i in range(cn)]
    total_length = max(binding_positions[-1] + _CONSTRUCT_LEAD + 1, min_length)

    sequence = list((SCAFFOLD_HELIX * (total_length // len(SCAFFOLD_HELIX) + 1))[:total_length])
    for i, pos in enumerate(binding_positions):
        sequence[pos] = binding_residues[i]

    return "".join(sequence), binding_positions


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
    at helix-face positions matching the required coordination geometry — so the design is
    deterministic and reproducible (the same map gives the same protein). Whether that
    protein actually binds the metal is a wet-lab outcome, not a guarantee of this step.
    """
    binding_residues = _pick_binding_residues(coord_result.coordination_number, donor_preference)
    sequence = _build_sequence(binding_residues)

    cn = len(binding_residues)
    binding_positions = [i * HELIX_SPACING for i in range(cn)]

    # Stamp the FASTA with the *true* provenance of the binding map: a quantum VQE run,
    # or a literature-coordination estimate (proxies). Never claim VQE for a proxy.
    provenance = "quantum-vqe-pipeline" if coord_result.source == "vqe" else "literature-coordination"
    fasta_header = (
        f">HALOS_{coord_result.atom_id.upper()}_binding_protein | "
        f"coord={coord_result.geometry.value} | "
        f"n={cn} | "
        f"generated={provenance}"
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
