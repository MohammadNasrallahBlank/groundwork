import pytest

from groundwork.tools.ledger.metrics import brier_score, calibration_table


def test_brier_perfect_predictions_is_zero():
    assert brier_score([(1.0, 1), (0.0, 0), (1.0, 1)]) == 0.0


def test_brier_worst_predictions_is_one():
    assert brier_score([(1.0, 0), (0.0, 1)]) == 1.0


def test_brier_uninformed_half_is_quarter():
    assert brier_score([(0.5, 1), (0.5, 0)]) == pytest.approx(0.25)


def test_brier_empty_is_none():
    assert brier_score([]) is None


def test_calibration_table_buckets_and_rates():
    pairs = [(0.9, 1), (0.9, 0), (0.1, 0)]
    table = calibration_table(pairs, bins=5)
    assert len(table) == 5                       # empty buckets kept
    top = [b for b in table if b["range"] == [0.8, 1.0]][0]
    assert top["count"] == 2
    assert top["mean_confidence"] == pytest.approx(0.9)
    assert top["observed_rate"] == pytest.approx(0.5)
    assert top["gap"] == pytest.approx(0.4)
    low = [b for b in table if b["range"] == [0.0, 0.2]][0]
    assert low["count"] == 1 and low["observed_rate"] == 0.0


def test_calibration_last_bucket_is_inclusive_of_one():
    table = calibration_table([(1.0, 1)], bins=5)
    top = [b for b in table if b["range"] == [0.8, 1.0]][0]
    assert top["count"] == 1


def test_calibration_empty_pairs_all_zero_buckets():
    table = calibration_table([], bins=4)
    assert len(table) == 4 and all(b["count"] == 0 for b in table)
    assert all(b["observed_rate"] is None for b in table)
