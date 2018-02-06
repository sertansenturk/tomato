import warnings


class OffsetProcessor(object):
    """

    """
    def __init__(self, print_warnings=True):
        self.print_warnings = print_warnings

    def find_measure_start_idx(self, offsets):
        measure_start_idx = []
        is_measure_start_valid = True

        tol = 0.001
        for int_offset in range(0, int(max(offsets)) + 1):
            idx = min(i for i, o in enumerate(offsets) if o > int_offset - tol)
            measure_start_idx.append(idx)

        is_measure_start_valid = self._validate_measure_start(
            is_measure_start_valid, measure_start_idx, offsets)

        return measure_start_idx, is_measure_start_valid

    def _validate_measure_start(self, is_measure_start_valid,
                                measure_start_idx, offsets):
        # find the measures starts which does not coincide to an integer offset
        noninteger_measure_starts = self._find_non_integer_measure_starts(
            measure_start_idx, offsets)

        # all measures should start on integer offsets
        if noninteger_measure_starts:
            is_measure_start_valid = False
            if self.print_warnings:
                warn_str = ', '.join(str(e) for e in noninteger_measure_starts)

                warnings.warn(u"Some measures are skipped by the offsets: "
                              u"{0!s}".format(warn_str), stacklevel=2)

        return is_measure_start_valid

    def _find_non_integer_measure_starts(self, measure_start_idx, offsets):
        noninteger_measure_starts = []
        for i in measure_start_idx:
            if not self.is_integer_offset(offsets[i]):
                noninteger_measure_starts.append(offsets[i])

        return noninteger_measure_starts

    @staticmethod
    def is_integer_offset(offset):
        # The measure changes when the offset is an integer
        # (Note that offset was shifted by one earlier for easier processing )
        # Since integer check in floating point math can be inexact,
        # we accept +- 0.001
        return abs(offset - round(offset)) * 1000.0 < 1.0

    @staticmethod
    def get_measure_offset_id(measure_offset, offsets, measure_start_idx):
        measure_start_offsets = [offsets[m] for m in measure_start_idx]
        # do inexact integer matching
        dist = [abs(o - measure_offset) for o in measure_start_offsets]
        return measure_start_idx[dist.index(min(dist))]
