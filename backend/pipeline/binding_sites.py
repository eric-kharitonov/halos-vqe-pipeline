from dataclasses import dataclass
from enum import Enum
import numpy as np

EMPTY_THRESHOLD = 0.3   # orbital with occupancy < this is "empty" = binding site
FILLED_THRESHOLD = 0.7  # orbital with occupancy > this is "filled" = not binding site


class CoordinationGeometry(str, Enum):
    LINEAR = "linear"
    TRIGONAL = "trigonal"
    TETRAHEDRAL = "tetrahedral"
    SQUARE_PLANAR = "square_planar"
    TRIGONAL_BIPYRAMIDAL = "trigonal_bipyramidal"
    OCTAHEDRAL = "octahedral"
    PENTAGONAL_BIPYRAMIDAL = "pentagonal_bipyramidal"
    SQUARE_ANTIPRISMATIC = "square_antiprismatic"
    TRICAPPED_TRIGONAL = "tricapped_trigonal"
    UNKNOWN = "unknown"


def _infer_geometry(coord_number: int, atom_id: str) -> CoordinationGeometry:
    """Infer coordination geometry from the number of empty orbitals."""
    geo_map = {
        2: CoordinationGeometry.LINEAR,
        3: CoordinationGeometry.TRIGONAL,
        4: CoordinationGeometry.TETRAHEDRAL,
        5: CoordinationGeometry.TRIGONAL_BIPYRAMIDAL,
        6: CoordinationGeometry.OCTAHEDRAL,
        7: CoordinationGeometry.PENTAGONAL_BIPYRAMIDAL,
        8: CoordinationGeometry.SQUARE_ANTIPRISMATIC,
        9: CoordinationGeometry.TRICAPPED_TRIGONAL,
    }
    return geo_map.get(coord_number, CoordinationGeometry.UNKNOWN)


@dataclass
class CoordinationResult:
    atom_id: str
    orbital_occupancies: list[float]
    empty_orbital_indices: list[int]
    coordination_number: int
    geometry: CoordinationGeometry
    binding_strength_estimate: float
    source: str = "vqe"   # "vqe" = quantum-computed; "literature" = proxy estimate


def extract_binding_sites(one_rdm: np.ndarray, atom_id: str) -> CoordinationResult:
    """
    Extract coordination sites from the 1-particle reduced density matrix.
    Empty orbitals (low occupancy) are the binding sites: electron-deficient regions
    where a protein donor group can form a coordinate bond. This is the QPD's
    'identifying weak links' step.
    """
    occupancies = np.diag(one_rdm).real.tolist()

    empty_indices = [i for i, occ in enumerate(occupancies) if occ < EMPTY_THRESHOLD]

    coord_number = len(empty_indices)
    geometry = _infer_geometry(coord_number, atom_id)

    if empty_indices:
        deficiencies = [1.0 - occupancies[i] for i in empty_indices]
        binding_strength = float(np.mean(deficiencies))
    else:
        binding_strength = 0.0

    return CoordinationResult(
        atom_id=atom_id,
        orbital_occupancies=occupancies,
        empty_orbital_indices=empty_indices,
        coordination_number=coord_number,
        geometry=geometry,
        binding_strength_estimate=binding_strength,
        source="vqe",
    )


def estimate_coordination_from_literature(
    atom_id: str, coordination_number: int, binding_strength: float = 0.9
) -> CoordinationResult:
    """Build a coordination map for a proxy WITHOUT VQE, from known coordination chemistry.

    Used for targets too large to simulate (Cs⁺, Sr²⁺): we know their coordination number
    and donor preference from the literature, so we can still drive the downstream protein
    design + folding. The result is explicitly marked `source="literature"` — it is an
    estimate, not a quantum-computed electron-density map.
    """
    # Represent the literature coordination as `coordination_number` empty orbitals
    # plus two filled ones, so the same downstream code path applies.
    occupancies = [0.05] * coordination_number + [0.95] * 2
    geometry = _infer_geometry(coordination_number, atom_id)
    return CoordinationResult(
        atom_id=atom_id,
        orbital_occupancies=occupancies,
        empty_orbital_indices=list(range(coordination_number)),
        coordination_number=coordination_number,
        geometry=geometry,
        binding_strength_estimate=binding_strength,
        source="literature",
    )
