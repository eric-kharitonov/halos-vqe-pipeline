import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from pipeline import folding
from pipeline.folding import _extract_plddt, fold_sequence, FoldingError, InvalidSequenceError

# Minimal PDB snippet: two residues, CA B-factor column (cols 61-66) holds pLDDT.
_PDB = (
    "ATOM      1  N   MET A   1      11.104  13.207  10.567  1.00 88.50           N\n"
    "ATOM      2  CA  MET A   1      12.560  13.207  10.567  1.00 88.50           C\n"
    "ATOM      3  N   ALA A   2      13.100  14.500  11.000  1.00 42.10           N\n"
    "ATOM      4  CA  ALA A   2      14.000  15.000  11.500  1.00 42.10           C\n"
)


def test_extract_plddt_reads_ca_bfactors():
    plddt = _extract_plddt(_PDB)
    assert plddt == [88.50, 42.10]


def test_fold_rejects_nonstandard_residues():
    # Bad residues raise InvalidSequenceError (a FoldingError subclass) -> maps to HTTP 400.
    with pytest.raises(InvalidSequenceError):
        fold_sequence("DEZX1")  # Z, X, 1 are not standard amino acids


def test_fold_rejects_empty():
    with pytest.raises(InvalidSequenceError):
        fold_sequence("   ")


def test_fold_rejects_too_long():
    with pytest.raises(InvalidSequenceError):
        fold_sequence("A" * 401)


# Two-residue PDB whose CA B-factors are on the 0-1 scale the esmatlas endpoint returns.
_PDB_LOW = _PDB.replace("88.50", "00.88").replace("42.10", "00.42")


def test_plddt_is_rescaled_from_0_1_to_0_100(monkeypatch, tmp_path):
    # Redirect the cache to a temp dir: fold_sequence still *writes* a cache entry even with
    # use_cache=False, so without this the test would pollute the real data/folds/ with fake data.
    monkeypatch.setattr(folding, "_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(folding, "_call_esmfold", lambda seq, timeout: _PDB_LOW)
    result = fold_sequence("DE", use_cache=False)
    # 0.88 / 0.42 must be lifted onto the standard 0-100 pLDDT scale.
    assert result.per_residue_plddt == [88.0, 42.0]
    assert result.mean_plddt == 65.0


def test_successful_fold_is_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(folding, "_CACHE_DIR", str(tmp_path))
    calls = {"n": 0}

    def fake_call(seq, timeout):
        calls["n"] += 1
        return _PDB

    monkeypatch.setattr(folding, "_call_esmfold", fake_call)

    first = fold_sequence("DEDE")
    assert calls["n"] == 1

    # A second fold of the same sequence must hit the disk cache, not the network.
    def boom(seq, timeout):
        raise AssertionError("network should not be called when the fold is cached")

    monkeypatch.setattr(folding, "_call_esmfold", boom)
    second = fold_sequence("DEDE")
    assert second.per_residue_plddt == first.per_residue_plddt
    assert calls["n"] == 1


@pytest.mark.network
def test_fold_live_esmfold():
    """Live ESMFold call. Skips (does not fail) if the service is unreachable."""
    seq = "ALKALAEADEALKALAEAALKALAEAALKALAEA"  # 34-aa helix-ish construct
    try:
        result = fold_sequence(seq, timeout=120)
    except FoldingError as e:
        pytest.skip(f"ESMFold unavailable: {e}")
    assert result.n_residues == len(seq)
    assert 0 <= result.mean_plddt <= 100
    assert "ATOM" in result.pdb
