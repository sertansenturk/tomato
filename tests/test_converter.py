import numpy as np
import pytest

from tomato.converter import Converter


def test_hz_to_cent_negative_hz_track():
    # GIVEN
    hz_track = np.array([-50])
    ref_freq = np.float(25.0)

    # WHEN; THEN
    with pytest.raises(ValueError):
        Converter.hz_to_cent(hz_track, ref_freq)


def test_hz_to_cent_negative_ref_freq():
    # GIVEN
    hz_track = np.array([50])
    ref_freq = np.float(-5.0)

    # WHEN; THEN
    with pytest.raises(ValueError):
        Converter.hz_to_cent(hz_track, ref_freq)


def test_hz_to_cent_negative_min_freq():
    # GIVEN
    hz_track = np.array([50])
    ref_freq = np.float(25.0)
    min_freq = -5.0

    # WHEN; THEN
    with pytest.raises(ValueError):
        Converter.hz_to_cent(hz_track, ref_freq, min_freq)


def test_hz_to_cent_ref_less_than_min():
    # GIVEN
    hz_track = np.array([50])
    ref_freq = np.float(25.0)
    min_freq = np.float(30.0)

    # WHEN; THEN
    with pytest.raises(ValueError):
        Converter.hz_to_cent(hz_track, ref_freq, min_freq)


def test_hz_to_cent_hz_less_than_min():
    # GIVEN
    hz_track = np.array([20])
    ref_freq = np.float(35.0)
    min_freq = np.float(30.0)

    # WHEN
    result = Converter.hz_to_cent(hz_track, ref_freq, min_freq)

    # THEN
    expected = np.array([np.nan])
    np.testing.assert_array_equal(result, expected)