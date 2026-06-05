# HALOS — Quantum Bioremediation Pipeline Tool

Pick a target atom → run **Qiskit VQE** to find its ground state and identify the
electron-deficient "weak links" (empty coordination orbitals) → **design a protein**
with the right metal-coordinating residues, in the right geometry, to bind those sites →
export a bio-team handoff package for prime-editing into *D. radiodurans*.

The binding is **by design, not by luck**: the coordinating residues are chosen from the
quantum-computed orbital occupancies and placed on an α-helix face matching the
coordination geometry. Same input → same output, every time.

TKS Moonshot — Eric Kharitonov, 2025-26.

---

## The pipeline (one atom, end to end)

```
atom  →  Hamiltonian  →  VQE (Qiskit)  →  1-RDM occupancies  →  binding sites
                                                                      │
            bio-team handoff JSON  ←  protein (FASTA)  ←  coordination geometry
```

1. **VQE** (`backend/pipeline/vqe_runner.py`) — `StatevectorEstimator` + `EfficientSU2`
   ansatz + COBYLA. Reaches chemical accuracy on H₂ (−1.1373 Ha) and LiH (−7.8631 Ha).
2. **Binding sites** (`binding_sites.py`) — orbitals with occupancy < 0.3 are empty =
   coordination sites. Their count picks the geometry (linear, tetrahedral, …).
3. **Protein design** (`protein_designer.py`) — maps donor preference → residues
   (O→D/E/S/T/Y, N→H/N/Q, S→C/M), placed at helix positions 0, 4, 8, … → FASTA.
4. **Handoff** (`handoff.py`) — bundles VQE energy, geometry, sequence, confidence, and
   next-step lab instructions into one JSON.

## Atoms

| Runnable now | Awaiting fault-tolerant hardware (placeholders) |
|---|---|
| H₂ (4 qubits), LiH (6 qubits) | Ce³⁺, La³⁺ proxies · U, Pu, Np, Am actinide targets |

The actinide configs are registered and the pipeline is parameterized for them — only the
Hamiltonian input changes when hardware is ready. The code does not change.

---

## Run it

**Prerequisites:** Python 3.13 with `qiskit` + `qiskit-aer` installed globally; Node 20+.

### Backend
```bash
cd backend
pip install -r requirements.txt          # fastapi, uvicorn, pydantic, pytest, httpx
python -m uvicorn main:app --port 8000
```
- `GET /atoms` — list all atoms
- `GET /pipeline/run/{atom_id}` — run the full pipeline (e.g. `/pipeline/run/h2`)

### Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxies /api → :8000)
```
Open the page, click H₂ or LiH, watch VQE converge, inspect the binding sites and designed
protein, and download the handoff package.

### Tests
```bash
cd backend
python -m pytest tests/ -v      # 35 tests; the VQE tests take ~2 min
```

---

## Regenerating the Hamiltonians

PySCF has no Windows wheel, so molecular Hamiltonians are generated **offline** with
PennyLane's pure-Python differentiable Hartree-Fock backend and shipped as JSON under
`data/hamiltonians/`. Each is exact-diagonalized and verified against Qiskit before use.

```bash
pip install pennylane
python backend/generate_hamiltonians.py
```

This is the only place PennyLane is used — the runtime VQE pipeline is pure Qiskit.

---

## What's still notional (be honest about scope)

This is a **proof-of-concept simulator**, not a validated drug-design tool:

- VQE runs on small molecules (H₂, LiH); actinides need fault-tolerant hardware.
- The binding-site → geometry → residue mapping is a principled heuristic, not a docking
  or folding calculation. The FASTA output is meant to be validated downstream with
  AlphaFold2 / RFdiffusion before any wet-lab work (see the handoff JSON's `next_step`).
- The 1-RDM off-diagonal terms use an approximation; only the diagonal occupancies (which
  are exact) drive the binding-site logic.
