import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from pipeline.folding import _extract_plddt, fold_sequence, FoldingError

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
    with pytest.raises(FoldingError):
        fold_sequence("DEZX1")  # Z, X, 1 are not standard amino acids


def test_fold_rejects_empty():
    with pytest.raises(FoldingError):
        fold_sequence("   ")


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
