"""Pre-cache ESMFold structures for the downstream-only proxy targets.

The PROXY-tier targets (Cs⁺, Sr²⁺) skip VQE and design their construct from literature
coordination chemistry. Their constructs are not produced by a quantum run, so they are
not folded during normal verification — which means the *first* user to fold one waits on
a live (and intermittently 504-ing) ESMFold call. This script folds those constructs once
so they are served instantly from the disk cache afterwards (cached data is genuine ESMFold
output). Run it whenever the proxy set or the construct builder changes.

    python precache_folds.py
"""
import sys

# Windows consoles default to cp1252, which can't encode the proxy symbols (Cs⁺, Sr²⁺).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pipeline.atoms import list_atoms
from pipeline.binding_sites import estimate_coordination_from_literature
from pipeline.protein_designer import design_protein, build_foldable_construct
from pipeline.folding import fold_sequence, FoldingError


def main() -> None:
    proxies = [a for a in list_atoms() if a.is_downstream_only]
    seen: dict[str, str] = {}   # construct sequence -> first atom that produced it

    for atom in proxies:
        coord = estimate_coordination_from_literature(atom.id, atom.typical_coordination_number)
        protein = design_protein(coord, donor_preference=atom.donor_preference)
        construct, _ = build_foldable_construct(protein.binding_residues)

        if construct in seen:
            print(f"{atom.symbol:>5}  same construct as {seen[construct]} — already handled")
            continue

        print(f"{atom.symbol:>5}  folding {len(construct)}-residue construct ...", flush=True)
        try:
            result = fold_sequence(construct)
        except FoldingError as exc:
            print(f"{atom.symbol:>5}  FAILED: {exc}")
            continue
        seen[construct] = atom.symbol   # only mark handled once it is genuinely cached
        print(f"{atom.symbol:>5}  cached · mean pLDDT {result.mean_plddt} · {result.n_residues} residues")


if __name__ == "__main__":
    main()
