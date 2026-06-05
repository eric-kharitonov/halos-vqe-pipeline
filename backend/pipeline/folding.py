"""
Protein structure prediction via ESMFold (the one genuinely-simulatable bio step).

The QC pipeline produces a sequence; the *first* thing the bio team does (BPD Build 1)
is predict its 3D fold and check confidence (pLDDT) before any wet-lab work. ESMFold
(Meta) folds a single sequence with no MSA, exposed as a public REST endpoint — so we can
wire it directly into the pipeline.

Honest scope: ESMFold predicts STRUCTURE, not metal-binding function or in-cell viability.
A high pLDDT means "this sequence folds into a confident shape", not "this protein works".
Everything past folding (binding assay, prime editing, biomineralization) is wet-lab and is
NOT simulated.
"""
import hashlib
import json
import os
import ssl
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict

ESMFOLD_URL = "https://api.esmatlas.com/foldSequence/v1/pdb/"
VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")

# The public ESMFold endpoint is free but intermittently overloaded (504s / timeouts).
# We retry transient failures and cache every successful fold to disk, so a fold that
# has ever succeeded is served instantly and reliably afterwards. Cached data is real
# ESMFold output, not a substitute.
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "folds")
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 3


class FoldingError(RuntimeError):
    """ESMFold could not fold the sequence (bad input or service unavailable)."""


class InvalidSequenceError(FoldingError):
    """The input sequence itself is invalid (empty, non-standard residues, too long).

    A subclass of FoldingError so existing callers still catch it, but distinct so the API
    can return 400 (client error) instead of 502 (upstream service unavailable).
    """


@dataclass
class FoldResult:
    sequence: str
    pdb: str                       # full PDB text (B-factor column holds pLDDT)
    mean_plddt: float              # 0-100; >70 = confident
    per_residue_plddt: list[float]
    n_residues: int
    source: str


def _extract_plddt(pdb: str) -> list[float]:
    """ESMFold writes the per-residue pLDDT into the B-factor column of each CA atom."""
    values = []
    for line in pdb.splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            try:
                values.append(float(line[60:66]))
            except ValueError:
                continue
    return values


def _cache_path(seq: str) -> str:
    return os.path.join(_CACHE_DIR, hashlib.sha1(seq.encode()).hexdigest() + ".json")


def _load_cache(seq: str) -> FoldResult | None:
    path = _cache_path(seq)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return FoldResult(**json.load(f))
        except (OSError, TypeError, ValueError):
            return None
    return None


def _save_cache(result: FoldResult) -> None:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    try:
        with open(_cache_path(result.sequence), "w") as f:
            json.dump(asdict(result), f)
    except OSError:
        pass


def _call_esmfold(seq: str, timeout: int) -> str:
    # api.esmatlas.com has presented an untrusted certificate at times; this is a public
    # read-only folding service, so we proceed without certificate verification.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    request = urllib.request.Request(ESMFOLD_URL, data=seq.encode(), method="POST")
    with urllib.request.urlopen(request, timeout=timeout, context=ctx) as response:
        return response.read().decode()


def fold_sequence(sequence: str, timeout: int = 120, use_cache: bool = True) -> FoldResult:
    """Fold a single amino-acid sequence with ESMFold. Raises FoldingError on failure.

    Successful folds are cached to disk and reused (cached output is genuine ESMFold data).
    Transient gateway/timeout errors are retried before giving up.
    """
    seq = "".join(sequence.split()).upper()
    if not seq:
        raise InvalidSequenceError("Empty sequence.")
    bad = set(seq) - VALID_AA
    if bad:
        raise InvalidSequenceError(f"Sequence has non-standard residues: {sorted(bad)}")
    if len(seq) > 400:
        raise InvalidSequenceError("Sequence too long for the public ESMFold endpoint (>400).")

    if use_cache:
        cached = _load_cache(seq)
        if cached is not None:
            return cached

    last_error = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            pdb = _call_esmfold(seq, timeout)
            if "ATOM" not in pdb:
                raise FoldingError("ESMFold returned no structure (service may be busy).")
            plddt = _extract_plddt(pdb)
            # The esmatlas endpoint returns pLDDT on a 0-1 scale; normalise to the
            # standard 0-100 scale (where >70 = confident) if needed.
            if plddt and max(plddt) <= 1.0:
                plddt = [round(v * 100, 2) for v in plddt]
            mean_plddt = round(sum(plddt) / len(plddt), 1) if plddt else 0.0
            result = FoldResult(
                sequence=seq,
                pdb=pdb,
                mean_plddt=mean_plddt,
                per_residue_plddt=plddt,
                n_residues=len(plddt),
                source="ESMFold v1 (api.esmatlas.com)",
            )
            _save_cache(result)
            return result
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_BACKOFF_SECONDS * (attempt + 1))

    raise FoldingError(f"ESMFold service unavailable after {_MAX_ATTEMPTS} attempts: {last_error}")
