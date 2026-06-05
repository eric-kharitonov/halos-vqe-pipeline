from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CoordinationClass(str, Enum):
    DIATOMIC = "diatomic"
    ALKALI = "alkali"
    ALKALINE = "alkaline"
    TRANSITION = "transition"
    LANTHANIDE = "lanthanide"
    ACTINIDE = "actinide"


class Tier(str, Enum):
    """How far down the pipeline a target can go, given today's compute.

    REAL_VQE    -> real VQE runs now (small molecule).
    PRECOMPUTED -> real Hamiltonian, verified; full pipeline + folding.
    TOY         -> tiny illustrative VQE; full downstream + folding.
    PROXY       -> too big for VQE; SKIP it, run downstream design + folding
                   from literature coordination chemistry (clearly labelled estimate).
    LOCKED      -> blocked; needs fault-tolerant hardware. Nothing runs.
    """
    REAL_VQE = "real_vqe"
    PRECOMPUTED = "precomputed"
    TOY = "toy"
    PROXY = "proxy"
    LOCKED = "locked"


# Short badge text shown on each atom tile (matches the original mockup).
TIER_BADGE = {
    Tier.REAL_VQE: "REAL VQE",
    Tier.PRECOMPUTED: "PRECOMPUTED",
    Tier.TOY: "TOY",
    Tier.PROXY: "PROXY",
    Tier.LOCKED: "LOCKED",
}


@dataclass
class AtomConfig:
    id: str
    symbol: str
    name: str
    tier: Tier
    num_qubits: int                 # real qubit count, or fault-tolerant estimate
    qubits_are_estimate: bool       # True -> display "~N (FT)"
    electrons: int
    coordination_class: CoordinationClass
    typical_coordination_number: int
    donor_preference: list[str]
    known_ground_state_hartree: Optional[float] = None
    hamiltonian_file: Optional[str] = None
    notes: str = ""

    @property
    def runs_vqe(self) -> bool:
        """Targets that execute a (real or toy) VQE now."""
        return self.tier in (Tier.REAL_VQE, Tier.PRECOMPUTED, Tier.TOY)

    @property
    def is_downstream_only(self) -> bool:
        """Proxies: skip VQE, run design + folding from literature chemistry."""
        return self.tier == Tier.PROXY

    @property
    def is_locked(self) -> bool:
        return self.tier == Tier.LOCKED

    @property
    def badge(self) -> str:
        return TIER_BADGE[self.tier]


_REGISTRY: dict[str, AtomConfig] = {}


def _register(atom: AtomConfig) -> AtomConfig:
    _REGISTRY[atom.id] = atom
    return atom


# --- Full quantum pipeline (real VQE runs now) ---

H2 = _register(AtomConfig(
    id="h2",
    symbol="H₂",
    name="Dihydrogen",
    tier=Tier.REAL_VQE,
    num_qubits=4,
    qubits_are_estimate=False,
    electrons=2,
    coordination_class=CoordinationClass.DIATOMIC,
    typical_coordination_number=2,
    donor_preference=["O", "N"],
    known_ground_state_hartree=-1.1373,
    hamiltonian_file="h2_sto3g.json",
    notes="Reference molecule. Real VQE, STO-3G, 4-qubit Jordan-Wigner. "
          "Ground state ~-1.1373 Ha at R=0.735 Å.",
))

LIH = _register(AtomConfig(
    id="lih",
    symbol="LiH",
    name="Lithium hydride",
    tier=Tier.PRECOMPUTED,
    num_qubits=6,
    qubits_are_estimate=False,
    electrons=4,
    coordination_class=CoordinationClass.ALKALI,
    typical_coordination_number=4,
    donor_preference=["O", "N"],
    known_ground_state_hartree=-7.8631,
    hamiltonian_file="lih_sto3g.json",
    notes="Alkali-like coordination. Verified Hamiltonian, active space (2e, 3 orbitals), 6 qubits.",
))

T = _register(AtomConfig(
    id="t",
    symbol="T (³H)",
    name="Tritium (toy isotope)",
    tier=Tier.TOY,
    num_qubits=2,
    qubits_are_estimate=False,
    electrons=1,
    coordination_class=CoordinationClass.DIATOMIC,
    typical_coordination_number=1,
    donor_preference=["O", "N"],
    known_ground_state_hartree=-0.466,
    hamiltonian_file="t_sto3g.json",
    notes="Toy single-orbital hydrogenic system (tritium is electronically hydrogen). "
          "2 qubits, illustrative VQE.",
))

# --- Downstream-only proxies (no VQE; design + folding from literature chemistry) ---

CS = _register(AtomConfig(
    id="cs",
    symbol="Cs⁺",
    name="Cesium-137 proxy (Cs⁺)",
    tier=Tier.PROXY,
    num_qubits=30,
    qubits_are_estimate=True,
    electrons=55,
    coordination_class=CoordinationClass.ALKALI,
    typical_coordination_number=8,
    donor_preference=["O"],
    notes="Major fission product. Large soft monovalent cation; ~8-coordinate, hard-O donors "
          "(carboxylates/crowns). Too big for VQE today — downstream design runs from "
          "literature coordination, not a quantum-computed map.",
))

SR = _register(AtomConfig(
    id="sr",
    symbol="Sr²⁺",
    name="Strontium-90 proxy (Sr²⁺)",
    tier=Tier.PROXY,
    num_qubits=24,
    qubits_are_estimate=True,
    electrons=38,
    coordination_class=CoordinationClass.ALKALINE,
    typical_coordination_number=8,
    donor_preference=["O"],
    notes="Major fission product, bone-seeker. Ca-like, ~8-coordinate, hard-O donors. "
          "Downstream design from literature coordination; VQE not feasible today.",
))

# --- Locked actinide targets (need fault-tolerant hardware) ---

U = _register(AtomConfig(
    id="u",
    symbol="U",
    name="Uranium (UO₂²⁺)",
    tier=Tier.LOCKED,
    num_qubits=80,
    qubits_are_estimate=True,
    electrons=92,
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=8,
    donor_preference=["O"],
    notes="Primary waste target (highest volume). Uranyl is ~8-coordinate in the equatorial "
          "plane. Requires relativistic ECPs and fault-tolerant hardware.",
))

PU = _register(AtomConfig(
    id="pu",
    symbol="Pu",
    name="Plutonium (Pu⁴⁺)",
    tier=Tier.LOCKED,
    num_qubits=94,
    qubits_are_estimate=True,
    electrons=94,
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=9,
    donor_preference=["O", "N"],
    notes="24,100 year half-life; highest radioactivity target. Second priority after uranium.",
))

NP = _register(AtomConfig(
    id="np",
    symbol="Np",
    name="Neptunium (NpO₂⁺)",
    tier=Tier.LOCKED,
    num_qubits=82,
    qubits_are_estimate=True,
    electrons=93,
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=8,
    donor_preference=["O"],
    notes="2.14 million year half-life. Third priority target.",
))

AM = _register(AtomConfig(
    id="am",
    symbol="Am",
    name="Americium (Am³⁺)",
    tier=Tier.LOCKED,
    num_qubits=87,
    qubits_are_estimate=True,
    electrons=95,
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=9,
    donor_preference=["O", "N"],
    notes="432 year half-life. Fourth priority target.",
))


def get_atom(atom_id: str) -> AtomConfig:
    if atom_id not in _REGISTRY:
        raise KeyError(f"Unknown atom id '{atom_id}'. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[atom_id]


def list_atoms() -> list[AtomConfig]:
    return list(_REGISTRY.values())
