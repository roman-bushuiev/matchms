import numpy
import pytest
from matchms import Spectrum
from matchms.similarity import CosineHungarian


def test_cosine_hungarian_without_parameters():
    """Compare output cosine score with own calculation on simple dummy spectrums."""
    spectrum_1 = Spectrum(mz=numpy.array([100, 200, 300, 500, 510], dtype="float"),
                          intensities=numpy.array([0.1, 0.2, 1.0, 0.3, 0.4], dtype="float"))

    spectrum_2 = Spectrum(mz=numpy.array([100, 200, 290, 490, 510], dtype="float"),
                          intensities=numpy.array([0.1, 0.2, 1.0, 0.3, 0.4], dtype="float"))
    cosine_hungarian = CosineHungarian()
    score, n_matches = cosine_hungarian.pair(spectrum_1, spectrum_2)

    # Derive expected cosine score
    expected_matches = [0, 1, 4]  # Those peaks have matching mz values (within given tolerance)
    multiply_matching_intensities = spectrum_1.peaks.intensities[expected_matches] \
        * spectrum_2.peaks.intensities[expected_matches]
    denominator = numpy.sqrt((spectrum_1.peaks.intensities ** 2).sum()) \
        * numpy.sqrt((spectrum_2.peaks.intensities ** 2).sum())
    expected_score = multiply_matching_intensities.sum() / denominator

    assert score == pytest.approx(expected_score, 0.0001), "Expected different cosine score."
    assert n_matches == len(expected_matches), "Expected different number of matching peaks."


def test_cosine_hungarian_matrix_without_parameters():
    """Compare output cosine score with expected scores."""
    spectrum_1 = Spectrum(mz=numpy.array([100, 200, 300, 500, 510], dtype="float"),
                          intensities=numpy.array([0.1, 0.2, 1.0, 0.3, 0.4], dtype="float"))

    spectrum_2 = Spectrum(mz=numpy.array([100, 200, 290, 490, 510], dtype="float"),
                          intensities=numpy.array([0.1, 0.2, 1.0, 0.3, 0.4], dtype="float"))
    cosine_hungarian = CosineHungarian()
    scores = cosine_hungarian.matrix([spectrum_1, spectrum_2], [spectrum_1, spectrum_2])

    assert scores[0, 0] == scores[1, 1] == (1.0, 5), "Expected different cosine score."
    assert scores[0, 1] == scores[1, 0] == pytest.approx((0.1615384, 3), 1e-6), "Expected different cosine score."


def test_cosine_hungarian_with_tolerance_0_2():
    """Compare output cosine score for tolerance 0.2 with own calculation on simple dummy spectrums."""
    spectrum_1 = Spectrum(mz=numpy.array([100, 299, 300, 301, 510], dtype="float"),
                          intensities=numpy.array([0.1, 1.0, 0.2, 0.3, 0.4], dtype="float"))

    spectrum_2 = Spectrum(mz=numpy.array([100, 300, 301, 511], dtype="float"),
                          intensities=numpy.array([0.1, 1.0, 0.3, 0.4], dtype="float"))
    cosine_hungarian = CosineHungarian(tolerance=0.2)
    score, n_matches = cosine_hungarian.pair(spectrum_1, spectrum_2)

    # Derive expected cosine score
    expected_matches = [[0, 2, 3], [0, 1, 2]]  # Those peaks have matching mz values (within given tolerance)
    multiply_matching_intensities = spectrum_1.peaks.intensities[expected_matches[0]] \
        * spectrum_2.peaks.intensities[expected_matches[1]]
    denominator = numpy.sqrt((spectrum_1.peaks.intensities ** 2).sum()) \
        * numpy.sqrt((spectrum_2.peaks.intensities ** 2).sum())
    expected_score = multiply_matching_intensities.sum() / denominator

    assert score == pytest.approx(expected_score, 0.0001), "Expected different cosine score."
    assert n_matches == len(expected_matches[0]), "Expected different number of matching peaks."


def test_cosine_hungarian_with_tolerance_2_0():
    """Compare output cosine score for tolerance 2.0 with own calculation on simple dummy spectrums."""
    spectrum_1 = Spectrum(mz=numpy.array([100, 299, 300, 301, 510], dtype="float"),
                          intensities=numpy.array([0.1, 1.0, 0.2, 0.3, 0.4], dtype="float"))

    spectrum_2 = Spectrum(mz=numpy.array([100, 300, 301, 511], dtype="float"),
                          intensities=numpy.array([0.1, 1.0, 0.3, 0.4], dtype="float"))
    cosine_hungarian = CosineHungarian(tolerance=2.0)
    score, n_matches = cosine_hungarian.pair(spectrum_1, spectrum_2)

    # Derive expected cosine score
    expected_matches = [[0, 1, 3, 4], [0, 1, 2, 3]]  # Those peaks have matching mz values (within given tolerance)
    multiply_matching_intensities = spectrum_1.peaks.intensities[expected_matches[0]] \
        * spectrum_2.peaks.intensities[expected_matches[1]]
    denominator = numpy.sqrt((spectrum_1.peaks.intensities ** 2).sum()) \
        * numpy.sqrt((spectrum_2.peaks.intensities ** 2).sum())
    expected_score = multiply_matching_intensities.sum() / denominator

    assert score == pytest.approx(expected_score, 0.0001), "Expected different cosine score."
    assert n_matches == len(expected_matches[0]), "Expected different number of matching peaks."


def test_cosine_hungarian_order_of_arguments():
    """Compare cosine scores for A,B versus B,A, which should give the same score."""
    spectrum_1 = Spectrum(mz=numpy.array([100, 200, 299, 300, 301, 500, 510], dtype="float"),
                          intensities=numpy.array([0.02, 0.02, 1.0, 0.2, 0.4, 0.04, 0.2], dtype="float"),
                          metadata=dict())

    spectrum_2 = Spectrum(mz=numpy.array([100, 200, 300, 301, 500, 512], dtype="float"),
                          intensities=numpy.array([0.02, 0.02, 1.0, 0.2, 0.04, 0.2], dtype="float"),
                          metadata=dict())

    cosine_hungarian = CosineHungarian(tolerance=2.0)
    score_1_2, n_matches_1_2 = cosine_hungarian.pair(spectrum_1, spectrum_2)
    score_2_1, n_matches_2_1 = cosine_hungarian.pair(spectrum_2, spectrum_1)

    assert score_1_2 == score_2_1, "Expected that the order of the arguments would not matter."
    assert n_matches_1_2 == n_matches_2_1, "Expected that the order of the arguments would not matter."


def test_cosine_hungarian_case_where_greedy_would_fail():
    """Test case that would fail for cosine greedy implementations."""
    spectrum_1 = Spectrum(mz=numpy.array([100.005, 100.016], dtype="float"),
                          intensities=numpy.array([1.0, 0.9], dtype="float"),
                          metadata={})

    spectrum_2 = Spectrum(mz=numpy.array([100.005, 100.01], dtype="float"),
                          intensities=numpy.array([0.9, 1.0], dtype="float"),
                          metadata={})

    cosine_hungarian = CosineHungarian(tolerance=0.01)
    score, n_matches = cosine_hungarian.pair(spectrum_1, spectrum_2)
    assert score == pytest.approx(0.994475, 0.0001), "Expected different cosine score."
    assert n_matches == 2, "Expected different number of matching peaks."


def test_cosine_hungarian_case_without_matches():
    """Test case for spectrums without any matching peaks."""
    spectrum_1 = Spectrum(mz=numpy.array([100, 200], dtype="float"),
                          intensities=numpy.array([1.0, 0.1], dtype="float"),
                          metadata={})

    spectrum_2 = Spectrum(mz=numpy.array([110, 210], dtype="float"),
                          intensities=numpy.array([1.0, 0.1], dtype="float"),
                          metadata={})

    cosine_hungarian = CosineHungarian()
    score, n_matches = cosine_hungarian.pair(spectrum_1, spectrum_2)
    assert score == 0.0, "Expected different cosine score."
    assert n_matches == 0, "Expected different number of matching peaks."


def test_cosine_hungarian_with_peak_powers():
    """Compare output cosine score with own calculation on simple dummy spectrums.
    Here testing the options to raise peak intensities to given powers.
    """
    mz_power = 0.5
    intensity_power = 2.0
    spectrum_1 = Spectrum(mz=numpy.array([100, 200, 300, 500, 510], dtype="float"),
                          intensities=numpy.array([0.1, 0.2, 1.0, 0.3, 0.4], dtype="float"))

    spectrum_2 = Spectrum(mz=numpy.array([100, 200, 290, 490, 510], dtype="float"),
                          intensities=numpy.array([0.1, 0.2, 1.0, 0.3, 0.4], dtype="float"))
    cosine_hungarian = CosineHungarian(tolerance=1.0, mz_power=mz_power, intensity_power=intensity_power)
    score, n_matches = cosine_hungarian.pair(spectrum_1, spectrum_2)

    # Derive expected cosine score
    matches = [0, 1, 4]  # Those peaks have matching mz values (within given tolerance)
    intensity1 = spectrum_1.peaks.intensities
    mz1 = spectrum_1.peaks.mz
    intensity2 = spectrum_2.peaks.intensities
    mz2 = spectrum_2.peaks.mz
    multiply_matching_intensities = (mz1[matches] ** mz_power) * (intensity1[matches] ** intensity_power) \
        * (mz2[matches] ** mz_power) * (intensity2[matches] ** intensity_power)
    denominator = numpy.sqrt((((mz1 ** mz_power) * (intensity1 ** intensity_power)) ** 2).sum()) \
        * numpy.sqrt((((mz2 ** mz_power) * (intensity2 ** intensity_power)) ** 2).sum())
    expected_score = multiply_matching_intensities.sum() / denominator

    assert score == pytest.approx(expected_score, 0.0001), "Expected different cosine score."
    assert n_matches == len(matches), "Expected different number of matching peaks."
