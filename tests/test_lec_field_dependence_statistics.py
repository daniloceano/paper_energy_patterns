import numpy as np

from scripts.lec_field_dependence_analysis.utils_statistical_tests import _dunn_test


def test_rank_biserial_sign_matches_named_contrast_direction():
    results = _dunn_test(
        [np.array([8.0, 9.0, 10.0]), np.array([1.0, 2.0, 3.0])],
        ["EP1", "EP2"],
    )

    assert len(results) == 1
    assert results[0]["contrast"] == "EP1 vs EP2"
    assert results[0]["direction"] == "EP1 > EP2"
    assert results[0]["effect_size"] == 1.0


def test_rank_biserial_sign_is_negative_when_second_group_is_larger():
    results = _dunn_test(
        [np.array([1.0, 2.0, 3.0]), np.array([8.0, 9.0, 10.0])],
        ["EP1", "EP2"],
    )

    assert results[0]["direction"] == "EP2 > EP1"
    assert results[0]["effect_size"] == -1.0


def test_direction_follows_rank_dominance_when_medians_disagree():
    results = _dunn_test(
        [np.array([0.0, 2.0, 2.0]), np.array([1.0, 1.0, 100.0])],
        ["EP1", "EP2"],
    )

    assert np.median([0.0, 2.0, 2.0]) > np.median([1.0, 1.0, 100.0])
    assert results[0]["effect_size"] < 0
    assert results[0]["direction"] == "EP2 > EP1"


def test_zero_rank_biserial_reports_no_rank_dominance():
    results = _dunn_test(
        [np.array([0.0, 2.0]), np.array([1.0, 1.0])],
        ["EP1", "EP2"],
    )

    assert results[0]["effect_size"] == 0.0
    assert results[0]["direction"] == "no rank dominance"
