import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
import numpy as np
from pipeline.binding_sites import extract_binding_sites, CoordinationResult, CoordinationGeometry

def _mock_rdm_half_filled(n):
    return np.diag([0.5] * n)

def _mock_rdm_one_empty(n):
    occs = [0.05] + [0.95] * (n - 1)
    return np.diag(occs)

def _mock_rdm_four_empty(n=6):
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
