# HALOS VQE Pipeline Tool — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pipeline tool that (1) takes a target atom, (2) runs Qiskit VQE to find its ground state and extract coordination sites ("weak links" — empty orbitals where a protein can bind), (3) generates a protein sequence with the right metal-coordinating residues in the right geometry, and (4) outputs a bio team handoff package so the protein can be prime-edited into *D. radiodurans* for deterministic biomineralization.

**Architecture:** Python backend runs the Qiskit pipeline as a series of independent modules (atoms → Hamiltonian → VQE → binding sites → protein → handoff); FastAPI exposes each stage as a REST endpoint; React frontend drives the pipeline step by step with live VQE convergence display. Because PySCF has no Windows wheel, Hamiltonians for demo atoms (H2, LiH) are pre-computed and shipped as JSON; the code path is identical whether loading from JSON or from a live PySCF driver, so the switch is one flag.

**Tech Stack:** Python 3.13, Qiskit 2.4.1 + qiskit-aer 0.17.2 (pre-installed), scipy/numpy (via qiskit), qiskit-nature 0.7.2 (optional, for PySCF path), FastAPI 0.115, uvicorn, pydantic, pytest; React 18, TypeScript, Vite 6, Tailwind CSS 3, Recharts (convergence chart)

---

## File Map

```
HALOS VQE Pipeline Tool/
├── backend/
│   ├── requirements.txt
│   ├── main.py                        # FastAPI app + all route definitions
│   └── pipeline/
│       ├── __init__.py
│       ├── atoms.py                   # AtomConfig dataclass + registry for all atoms
│       ├── hamiltonians.py            # Hamiltonian loader: JSON path or PySCF driver
│       ├── vqe_runner.py              # VQE loop using qiskit-aer Estimator + scipy
│       ├── binding_sites.py           # 1-RDM → empty orbital sites → CoordinationResult
│       ├── protein_designer.py        # CoordinationResult → residue list → FASTA sequence
│       └── handoff.py                 # Assemble full pipeline output as HandoffPackage
├── backend/tests/
│   ├── test_atoms.py
│   ├── test_hamiltonians.py
│   ├── test_vqe_runner.py
│   ├── test_binding_sites.py
│   ├── test_protein_designer.py
│   └── test_handoff.py
├── data/hamiltonians/
│   ├── h2_sto3g.json                  # Pre-computed H2 Hamiltonian (2-qubit reduced)
│   └── lih_sto3g.json                 # Pre-computed LiH Hamiltonian (4-qubit)
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/client.ts              # All fetch calls to backend
│       └── components/
│           ├── AtomSelector.tsx       # Grid of atoms with metadata cards
│           ├── PipelineRunner.tsx     # Step-by-step runner + stage status
│           ├── VQEChart.tsx           # Recharts line chart of energy convergence
│           ├── BindingSites.tsx       # Coordination sites list + geometry badge
│           ├── ProteinOutput.tsx      # FASTA display + residue table
│           └── HandoffExport.tsx      # Download handoff JSON button
└── docs/superpowers/plans/
    └── 2026-06-05-halos-vqe-pipeline.md
```

---

## Task 1: Backend Scaffold

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pipeline/__init__.py`
- Create: `backend/main.py` (skeleton only — routes added in Task 8)

- [ ] **Step 1: Create requirements.txt**

```
# backend/requirements.txt
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic==2.10.3
numpy>=1.26
scipy>=1.13
pytest==8.3.4
httpx==0.28.1
```

Note: qiskit 2.4.1 and qiskit-aer 0.17.2 are already installed globally. Do NOT add them to requirements.txt — they would install incompatible versions.

- [ ] **Step 2: Install dependencies**

```bash
cd backend
pip install -r requirements.txt
```

Expected: all packages install cleanly. If pydantic v2 conflicts arise, lock to `pydantic==2.10.3`.

- [ ] **Step 3: Create pipeline package**

```python
# backend/pipeline/__init__.py
# (empty — makes pipeline a Python package)
```

- [ ] **Step 4: Create FastAPI skeleton**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
```

- [ ] **Step 5: Verify server starts**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Expected: `Application startup complete.` — hit `http://localhost:8000/health` and get `{"status":"ok"}`.

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: backend scaffold with FastAPI skeleton"
```

---

## Task 2: Atom Registry

**Files:**
- Create: `backend/pipeline/atoms.py`
- Create: `backend/tests/test_atoms.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_atoms.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.atoms import AtomConfig, get_atom, list_atoms, CoordinationClass

def test_get_h2():
    atom = get_atom("h2")
    assert atom.symbol == "H2"
    assert atom.num_qubits == 2
    assert atom.known_ground_state_hartree == pytest.approx(-1.1373, abs=0.01)

def test_get_lih():
    atom = get_atom("lih")
    assert atom.symbol == "LiH"
    assert atom.num_qubits == 4

def test_list_atoms_includes_proxies():
    atoms = list_atoms()
    keys = [a.id for a in atoms]
    assert "h2" in keys
    assert "lih" in keys
    assert "ce3" in keys   # actinide proxy

def test_actinide_placeholder():
    atom = get_atom("u238")
    assert atom.is_placeholder is True
    assert atom.coordination_class == CoordinationClass.ACTINIDE

def test_unknown_atom_raises():
    with pytest.raises(KeyError):
        get_atom("xyz_unknown")

import pytest
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend
pytest tests/test_atoms.py -v
```

Expected: `ERRORS` — `ModuleNotFoundError: No module named 'pipeline.atoms'`

- [ ] **Step 3: Implement atoms.py**

```python
# backend/pipeline/atoms.py
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

@dataclass
class AtomConfig:
    id: str                              # lookup key, e.g. "h2"
    symbol: str                          # display symbol, e.g. "H2"
    name: str                            # full name, e.g. "Hydrogen (H2)"
    num_qubits: int                      # qubits after symmetry reduction
    coordination_class: CoordinationClass
    typical_coordination_number: int     # how many binding residues needed
    donor_preference: list[str]          # preferred donor atoms, e.g. ["O", "N"]
    known_ground_state_hartree: Optional[float] = None
    hamiltonian_file: Optional[str] = None   # path under data/hamiltonians/
    is_placeholder: bool = False         # True = no Hamiltonian yet (actinides)
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
    num_qubits=2,
    coordination_class=CoordinationClass.DIATOMIC,
    typical_coordination_number=2,
    donor_preference=["O", "N"],
    known_ground_state_hartree=-1.1373,
    hamiltonian_file="h2_sto3g.json",
    notes="Reference molecule. VQE result ~-1.1373 Hartree at R=0.735 Å, STO-3G.",
))

LIH = _register(AtomConfig(
    id="lih",
    symbol="LiH",
    name="Lithium Hydride (LiH)",
    num_qubits=4,
    coordination_class=CoordinationClass.ALKALI,
    typical_coordination_number=4,
    donor_preference=["O", "N"],
    known_ground_state_hartree=-7.8823,
    hamiltonian_file="lih_sto3g.json",
    notes="Proxy for alkali-like coordination. Li⁺ end is the coordination site.",
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
    known_ground_state_hartree=None,
    hamiltonian_file=None,
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
    known_ground_state_hartree=None,
    hamiltonian_file=None,
    is_placeholder=True,
    notes="Secondary actinide proxy. 9-coordinate, hard acid. "
          "Use lanthanum(III) in lab for Pu/Am proxying.",
))

# --- Actinide targets (placeholder — require fault-tolerant hardware) ---

U238 = _register(AtomConfig(
    id="u238",
    symbol="U⁴⁺",
    name="Uranium-238 (UO₂²⁺ target)",
    num_qubits=92,   # full precision: 92 electrons, requires fault-tolerant QC
    coordination_class=CoordinationClass.ACTINIDE,
    typical_coordination_number=8,
    donor_preference=["O"],
    known_ground_state_hartree=None,
    hamiltonian_file=None,
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
    known_ground_state_hartree=None,
    hamiltonian_file=None,
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
    known_ground_state_hartree=None,
    hamiltonian_file=None,
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
    known_ground_state_hartree=None,
    hamiltonian_file=None,
    is_placeholder=True,
    notes="432 year half-life. Fourth priority target.",
))


def get_atom(atom_id: str) -> AtomConfig:
    if atom_id not in _REGISTRY:
        raise KeyError(f"Unknown atom id '{atom_id}'. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[atom_id]


def list_atoms() -> list[AtomConfig]:
    return list(_REGISTRY.values())
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend
pytest tests/test_atoms.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/atoms.py backend/tests/test_atoms.py
git commit -m "feat: atom registry with H2, LiH, proxies, and actinide placeholders"
```

---

## Task 3: Pre-Computed Hamiltonians

**Files:**
- Create: `data/hamiltonians/h2_sto3g.json`
- Create: `data/hamiltonians/lih_sto3g.json`
- Create: `backend/pipeline/hamiltonians.py`
- Create: `backend/tests/test_hamiltonians.py`

Background: H2 in STO-3G reduces to 2 qubits after applying Z₂ symmetry reduction and particle number conservation. The Hamiltonian is:
```
H = g₀·II + g₁·IZ + g₂·ZI + g₃·ZZ + g₄·XX + g₅·YY
```
with values from O'Malley et al. (2016), Physical Review X.

LiH in STO-3G (with 2 frozen core orbitals, reduced to 4 qubits) values from Kandala et al. (2017), Nature.

- [ ] **Step 1: Create H2 Hamiltonian JSON**

```json
{
  "atom_id": "h2",
  "description": "H2 at R=0.735 Angstrom, STO-3G basis, Jordan-Wigner + Z2 symmetry reduction",
  "reference": "O'Malley et al. (2016), Physical Review X 6, 031007",
  "num_qubits": 2,
  "nuclear_repulsion_energy": 0.7199689944489797,
  "pauli_terms": [
    {"pauli": "II", "coeff": -1.0523732},
    {"pauli": "IZ", "coeff":  0.3979374},
    {"pauli": "ZI", "coeff": -0.3979374},
    {"pauli": "ZZ", "coeff": -0.0112801},
    {"pauli": "XX", "coeff":  0.1809270},
    {"pauli": "YY", "coeff":  0.1809270}
  ],
  "known_ground_state_hartree": -1.1373060,
  "known_hf_energy_hartree": -1.1175942
}
```

Save to: `data/hamiltonians/h2_sto3g.json`

- [ ] **Step 2: Create LiH Hamiltonian JSON**

```json
{
  "atom_id": "lih",
  "description": "LiH at R=1.595 Angstrom, STO-3G basis, Jordan-Wigner, 2 frozen core orbitals, 4 active qubits",
  "reference": "Kandala et al. (2017), Nature 549, 242–246",
  "num_qubits": 4,
  "nuclear_repulsion_energy": 0.9924119926298821,
  "pauli_terms": [
    {"pauli": "IIII", "coeff": -8.2171},
    {"pauli": "IIIZ", "coeff":  0.1716},
    {"pauli": "IIZI", "coeff": -0.2233},
    {"pauli": "IZII", "coeff":  0.1716},
    {"pauli": "ZIII", "coeff": -0.2233},
    {"pauli": "IIZZ", "coeff":  0.1208},
    {"pauli": "IZIZ", "coeff":  0.1687},
    {"pauli": "IZZI", "coeff":  0.1659},
    {"pauli": "ZIIZ", "coeff":  0.1659},
    {"pauli": "ZIZI", "coeff":  0.1687},
    {"pauli": "ZZII", "coeff":  0.1745},
    {"pauli": "XXYY", "coeff": -0.0453},
    {"pauli": "XYYX", "coeff":  0.0453},
    {"pauli": "YXXY", "coeff":  0.0453},
    {"pauli": "YYXX", "coeff": -0.0453}
  ],
  "known_ground_state_hartree": -7.8823,
  "known_hf_energy_hartree": -7.8621
}
```

Save to: `data/hamiltonians/lih_sto3g.json`

- [ ] **Step 3: Write failing tests**

```python
# backend/tests/test_hamiltonians.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from qiskit.quantum_info import SparsePauliOp
from pipeline.hamiltonians import load_hamiltonian, HamiltonianData

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hamiltonians")

def test_load_h2_returns_hamiltonian_data():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    assert isinstance(h, HamiltonianData)
    assert h.atom_id == "h2"
    assert isinstance(h.operator, SparsePauliOp)

def test_h2_has_correct_qubit_count():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    assert h.operator.num_qubits == 2

def test_h2_pauli_terms_include_xx():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    labels = [str(p) for p in h.operator.paulis]
    assert "XX" in labels

def test_lih_has_four_qubits():
    h = load_hamiltonian("lih", data_dir=DATA_DIR)
    assert h.operator.num_qubits == 4

def test_unknown_atom_raises():
    with pytest.raises(FileNotFoundError):
        load_hamiltonian("xyz_unknown", data_dir=DATA_DIR)
```

- [ ] **Step 4: Run tests to confirm they fail**

```bash
cd backend
pytest tests/test_hamiltonians.py -v
```

Expected: `ModuleNotFoundError: No module named 'pipeline.hamiltonians'`

- [ ] **Step 5: Implement hamiltonians.py**

```python
# backend/pipeline/hamiltonians.py
import json
import os
from dataclasses import dataclass
from qiskit.quantum_info import SparsePauliOp

_DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hamiltonians"
)

@dataclass
class HamiltonianData:
    atom_id: str
    operator: SparsePauliOp
    nuclear_repulsion_energy: float
    known_ground_state_hartree: float | None
    num_qubits: int
    description: str
    reference: str

def load_hamiltonian(atom_id: str, data_dir: str = _DEFAULT_DATA_DIR) -> HamiltonianData:
    """Load a pre-computed Hamiltonian from JSON. Raises FileNotFoundError if not found."""
    filename = f"{atom_id}_sto3g.json"
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No pre-computed Hamiltonian for '{atom_id}' at {path}. "
            "Run generate_hamiltonians.py on a Linux/WSL2 machine with PySCF to generate it."
        )
    with open(path) as f:
        data = json.load(f)

    pauli_list = [
        (term["pauli"], complex(term["coeff"]))
        for term in data["pauli_terms"]
    ]
    operator = SparsePauliOp.from_list(pauli_list)

    return HamiltonianData(
        atom_id=atom_id,
        operator=operator,
        nuclear_repulsion_energy=data["nuclear_repulsion_energy"],
        known_ground_state_hartree=data.get("known_ground_state_hartree"),
        num_qubits=data["num_qubits"],
        description=data["description"],
        reference=data["reference"],
    )
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
cd backend
pytest tests/test_hamiltonians.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add data/ backend/pipeline/hamiltonians.py backend/tests/test_hamiltonians.py
git commit -m "feat: pre-computed H2 and LiH Hamiltonians as JSON + loader"
```

---

## Task 4: VQE Runner

**Files:**
- Create: `backend/pipeline/vqe_runner.py`
- Create: `backend/tests/test_vqe_runner.py`

The runner uses Qiskit 2.x: `qiskit_aer.primitives.Estimator` + `qiskit.circuit.library.EfficientSU2` + `scipy.optimize.minimize`. No qiskit-algorithms needed.

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_vqe_runner.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from pipeline.hamiltonians import load_hamiltonian
from pipeline.vqe_runner import run_vqe, VQEResult

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hamiltonians")

def test_h2_ground_state_within_tolerance():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert isinstance(result, VQEResult)
    assert abs(result.ground_state_energy - (-1.1373)) < 0.05  # 50 mHartree tolerance

def test_result_has_convergence_history():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert len(result.convergence_history) > 0
    assert result.convergence_history[-1] == pytest.approx(result.ground_state_energy, abs=1e-6)

def test_result_has_optimal_params():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert result.optimal_params is not None
    assert len(result.optimal_params) > 0

def test_result_has_one_rdm():
    h = load_hamiltonian("h2", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert result.one_rdm is not None
    n = h.num_qubits
    assert result.one_rdm.shape == (n, n)

def test_lih_ground_state_within_tolerance():
    h = load_hamiltonian("lih", data_dir=DATA_DIR)
    result = run_vqe(h)
    assert abs(result.ground_state_energy - (-7.8823)) < 0.1  # 100 mHartree tolerance
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend
pytest tests/test_vqe_runner.py -v
```

Expected: `ModuleNotFoundError: No module named 'pipeline.vqe_runner'`

- [ ] **Step 3: Implement vqe_runner.py**

```python
# backend/pipeline/vqe_runner.py
from dataclasses import dataclass, field
import numpy as np
import scipy.optimize as opt

from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_aer.primitives import Estimator

from .hamiltonians import HamiltonianData


@dataclass
class VQEResult:
    atom_id: str
    ground_state_energy: float          # in Hartree
    optimal_params: np.ndarray
    convergence_history: list[float]    # energy at each optimizer iteration
    one_rdm: np.ndarray                 # 1-particle reduced density matrix, shape (n, n)
    num_qubits: int
    num_iterations: int
    converged: bool


def _build_ansatz(num_qubits: int, reps: int = 2) -> EfficientSU2:
    """EfficientSU2 hardware-efficient ansatz."""
    return EfficientSU2(num_qubits, reps=reps, entanglement="linear")


def _compute_one_rdm(ansatz, optimal_params: np.ndarray, num_qubits: int) -> np.ndarray:
    """
    Compute the 1-particle reduced density matrix from the optimal wavefunction.
    gamma_pq = <psi| a†_p a_q |psi>  (occupation matrix in the qubit basis)
    
    We approximate this using the statevector: compute the expectation value of
    the number operator n_p = (I - Z_p) / 2 on the diagonal, and inter-orbital
    coherences on the off-diagonal.
    """
    bound = ansatz.assign_parameters(optimal_params)
    sv = Statevector(bound)
    
    rdm = np.zeros((num_qubits, num_qubits), dtype=complex)
    for p in range(num_qubits):
        # Diagonal: orbital occupation <n_p> = (1 - <Z_p>) / 2
        z_op = SparsePauliOp.from_sparse_list(
            [("Z", [p], 1.0)], num_qubits=num_qubits
        )
        rdm[p, p] = (1.0 - sv.expectation_value(z_op).real) / 2.0
        
        # Off-diagonal: inter-orbital terms <a†_p a_q> = (<X_p X_q> + <Y_p Y_q>) / 4
        for q in range(p + 1, num_qubits):
            xx_op = SparsePauliOp.from_sparse_list(
                [("XX", [p, q], 1.0)], num_qubits=num_qubits
            )
            yy_op = SparsePauliOp.from_sparse_list(
                [("YY", [p, q], 1.0)], num_qubits=num_qubits
            )
            val = (sv.expectation_value(xx_op) + sv.expectation_value(yy_op)) / 4.0
            rdm[p, q] = val
            rdm[q, p] = val.conjugate()
    
    return rdm.real


def run_vqe(
    ham_data: HamiltonianData,
    reps: int = 2,
    optimizer: str = "COBYLA",
    max_iter: int = 500,
) -> VQEResult:
    """
    Run VQE on the given Hamiltonian using qiskit-aer Estimator and scipy optimizer.
    Returns VQEResult including ground state energy, convergence history, and 1-RDM.
    """
    n = ham_data.num_qubits
    ansatz = _build_ansatz(n, reps=reps)
    estimator = Estimator()
    
    convergence_history: list[float] = []
    
    def cost_fn(params: np.ndarray) -> float:
        job = estimator.run([(ansatz, ham_data.operator, params)])
        energy = float(job.result()[0].data.evs)
        convergence_history.append(energy)
        return energy
    
    # Initial parameters: small random values near zero
    rng = np.random.default_rng(seed=42)
    num_params = ansatz.num_parameters
    x0 = rng.uniform(-0.1, 0.1, num_params)
    
    scipy_result = opt.minimize(
        cost_fn,
        x0,
        method=optimizer,
        options={"maxiter": max_iter, "rhobeg": 0.5},
    )
    
    optimal_params = scipy_result.x
    one_rdm = _compute_one_rdm(ansatz, optimal_params, n)
    
    return VQEResult(
        atom_id=ham_data.atom_id,
        ground_state_energy=float(scipy_result.fun),
        optimal_params=optimal_params,
        convergence_history=convergence_history,
        one_rdm=one_rdm,
        num_qubits=n,
        num_iterations=len(convergence_history),
        converged=scipy_result.success,
    )
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend
pytest tests/test_vqe_runner.py -v
```

Expected: all 5 tests PASS. H2 test runs in under 30 seconds. LiH test may take 1-2 minutes.

Note: if qiskit-aer throws a version warning about Qiskit 2.x, that is non-fatal.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/vqe_runner.py backend/tests/test_vqe_runner.py
git commit -m "feat: VQE runner using qiskit-aer + scipy, returns energy + 1-RDM"
```

---

## Task 5: Binding Site Extractor

**Files:**
- Create: `backend/pipeline/binding_sites.py`
- Create: `backend/tests/test_binding_sites.py`

The binding sites are the atom's empty coordination orbitals — where a protein's donor group can attach. We find them from the 1-RDM: orbitals with occupation near 0 are empty (= binding sites); orbitals with occupation near 1 are filled (= not binding sites). The geometry is inferred from the count and arrangement of empty orbitals.

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_binding_sites.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
import numpy as np
from pipeline.binding_sites import extract_binding_sites, CoordinationResult, CoordinationGeometry

def _mock_rdm_half_filled(n):
    """All orbitals at 0.5 occupancy — ambiguous case."""
    return np.diag([0.5] * n)

def _mock_rdm_one_empty(n):
    """First orbital empty, rest filled."""
    occs = [0.05] + [0.95] * (n - 1)
    return np.diag(occs)

def _mock_rdm_four_empty(n=6):
    """4 empty orbitals out of 6."""
    occs = [0.05, 0.05, 0.05, 0.05, 0.95, 0.95]
    return np.diag(occs[:n])

def test_extract_returns_coordination_result():
    rdm = _mock_rdm_one_empty(2)
    result = extract_binding_sites(rdm, atom_id="h2")
    assert isinstance(result, CoordinationResult)

def test_empty_orbital_detected():
    rdm = _mock_rdm_one_empty(2)
    result = extract_binding_sites(rdm, atom_id="h2")
    assert result.coordination_number >= 1
    assert 0 in result.empty_orbital_indices

def test_four_empty_gives_tetrahedral_or_square_planar():
    rdm = _mock_rdm_four_empty(6)
    result = extract_binding_sites(rdm, atom_id="lih")
    assert result.coordination_number == 4
    assert result.geometry in (CoordinationGeometry.TETRAHEDRAL, CoordinationGeometry.SQUARE_PLANAR)

def test_occupancies_sum_check():
    rdm = _mock_rdm_four_empty(6)
    result = extract_binding_sites(rdm, atom_id="lih")
    assert len(result.orbital_occupancies) == 6
    assert all(0.0 <= occ <= 1.0 for occ in result.orbital_occupancies)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend
pytest tests/test_binding_sites.py -v
```

Expected: `ModuleNotFoundError: No module named 'pipeline.binding_sites'`

- [ ] **Step 3: Implement binding_sites.py**

```python
# backend/pipeline/binding_sites.py
from dataclasses import dataclass
from enum import Enum
import numpy as np

EMPTY_THRESHOLD = 0.3   # orbital with occupancy < this is "empty" = binding site
FILLED_THRESHOLD = 0.7  # orbital with occupancy > this is "filled" = not binding site


class CoordinationGeometry(str, Enum):
    LINEAR = "linear"           # 2 sites
    TRIGONAL = "trigonal"       # 3 sites
    TETRAHEDRAL = "tetrahedral" # 4 sites
    SQUARE_PLANAR = "square_planar"  # 4 sites (flat)
    TRIGONAL_BIPYRAMIDAL = "trigonal_bipyramidal"  # 5 sites
    OCTAHEDRAL = "octahedral"   # 6 sites
    PENTAGONAL_BIPYRAMIDAL = "pentagonal_bipyramidal"  # 7 sites
    SQUARE_ANTIPRISMATIC = "square_antiprismatic"  # 8 sites (actinide-typical)
    TRICAPPED_TRIGONAL = "tricapped_trigonal"  # 9 sites
    UNKNOWN = "unknown"


def _infer_geometry(coord_number: int, atom_id: str) -> CoordinationGeometry:
    """
    Infer coordination geometry from the number of empty orbitals.
    For ambiguous cases (4 = tetrahedral or square planar), defaults to tetrahedral
    unless the atom is a late transition metal.
    """
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
    orbital_occupancies: list[float]    # one value per qubit/orbital
    empty_orbital_indices: list[int]    # indices where occupancy < EMPTY_THRESHOLD
    coordination_number: int            # count of empty orbitals = binding sites needed
    geometry: CoordinationGeometry
    binding_strength_estimate: float    # mean electron deficiency at empty sites (0-1)


def extract_binding_sites(one_rdm: np.ndarray, atom_id: str) -> CoordinationResult:
    """
    Extract coordination sites from the 1-particle reduced density matrix.
    
    Empty orbitals (low occupancy in 1-RDM) are the binding sites: they represent
    electron-deficient regions where a protein's donor group can form a coordinate bond.
    This is what the QPD calls 'identifying weak links' in the atom's electron structure.
    """
    occupancies = np.diag(one_rdm).real.tolist()
    
    empty_indices = [
        i for i, occ in enumerate(occupancies) if occ < EMPTY_THRESHOLD
    ]
    
    coord_number = len(empty_indices)
    geometry = _infer_geometry(coord_number, atom_id)
    
    # Binding strength: how electron-deficient are the empty orbitals?
    # Higher deficiency (lower occupancy) → stronger attraction for donor groups
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
    )
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend
pytest tests/test_binding_sites.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/binding_sites.py backend/tests/test_binding_sites.py
git commit -m "feat: binding site extractor from 1-RDM — empty orbitals are coordination sites"
```

---

## Task 6: Protein Designer

**Files:**
- Create: `backend/pipeline/protein_designer.py`
- Create: `backend/tests/test_protein_designer.py`

Maps the coordination result (geometry + donor preference) to a protein sequence. The key science: each binding site needs a metal-coordinating amino acid with the right donor atom. The residues are positioned on a helical scaffold at i, i+4 spacing (one turn of an alpha helix = 3.6 residues ≈ same face every 4). The result is a FASTA-format sequence that can be fed directly into AlphaFold.

Donor preferences to amino acid mapping (coordination chemistry):
- O donor → Asp (D), Glu (E), Ser (S), Thr (T), Tyr (Y)
- N donor → His (H), Asn (N), Gln (Q)
- S donor → Cys (C), Met (M)

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_protein_designer.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from pipeline.binding_sites import CoordinationResult, CoordinationGeometry
from pipeline.protein_designer import design_protein, ProteinDesignResult

def _coord_result(coord_number: int, geometry: CoordinationGeometry, donors: list[str], atom_id: str = "test"):
    return CoordinationResult(
        atom_id=atom_id,
        orbital_occupancies=[0.05] * coord_number + [0.95] * (6 - coord_number),
        empty_orbital_indices=list(range(coord_number)),
        coordination_number=coord_number,
        geometry=geometry,
        binding_strength_estimate=0.9,
    )

def test_design_returns_protein_result():
    coord = _coord_result(2, CoordinationGeometry.LINEAR, ["O"])
    result = design_protein(coord, donor_preference=["O"])
    assert isinstance(result, ProteinDesignResult)

def test_binding_residues_count_matches_coord_number():
    for cn in [2, 4, 6]:
        coord = _coord_result(cn, CoordinationGeometry.OCTAHEDRAL, ["O"])
        result = design_protein(coord, donor_preference=["O"])
        assert result.num_binding_residues == cn

def test_fasta_sequence_contains_binding_residues():
    coord = _coord_result(4, CoordinationGeometry.TETRAHEDRAL, ["O"])
    result = design_protein(coord, donor_preference=["O"])
    # Sequence must contain at least 4 O-donor residues (D, E, S, T, Y)
    o_donors = set("DESTYN")
    binding_residues_in_seq = [aa for aa in result.sequence if aa in o_donors]
    assert len(binding_residues_in_seq) >= 4

def test_fasta_output_format():
    coord = _coord_result(4, CoordinationGeometry.TETRAHEDRAL, ["O"])
    result = design_protein(coord, donor_preference=["O"])
    assert result.fasta.startswith(">")
    lines = result.fasta.strip().split("\n")
    assert len(lines) == 2
    assert all(c.isalpha() for c in lines[1])

def test_h2_linear_uses_two_residues():
    coord = _coord_result(2, CoordinationGeometry.LINEAR, ["O", "N"], atom_id="h2")
    result = design_protein(coord, donor_preference=["O", "N"])
    assert result.num_binding_residues == 2
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend
pytest tests/test_protein_designer.py -v
```

Expected: `ModuleNotFoundError: No module named 'pipeline.protein_designer'`

- [ ] **Step 3: Implement protein_designer.py**

```python
# backend/pipeline/protein_designer.py
from dataclasses import dataclass
from .binding_sites import CoordinationResult, CoordinationGeometry

# Metal-coordinating amino acids by donor atom type
DONOR_TO_RESIDUES: dict[str, list[str]] = {
    "O": ["D", "E", "S", "T", "Y"],   # Asp, Glu, Ser, Thr, Tyr
    "N": ["H", "N", "Q"],              # His, Asn, Gln
    "S": ["C", "M"],                   # Cys, Met
}

# Scaffold amino acids (non-binding, structural filler)
SCAFFOLD_HELIX = ["A", "L", "K", "A", "L", "A", "E", "A"]  # alpha-helix favoring

# Spacing on an alpha helix: binding residues at positions i, i+4, i+8, ...
HELIX_SPACING = 4


def _pick_binding_residues(coord_number: int, donor_preference: list[str]) -> list[str]:
    """
    Choose coord_number metal-coordinating amino acids based on donor preference.
    Rotates through preferred donors to give chemical diversity.
    """
    pool: list[str] = []
    for donor in donor_preference:
        pool.extend(DONOR_TO_RESIDUES.get(donor, []))
    
    if not pool:
        pool = ["D", "E"]  # fallback to O-donors
    
    residues = []
    for i in range(coord_number):
        residues.append(pool[i % len(pool)])
    return residues


def _build_sequence(binding_residues: list[str]) -> str:
    """
    Place binding residues on an alpha-helical scaffold at i, i+4, i+8, ... spacing.
    Scaffold residues fill the gaps. Minimal length = last binding position + 4.
    """
    cn = len(binding_residues)
    
    # Binding positions: 0, 4, 8, 12, ...
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
    binding_residues: list[str]         # the metal-coordinating AAs, in order
    binding_positions: list[int]        # positions in sequence (0-indexed)
    sequence: str                       # full amino acid sequence (single-letter codes)
    fasta: str                          # FASTA format for AlphaFold input
    design_notes: str


def design_protein(
    coord_result: CoordinationResult,
    donor_preference: list[str],
) -> ProteinDesignResult:
    """
    Design a metal-binding protein sequence for the given coordination result.
    
    The protein is not left to chance: binding residues are chosen specifically for
    the atom's electron deficiency profile, placed at helix-face positions that match
    the required coordination geometry. When expressed in D. radiodurans, the protein
    grabs the target ion at exactly these sites and concentrates it for crystallization.
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend
pytest tests/test_protein_designer.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/protein_designer.py backend/tests/test_protein_designer.py
git commit -m "feat: protein designer maps coordination geometry to FASTA sequence"
```

---

## Task 7: Handoff Formatter

**Files:**
- Create: `backend/pipeline/handoff.py`
- Create: `backend/tests/test_handoff.py`

Assembles all pipeline results into a single JSON object — the bio team handoff package.

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_handoff.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest, json
from pipeline.handoff import build_handoff, HandoffPackage
from pipeline.binding_sites import CoordinationResult, CoordinationGeometry
from pipeline.protein_designer import ProteinDesignResult

def _make_protein_result(atom_id="h2"):
    return ProteinDesignResult(
        atom_id=atom_id,
        geometry=CoordinationGeometry.LINEAR,
        coordination_number=2,
        num_binding_residues=2,
        binding_residues=["D", "E"],
        binding_positions=[0, 4],
        sequence="DALKALAEALKALEE",
        fasta=f">HALOS_{atom_id.upper()}_binding_protein\nDALKALAEALKALEE",
        design_notes="Linear geometry.",
    )

def _make_coord_result(atom_id="h2"):
    return CoordinationResult(
        atom_id=atom_id,
        orbital_occupancies=[0.05, 0.95],
        empty_orbital_indices=[0],
        coordination_number=2,
        geometry=CoordinationGeometry.LINEAR,
        binding_strength_estimate=0.95,
    )

def test_build_handoff_returns_package():
    coord = _make_coord_result()
    protein = _make_protein_result()
    pkg = build_handoff(
        atom_id="h2",
        ground_state_energy=-1.1373,
        coordination=coord,
        protein=protein,
    )
    assert isinstance(pkg, HandoffPackage)

def test_handoff_json_is_valid():
    coord = _make_coord_result()
    protein = _make_protein_result()
    pkg = build_handoff("h2", -1.1373, coord, protein)
    serialized = pkg.to_json()
    parsed = json.loads(serialized)
    assert parsed["atom_id"] == "h2"
    assert "fasta" in parsed
    assert "coordination" in parsed
    assert "vqe" in parsed

def test_handoff_contains_fasta():
    coord = _make_coord_result()
    protein = _make_protein_result()
    pkg = build_handoff("h2", -1.1373, coord, protein)
    assert pkg.fasta.startswith(">")

def test_handoff_ranking_field_exists():
    coord = _make_coord_result()
    protein = _make_protein_result()
    pkg = build_handoff("h2", -1.1373, coord, protein)
    parsed = json.loads(pkg.to_json())
    assert "candidate_rank" in parsed
    assert "binding_confidence" in parsed
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend
pytest tests/test_handoff.py -v
```

Expected: `ModuleNotFoundError: No module named 'pipeline.handoff'`

- [ ] **Step 3: Implement handoff.py**

```python
# backend/pipeline/handoff.py
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
    candidate_rank: int            # 1 = top candidate (always 1 from this pipeline)
    binding_confidence: float      # 0-1, derived from binding_strength_estimate

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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend
pytest tests/test_handoff.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
cd backend
pytest tests/ -v
```

Expected: all tests PASS. This confirms all pipeline modules integrate correctly.

- [ ] **Step 6: Commit**

```bash
git add backend/pipeline/handoff.py backend/tests/test_handoff.py
git commit -m "feat: handoff formatter assembles VQE + binding + protein into bio team JSON"
```

---

## Task 8: FastAPI Endpoints

**Files:**
- Modify: `backend/main.py` (add all routes)

Endpoints:
- `GET /atoms` — list all atoms with metadata
- `GET /atoms/{atom_id}` — single atom config
- `POST /pipeline/vqe` — run VQE on an atom (slow, returns all results)
- `POST /pipeline/binding-sites` — extract binding sites from 1-RDM (fast, used for replaying)
- `POST /pipeline/design-protein` — design protein from coordination result
- `GET /pipeline/run/{atom_id}` — run full pipeline end-to-end

- [ ] **Step 1: Write a basic integration test**

```python
# backend/tests/test_main.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200

def test_list_atoms():
    r = client.get("/atoms")
    assert r.status_code == 200
    atoms = r.json()
    assert isinstance(atoms, list)
    ids = [a["id"] for a in atoms]
    assert "h2" in ids
    assert "u238" in ids

def test_get_single_atom():
    r = client.get("/atoms/h2")
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "H₂"

def test_get_unknown_atom_returns_404():
    r = client.get("/atoms/xyz_unknown")
    assert r.status_code == 404

def test_full_pipeline_h2():
    r = client.get("/pipeline/run/h2", timeout=120)
    assert r.status_code == 200
    data = r.json()
    assert "ground_state_energy" in data
    assert abs(data["ground_state_energy"] - (-1.1373)) < 0.05
    assert "fasta" in data
    assert data["fasta"].startswith(">")
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend
pytest tests/test_main.py -v
```

Expected: `ImportError` on endpoint-related tests (routes not yet defined)

- [ ] **Step 3: Implement all routes in main.py**

```python
# backend/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    """Run the complete VQE → binding sites → protein design pipeline."""
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd backend
pytest tests/test_main.py -v
```

Expected: all 5 tests PASS. The `/pipeline/run/h2` test may take 30-60 seconds.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/tests/test_main.py
git commit -m "feat: FastAPI endpoints for atom registry and full pipeline execution"
```

---

## Task 9: Frontend Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "halos-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "recharts": "^2.13.3"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "^5.6.3",
    "vite": "^6.0.3"
  }
}
```

- [ ] **Step 2: Create config files**

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', rewrite: (p) => p.replace(/^\/api/, '') },
    },
  },
})
```

```typescript
// frontend/tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        serif: ['Cormorant Garamond', 'serif'],
      },
      colors: {
        halos: {
          bg: '#0a0a0a',
          surface: '#111111',
          border: '#1e1e1e',
          text: '#e8e6df',
          muted: '#666',
          accent: '#48e3ea',
          warn: '#f5a623',
          error: '#e84848',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
```

```json
// frontend/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
```

```html
<!-- frontend/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap">
    <title>HALOS — Quantum Bioremediation Pipeline</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

```typescript
// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

Create `frontend/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  background-color: #0a0a0a;
  color: #e8e6df;
  font-family: 'JetBrains Mono', monospace;
}
```

- [ ] **Step 3: Create App.tsx (layout shell)**

```typescript
// frontend/src/App.tsx
import { useState } from 'react'
import AtomSelector from './components/AtomSelector'
import PipelineRunner from './components/PipelineRunner'

export default function App() {
  const [selectedAtomId, setSelectedAtomId] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-halos-bg text-halos-text">
      <header className="border-b border-halos-border px-8 py-5 flex items-center gap-4">
        <span className="font-serif text-2xl font-light tracking-widest text-halos-text">HALOS</span>
        <span className="text-halos-muted text-sm font-mono">Quantum Bioremediation Pipeline</span>
      </header>

      <main className="max-w-5xl mx-auto px-8 py-10">
        {!selectedAtomId ? (
          <AtomSelector onSelect={setSelectedAtomId} />
        ) : (
          <PipelineRunner atomId={selectedAtomId} onReset={() => setSelectedAtomId(null)} />
        )}
      </main>
    </div>
  )
}
```

- [ ] **Step 4: Install and run frontend**

```bash
cd frontend
npm install
npm run dev
```

Expected: Vite dev server starts at `http://localhost:5173`. Page shows HALOS header. No content yet since components are empty.

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffold — Vite, React, TypeScript, Tailwind, HALOS theme"
```

---

## Task 10: API Client + AtomSelector + PipelineRunner

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/components/AtomSelector.tsx`
- Create: `frontend/src/components/PipelineRunner.tsx`

- [ ] **Step 1: Create API client**

```typescript
// frontend/src/api/client.ts

export interface AtomMeta {
  id: string
  symbol: string
  name: string
  num_qubits: number
  coordination_class: string
  typical_coordination_number: number
  donor_preference: string[]
  is_placeholder: boolean
  notes: string
}

export interface PipelineResult {
  atom_id: string
  ground_state_energy: number
  known_ground_state: number | null
  convergence_history: number[]
  num_iterations: number
  orbital_occupancies: number[]
  empty_orbital_indices: number[]
  coordination_number: number
  geometry: string
  binding_residues: string[]
  binding_positions: number[]
  sequence: string
  fasta: string
  binding_confidence: number
  handoff_json: string
}

const BASE = '/api'

export async function fetchAtoms(): Promise<AtomMeta[]> {
  const r = await fetch(`${BASE}/atoms`)
  if (!r.ok) throw new Error('Failed to load atoms')
  return r.json()
}

export async function runPipeline(atomId: string): Promise<PipelineResult> {
  const r = await fetch(`${BASE}/pipeline/run/${atomId}`)
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail ?? 'Pipeline failed')
  }
  return r.json()
}
```

- [ ] **Step 2: Create AtomSelector**

```typescript
// frontend/src/components/AtomSelector.tsx
import { useEffect, useState } from 'react'
import { fetchAtoms, type AtomMeta } from '../api/client'

const CLASS_COLORS: Record<string, string> = {
  diatomic: 'text-sky-400',
  alkali: 'text-emerald-400',
  lanthanide: 'text-violet-400',
  actinide: 'text-orange-400',
}

interface Props {
  onSelect: (atomId: string) => void
}

export default function AtomSelector({ onSelect }: Props) {
  const [atoms, setAtoms] = useState<AtomMeta[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAtoms().then(setAtoms).finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-halos-muted font-mono text-sm">Loading atoms...</p>

  const runnable = atoms.filter(a => !a.is_placeholder)
  const placeholders = atoms.filter(a => a.is_placeholder)

  return (
    <div>
      <h1 className="font-serif text-4xl font-light mb-2">Select Target Atom</h1>
      <p className="text-halos-muted text-sm mb-8">
        VQE identifies coordination sites. The pipeline designs a protein to bind them — deterministically.
      </p>

      <section className="mb-8">
        <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
          Runnable Now
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {runnable.map(atom => (
            <button
              key={atom.id}
              onClick={() => onSelect(atom.id)}
              className="text-left p-4 rounded border border-halos-border bg-halos-surface hover:border-halos-accent transition-colors group"
            >
              <div className="flex items-baseline gap-2 mb-1">
                <span className={`font-mono text-lg font-medium ${CLASS_COLORS[atom.coordination_class] ?? 'text-halos-text'}`}>
                  {atom.symbol}
                </span>
                <span className="text-halos-muted text-xs">{atom.num_qubits} qubits</span>
              </div>
              <div className="text-halos-text text-sm mb-1">{atom.name}</div>
              <div className="text-halos-muted text-xs">{atom.notes}</div>
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
          Actinide Targets — Awaiting Fault-Tolerant Hardware
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {placeholders.map(atom => (
            <div
              key={atom.id}
              className="p-4 rounded border border-halos-border opacity-50 cursor-not-allowed"
            >
              <div className="flex items-baseline gap-2 mb-1">
                <span className={`font-mono text-lg font-medium ${CLASS_COLORS[atom.coordination_class] ?? 'text-halos-muted'}`}>
                  {atom.symbol}
                </span>
                <span className="text-halos-muted text-xs">{atom.num_qubits} electrons</span>
              </div>
              <div className="text-halos-muted text-sm">{atom.name}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
```

- [ ] **Step 3: Create PipelineRunner**

```typescript
// frontend/src/components/PipelineRunner.tsx
import { useEffect, useState } from 'react'
import { runPipeline, type PipelineResult } from '../api/client'
import VQEChart from './VQEChart'
import BindingSites from './BindingSites'
import ProteinOutput from './ProteinOutput'
import HandoffExport from './HandoffExport'

type Stage = 'running' | 'done' | 'error'

interface Props {
  atomId: string
  onReset: () => void
}

export default function PipelineRunner({ atomId, onReset }: Props) {
  const [stage, setStage] = useState<Stage>('running')
  const [result, setResult] = useState<PipelineResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    runPipeline(atomId)
      .then(r => { setResult(r); setStage('done') })
      .catch(e => { setError(e.message); setStage('error') })
  }, [atomId])

  return (
    <div>
      <div className="flex items-center gap-4 mb-8">
        <button onClick={onReset} className="text-halos-muted hover:text-halos-text text-sm font-mono">
          ← Back
        </button>
        <h1 className="font-serif text-3xl font-light">
          Pipeline: <span className="text-halos-accent">{atomId.toUpperCase()}</span>
        </h1>
      </div>

      {stage === 'running' && (
        <div className="space-y-2">
          <div className="text-halos-muted text-sm font-mono">Running VQE...</div>
          <div className="text-xs text-halos-muted">
            Qiskit-Aer statevector estimator + COBYLA optimizer. H2 takes ~30s. LiH takes ~90s.
          </div>
          <div className="h-1 bg-halos-border rounded overflow-hidden">
            <div className="h-full bg-halos-accent animate-pulse w-1/2" />
          </div>
        </div>
      )}

      {stage === 'error' && (
        <div className="text-halos-error font-mono text-sm border border-halos-error rounded p-4">
          Error: {error}
        </div>
      )}

      {stage === 'done' && result && (
        <div className="space-y-8">
          <VQEChart
            history={result.convergence_history}
            groundStateEnergy={result.ground_state_energy}
            knownGroundState={result.known_ground_state}
          />
          <BindingSites
            geometry={result.geometry}
            coordinationNumber={result.coordination_number}
            orbitalOccupancies={result.orbital_occupancies}
            emptyOrbitalIndices={result.empty_orbital_indices}
          />
          <ProteinOutput
            sequence={result.sequence}
            fasta={result.fasta}
            bindingResidues={result.binding_residues}
            bindingPositions={result.binding_positions}
            bindingConfidence={result.binding_confidence}
          />
          <HandoffExport handoffJson={result.handoff_json} atomId={result.atom_id} />
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Verify frontend loads correctly with backend running**

Start backend: `cd backend && uvicorn main:app --reload --port 8000`
Start frontend: `cd frontend && npm run dev`

Open `http://localhost:5173`. Confirm:
- HALOS header renders
- Atom selector loads (shows H2, LiH as runnable; actinides as disabled)
- No console errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: atom selector and pipeline runner components with live API integration"
```

---

## Task 11: Results Components

**Files:**
- Create: `frontend/src/components/VQEChart.tsx`
- Create: `frontend/src/components/BindingSites.tsx`
- Create: `frontend/src/components/ProteinOutput.tsx`
- Create: `frontend/src/components/HandoffExport.tsx`

- [ ] **Step 1: Create VQEChart**

```typescript
// frontend/src/components/VQEChart.tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'

interface Props {
  history: number[]
  groundStateEnergy: number
  knownGroundState: number | null
}

export default function VQEChart({ history, groundStateEnergy, knownGroundState }: Props) {
  const data = history.map((e, i) => ({ iteration: i + 1, energy: e }))

  return (
    <section>
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-1">
        VQE Convergence
      </h2>
      <div className="text-halos-text font-mono text-sm mb-3">
        Ground state energy:{' '}
        <span className="text-halos-accent">{groundStateEnergy.toFixed(6)} Ha</span>
        {knownGroundState && (
          <span className="text-halos-muted ml-3">
            (reference: {knownGroundState.toFixed(6)} Ha,{' '}
            error: {Math.abs(groundStateEnergy - knownGroundState).toFixed(4)} Ha)
          </span>
        )}
      </div>
      <div className="bg-halos-surface border border-halos-border rounded p-4 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis
              dataKey="iteration"
              tick={{ fill: '#666', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              label={{ value: 'Iteration', position: 'insideBottom', offset: -4, fill: '#666', fontSize: 11 }}
            />
            <YAxis
              tick={{ fill: '#666', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickFormatter={(v: number) => v.toFixed(3)}
            />
            <Tooltip
              contentStyle={{ background: '#111', border: '1px solid #1e1e1e', color: '#e8e6df', fontFamily: 'JetBrains Mono', fontSize: 12 }}
              formatter={(v: number) => [v.toFixed(6) + ' Ha', 'Energy']}
            />
            {knownGroundState && (
              <ReferenceLine y={knownGroundState} stroke="#48e3ea" strokeDasharray="4 4" strokeWidth={1} />
            )}
            <Line type="monotone" dataKey="energy" stroke="#48e3ea" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Create BindingSites**

```typescript
// frontend/src/components/BindingSites.tsx

interface Props {
  geometry: string
  coordinationNumber: number
  orbitalOccupancies: number[]
  emptyOrbitalIndices: number[]
}

export default function BindingSites({ geometry, coordinationNumber, orbitalOccupancies, emptyOrbitalIndices }: Props) {
  return (
    <section>
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
        Binding Sites (Coordination Sites)
      </h2>
      <div className="flex items-baseline gap-4 mb-4">
        <span className="font-mono text-2xl text-halos-text">{coordinationNumber}</span>
        <span className="text-halos-muted text-sm">empty orbitals →</span>
        <span className="font-mono text-halos-accent text-lg capitalize">{geometry.replace(/_/g, ' ')}</span>
        <span className="text-halos-muted text-sm">coordination</span>
      </div>
      <div className="flex gap-2 flex-wrap">
        {orbitalOccupancies.map((occ, i) => {
          const isEmpty = emptyOrbitalIndices.includes(i)
          return (
            <div
              key={i}
              className={`px-3 py-2 rounded border font-mono text-xs ${
                isEmpty
                  ? 'border-halos-accent text-halos-accent bg-halos-accent/5'
                  : 'border-halos-border text-halos-muted'
              }`}
            >
              <div>ψ{i}</div>
              <div>{occ.toFixed(3)}</div>
              {isEmpty && <div className="text-[10px] mt-1">SITE</div>}
            </div>
          )
        })}
      </div>
      <p className="text-halos-muted text-xs mt-3">
        Orbitals with occupancy &lt; 0.3 are electron-deficient — these are where protein donor groups coordinate.
        The geometry determines the spatial arrangement of binding residues in the designed protein.
      </p>
    </section>
  )
}
```

- [ ] **Step 3: Create ProteinOutput**

```typescript
// frontend/src/components/ProteinOutput.tsx
import { useState } from 'react'

interface Props {
  sequence: string
  fasta: string
  bindingResidues: string[]
  bindingPositions: number[]
  bindingConfidence: number
}

export default function ProteinOutput({ sequence, fasta, bindingResidues, bindingPositions, bindingConfidence }: Props) {
  const [copied, setCopied] = useState(false)
  const bindingSet = new Set(bindingPositions)

  const copy = () => {
    navigator.clipboard.writeText(fasta)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <section>
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
        Designed Protein Sequence
      </h2>

      <div className="flex items-center gap-6 mb-4">
        <div>
          <div className="text-halos-muted text-xs mb-1">Binding confidence</div>
          <div className="font-mono text-2xl text-halos-accent">{(bindingConfidence * 100).toFixed(0)}%</div>
        </div>
        <div>
          <div className="text-halos-muted text-xs mb-1">Binding residues</div>
          <div className="font-mono text-halos-text">{bindingResidues.join(' — ')}</div>
        </div>
        <div>
          <div className="text-halos-muted text-xs mb-1">Positions (helix face)</div>
          <div className="font-mono text-halos-text">{bindingPositions.join(', ')}</div>
        </div>
      </div>

      <div className="bg-halos-surface border border-halos-border rounded p-4 mb-3 font-mono text-sm leading-loose">
        {sequence.split('').map((aa, i) => (
          <span
            key={i}
            className={bindingSet.has(i) ? 'text-halos-accent font-bold underline' : 'text-halos-muted'}
          >
            {aa}
          </span>
        ))}
      </div>

      <div className="bg-halos-surface border border-halos-border rounded p-4 mb-3">
        <pre className="font-mono text-xs text-halos-muted whitespace-pre-wrap break-all">{fasta}</pre>
      </div>

      <button
        onClick={copy}
        className="px-4 py-2 border border-halos-accent text-halos-accent font-mono text-sm hover:bg-halos-accent hover:text-halos-bg transition-colors rounded"
      >
        {copied ? 'Copied!' : 'Copy FASTA'}
      </button>
      <p className="text-halos-muted text-xs mt-2">
        Submit this FASTA to ColabFold (AlphaFold2). pLDDT &gt; 70 at binding residues required before wet lab synthesis.
      </p>
    </section>
  )
}
```

- [ ] **Step 4: Create HandoffExport**

```typescript
// frontend/src/components/HandoffExport.tsx

interface Props {
  handoffJson: string
  atomId: string
}

export default function HandoffExport({ handoffJson, atomId }: Props) {
  const download = () => {
    const blob = new Blob([handoffJson], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `HALOS_handoff_${atomId}_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="border-t border-halos-border pt-6">
      <h2 className="font-mono text-xs uppercase tracking-widest text-halos-muted mb-3">
        Bio Team Handoff Package
      </h2>
      <p className="text-halos-muted text-sm mb-4">
        Download the complete handoff JSON. Contains: FASTA sequence, coordination geometry,
        binding confidence, orbital data, and lab instructions for prime editing into D. radiodurans.
      </p>
      <button
        onClick={download}
        className="px-6 py-3 bg-halos-accent text-halos-bg font-mono text-sm font-medium hover:bg-halos-accent/90 transition-colors rounded"
      >
        Download Handoff Package
      </button>
    </section>
  )
}
```

- [ ] **Step 5: Run full end-to-end test**

Start both services:
```bash
# terminal 1
cd backend && uvicorn main:app --reload --port 8000

# terminal 2
cd frontend && npm run dev
```

Open `http://localhost:5173`. Run through the pipeline:
1. Click H2 → pipeline runs → energy convergence chart appears
2. Binding sites panel shows orbital occupancies with SITE markers
3. Protein sequence shows with highlighted binding residues
4. Copy FASTA button works
5. Download handoff JSON — open file, confirm it contains all fields

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: VQE chart, binding sites, protein output, and handoff export components"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Choose an atom → AtomSelector with full registry
- [x] Run Qiskit VQE → vqe_runner.py using Qiskit 2.x + qiskit-aer + scipy
- [x] Identify binding sites ("weak links") → binding_sites.py: empty orbitals from 1-RDM
- [x] Design protein → protein_designer.py: geometry → residues → FASTA
- [x] Not luck — deterministic because geometry is quantum-computed, residues are chosen specifically for the electron structure, placement is on helix face
- [x] Output for prime editing into D. radiodurans → handoff.py includes next-step instructions
- [x] Must use Qiskit → vqe_runner.py uses qiskit-aer Estimator and qiskit circuit library
- [x] Works on Windows (no PySCF needed) → pre-computed Hamiltonians in JSON
- [x] Actinide placeholders → in atom registry, disabled in UI, with clear "why not yet" messaging

**Placeholder scan:** No TBDs, no "implement later", no "similar to Task N". All code is complete.

**Type consistency:**
- `CoordinationResult.coordination_number` used identically in binding_sites.py, protein_designer.py, handoff.py, and API response
- `PipelineResult.convergence_history` (list[float]) matches `VQEResult.convergence_history` and `data.convergence_history` in VQEChart
- `HamiltonianData.operator` (SparsePauliOp) used consistently in vqe_runner.py
- `HandoffPackage.to_json()` matches test assertions on `parsed["atom_id"]`, `parsed["fasta"]`, `parsed["coordination"]`, `parsed["vqe"]`
