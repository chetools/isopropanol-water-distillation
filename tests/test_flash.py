import numpy as np

from src.flash import ideal_tp_flash, nonideal_tp_flash, rachford_rice


def test_rachford_rice_closes_material_balance():
    z = np.array([0.4, 0.6])
    k = np.array([2.0, 0.5])
    beta = rachford_rice(z, k)
    x = z / (1 + beta * (k - 1))
    y = k * x
    assert 0 < beta < 1
    assert np.isclose(x.sum(), 1.0)
    assert np.isclose(y.sum(), 1.0)
    assert np.allclose(z, (1 - beta) * x + beta * y)


def test_ideal_and_nonideal_tp_flash_return_normalized_phases():
    for result in (ideal_tp_flash(355.0, 101325.0, 0.2), nonideal_tp_flash(355.0, 101325.0, 0.2)):
        assert 0 <= result["beta"] <= 1
        assert np.isclose(result["x"].sum(), 1.0)
        assert np.isclose(result["y"].sum(), 1.0)

