"""Pre-cache the deterministic VQE pipeline results so the live demo is instant.

The real/precomputed/toy VQE targets (H2, LiH, T) run a seeded VQE (seed=42), so their
full pipeline output is deterministic. On a CPU-throttled free host a fresh run can take
minutes; this runs each once and writes data/pipeline/<id>.json (the genuine computed
result, same idea as precache_folds.py) so the /api/pipeline/run endpoint serves it
instantly afterwards. The proxy targets (Cs/Sr) skip VQE and are already instant.

Re-run whenever the VQE/design logic changes:

    python precache_pipeline.py
"""
import sys

# Windows consoles default to cp1252, which can't encode the symbols (H₂, Cs⁺ …).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pipeline.atoms import list_atoms
from main import run_full_pipeline, _pipeline_cache_path


def main() -> None:
    for atom in list_atoms():
        if not atom.runs_vqe:
            continue
        print(f"{atom.symbol:>6}  running VQE pipeline (this is the slow part) ...", flush=True)
        result = run_full_pipeline(atom.id)   # computes + writes data/pipeline/<id>.json
        print(f"{atom.symbol:>6}  cached -> {_pipeline_cache_path(atom.id)}  "
              f"E={result['ground_state_energy']:.5f} Ha  iters={result['num_iterations']}")


if __name__ == "__main__":
    main()
