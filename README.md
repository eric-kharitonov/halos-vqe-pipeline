# HALOS — Quantum Bioremediation Pipeline Tool

Pick a target atom → run **Qiskit VQE** to find its ground state and identify the
electron-deficient "weak links" (empty coordination orbitals) → **design a protein**
with the right metal-coordinating residues, in the right geometry, to bind those sites →
export a bio-team handoff package for prime-editing into *D. radiodurans*.

The **design is deterministic, not random**: the coordinating residues are chosen from the
binding map's orbital occupancies and placed on an α-helix face matching the coordination
geometry, so the same target gives the same protein every time. "Deterministic" describes the
*design procedure* — whether the resulting protein actually binds the metal and crystallizes it
is a wet-lab question this tool does not claim to answer.

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
4. **QAOA search** (`protein_search.py`, optional) — instead of placing residues
   deterministically, *searches* a small peptide space with the Quantum Approximate
   Optimization Algorithm (`QAOAAnsatz` over a diagonal cost Hamiltonian). Brute-force
   validated to reach the true optimum on the 16/64-candidate spaces. Endpoint
   `GET /pipeline/qaoa-search?binding_strength=…&n_residues=…`.
5. **Structure prediction** (`folding.py`) — folds the designed construct with **ESMFold**
   (real, no MSA) and returns mean + per-residue pLDDT. Successful folds are cached to
   `data/folds/` (genuine ESMFold output) so the demo is reliable when the public endpoint
   is busy. Endpoint `GET /pipeline/fold?sequence=…`. pLDDT is *fold confidence*, not
   binding or in-cell function.
6. **Prime-edit design** (`prime_editing.py`) — codon-optimizes the protein's gene for
   *D. radiodurans* (high-GC) and designs a simplified pegRNA (spacer/PAM/PBS/RTT) against a
   representative neutral locus, returning the before → after DNA. Endpoint
   `GET /pipeline/prime-edit?protein=…`. This is the *design of the edit*, not a prediction
   that the cell survives or expresses it.
7. **Handoff** (`handoff.py`) — bundles the binding map (with its `source`: VQE energy or
   literature estimate), geometry, sequence, the electron-deficiency measure, the QAOA
   recommendation, the fold, and next-step lab instructions into one JSON.

## Targets (tiers)

Each target runs as far down the pipeline as today's compute allows:

| Tier | Targets | What runs |
|---|---|---|
| `REAL VQE` | H₂ | real VQE → binding → design → QAOA → fold |
| `PRECOMPUTED` | LiH | verified Hamiltonian → full pipeline → fold |
| `TOY` | T (³H) | toy 2-qubit VQE → downstream → fold |
| `PROXY` | Cs⁺ (Cs-137), Sr²⁺ (Sr-90) | **no VQE** — design + fold from literature coordination (marked `source=literature`) |
| `LOCKED` | U, Pu, Np, Am | blocked — needs fault-tolerant hardware |

The frontend is a single-page editorial pipeline: a periodic-table target grid with tier
badges, then every stage stacked vertically with honesty labels and a live event log.

## Repo layout

| Path | What it is |
|---|---|
| `backend/` | FastAPI app + the real pipeline (VQE, QAOA, folding, prime-edit, handoff) |
| `frontend/` | The live React/Vite app — **this is the real UI** (`npm run dev`) |
| `data/` | Committed Hamiltonians (`hamiltonians/`) and cached ESMFold structures (`folds/`) |
| `docs/` | PID / BPD / QPD project documents |
| `index.html` + `assets/` (root) | The original Perplexity-exported **design mockup** — a static reference only, not wired to the backend. Superseded by `frontend/`; kept for visual provenance. |

---

## Run it

**Prerequisites:** Python 3.13 with `qiskit` installed globally (the runtime uses Qiskit's
`StatevectorEstimator` — **not** `qiskit-aer`, which can't execute the `EfficientSU2` ansatz
directly); Node 20+.

### Backend
```bash
cd backend
pip install -r requirements.txt          # fastapi, uvicorn, pydantic, numpy, scipy, pytest, httpx
pip install qiskit                        # not pinned in requirements; installed globally
python -m uvicorn main:app --port 8000
```
- `GET /atoms` — list all targets (with tier/badge metadata)
- `GET /pipeline/run/{atom_id}` — run the pipeline as far as the tier allows (e.g. `/pipeline/run/h2`, `/pipeline/run/cs`)
- `GET /pipeline/qaoa-search?...` — QAOA peptide search
- `GET /pipeline/fold?sequence=...` — ESMFold structure prediction (400 on bad input, 502 if the service is down)
- `GET /pipeline/prime-edit?protein=...` — prime-edit / pegRNA design (400 on a non-standard sequence)

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
python -m pytest -m "not network"   # 71 offline tests (~4 min; the VQE/QAOA tests dominate)
python -m pytest tests/ -v          # +1 live ESMFold test (skips if the service is down)
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
- The QAOA search uses a transparent surrogate cost (donor strength vs. site deficiency +
  adjacency penalty), not an ab-initio binding energy. It's a faithful demonstration of
  the *algorithm* on a real combinatorial encoding, not a quantitative binding predictor.
- The 1-RDM off-diagonal terms use an approximation; only the diagonal occupancies (which
  are exact) drive the binding-site logic.
