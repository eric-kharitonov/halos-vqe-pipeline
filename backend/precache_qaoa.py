"""Pre-cache the QAOA search results so the live demo's "RUN QAOA SEARCH" is instant.

The UI fires the QAOA search for every non-locked target with deterministic params it
reads off the pipeline result (binding_confidence, min(coord, 3), atom_id, geometry). On a
throttled free host the search takes ~130s — past the frontend timeout. This runs each one
once and writes data/qaoa/<hash>.json so the endpoint serves it instantly afterwards.

Run after precache_pipeline.py (it reads the cached pipeline results):

    python precache_pipeline.py
    python precache_qaoa.py
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pipeline.atoms import list_atoms
from main import run_full_pipeline, qaoa_search, _qaoa_cache_path


def main() -> None:
    for atom in list_atoms():
        if atom.is_locked:
            continue
        run = run_full_pipeline(atom.id)            # cached (VQE) or instant (proxy literature)
        bs = run["binding_confidence"]
        nr = min(run["coordination_number"], 3)     # exactly what the UI sends
        geom = run["geometry"]
        print(f"{atom.symbol:>6}  QAOA  n_residues={nr}  binding_strength={bs} ...", flush=True)
        qaoa_search(binding_strength=bs, n_residues=nr, atom_id=atom.id, geometry=geom)
        print(f"{atom.symbol:>6}  cached -> {_qaoa_cache_path(bs, nr, atom.id, geom)}")


if __name__ == "__main__":
    main()
