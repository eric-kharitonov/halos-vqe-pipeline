from dataclasses import dataclass
from enum import Enum
from typing import Optional

class CoordinationClass(str, Enum):
    DIATOMIC = "diatomic"
    ALKALI = "alkali"
    ALKALINE = "alkaline"
    TRANSITION = "transition"
    LANTHANIDE = "lanthanide"
    ACTINIDE = "actinide"

@dataclass
class AtomConfig:
    id: str
    symbol: str
    name: str
    num_qubits: int
    coordination_class: CoordinationClass
    typical_coordination_number: int
    donor_preference: list[str]
    known_ground_state_hartree: Optional[float] = None
    hamiltonian_file: Optional[str] = None
    is_placeholder: bool = False
    notes: str = ""

_REGISTRY: dict[str, AtomConfig] = {}

def _register(atom: AtomConfig) -> AtomConfig:
    _REGISTRY[atom.id] = atom
    return atom

# --- Proof-of-concept atoms (runnable today) ---

H2 = _register(AtomConfig(
    id="h2",
    symbol="H₂",
    name="Hydrogen (H2)",
    num_qubits=4,
    coordination_class=CoordinationClass.DIATOMIC,
    typical_coordination_number=2,
    donor_preference=["O", "N"],
    known_ground_state_hartree=-1.1373,
    hamiltonian_file="h2_sto3g.json",
    notes="Reference molecule. VQE result ~-1.1373 Hartree at R=0.735 Å, STO-3G, "
          "full 4-qubit Jordan-Wigner.",
))

LIH = _register(AtomConfig(
    id="lih",
    symbol="LiH",
    name="Lithium Hydride (LiH)",
    num_qubits=6,
    coordination_class=CoordinationClass.ALKALI,
    typical_coordination_number=4,
    donor_preference=["O", "N"],
    known_ground_state_hartree=-7.8631,
    hamiltonian_file="lih_sto3g.json",
    notes="Proxy for alkali-like coordination. Active space (2e, 3 orbitals), 6 qubits.",
))

# --- Actinide proxy metals (safe, non-radioactive lab validation) ---

CE3 = _register(AtomConfig(
    id="ce3",
    symbol="Ce³⁺",
    name="Cerium(III) — Actinide Proxy",
    num_qubits=6,
    coordination_class=CoordinationClass.LANTHANIDE,
    typical_coordination_number=8,
    donor_preference=["O"],
    is_placeholder=True,
    notes="Primary actinide proxy. Similar f-orbital coordination chemistry to U/Pu. "
          "Use cerium(III) in lab; quantum sim not yet runnable.",
))

LA3 = _register(AtomConfig(
    id="la3",
    symbol="La³⁺",
    name="Lanthanum(III) — Actinide Proxy",
    num_qubits=6,
    coordination_class=CoordinationClass.LANTHANIDE,
    typical_coordination_number=9,
    donor_preference=["O"],
    is_placeholder=True,
    notes="Secondary actinide proxy. 9-coordinate, hard acid. "
          "Use lanthanum(III) in lab for Pu/Am proxying.",
))

# --- Actinide targets (placeholder — require fault-tolerant hardware) ---

U238 = _register(AtomConfig(
    id="u238",
    symbol="U⁴⁺",
    name="Uranium-238 (UO₂²⁺ target)",
    num_qubits=92,
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=8,
    donor_preference=["O"],
    is_placeholder=True,
    notes="Primary waste target (highest volume). Requires relativistic ECPs (Stuttgart). "
          "Fault-tolerant hardware needed. Pipeline ready to run when hardware available.",
))

PU239 = _register(AtomConfig(
    id="pu239",
    symbol="Pu³⁺",
    name="Plutonium-239",
    num_qubits=94,
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=9,
    donor_preference=["O", "N"],
    is_placeholder=True,
    notes="24,100 year half-life. Highest radioactivity target. "
          "Second priority after Uranium. Requires fault-tolerant hardware.",
))

NP237 = _register(AtomConfig(
    id="np237",
    symbol="Np⁴⁺",
    name="Neptunium-237",
    num_qubits=93,
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=8,
    donor_preference=["O"],
    is_placeholder=True,
    notes="2.14 million year half-life. Third priority target.",
))

AM241 = _register(AtomConfig(
    id="am241",
    symbol="Am³⁺",
    name="Americium-241",
    num_qubits=95,
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=9,
    donor_preference=["O", "N"],
    is_placeholder=True,
    notes="432 year half-life. Fourth priority target.",
))


def get_atom(atom_id: str) -> AtomConfig:
    if atom_id not in _REGISTRY:
        raise KeyError(f"Unknown atom id '{atom_id}'. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[atom_id]


def list_atoms() -> list[AtomConfig]:
    return list(_REGISTRY.values())
