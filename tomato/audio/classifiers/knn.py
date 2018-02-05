# -*- coding: utf-8 -*-
from __future__ import division
from scipy.spatial import distance as spdistance
import collections
import numpy as np
import copy


class KNN(object):
    @classmethod
    def generate_distance_matrix(cls, distrib, peak_idx, training_distribs,
                                 distance_method='bhat'):
        """--------------------------------------------------------------------
        Iteratively calculates the distance of the input distribution from each
        (mode candidate, tonic candidate) pair. This is a generic function,
        that is independent of distribution type or any other parameter value.
        -----------------------------------------------------------------------
        distribs            : Input distribution that is to be estimated
        peak_idx            : List of indices of distribution peaks
        training_distribs   : List of training distributions
        method              : The distance method to be used. The available
                              distances are listed in _distance() method.
        --------------------------------------------------------------------"""
        result = np.zeros((len(peak_idx), len(training_distribs)))
        trial = copy.deepcopy(distrib)

        # convert the shifts from absolute wrt the reference distribution to
        # relative wrt the previous shift
        shift_idx = np.diff(np.insert(peak_idx, 0, 0))

        # Iterates over the peaks, i.e. the tonic candidates
        for i, cur_peak_idx in enumerate(shift_idx):
            trial.shift(cur_peak_idx)

            # Iterates over mode candidates
            for j, td in enumerate(training_distribs):
                assert trial.bin_unit == td.bin_unit, \
                    'The bin units of the compared distributions should match.'
                assert trial.distrib_type() == td.distrib_type(), \
                    'The features should be of the same type'
                assert trial.step_size == td.step_size, \
                    'The step_sizes should be the same'

                if trial.is_pcd():
                    trial_vals = trial.vals
                    td_vals = td.vals
                else:  # PD, compare in the overlapping region
                    min_td_bin = np.min(td.bins)
                    max_td_bin = np.max(td.bins)

                    min_trial_bin = np.min(trial.bins)
                    max_trial_bin = np.max(trial.bins)

                    overlap = [max([min_td_bin, min_trial_bin]),
                               min([max_td_bin, max_trial_bin])]

                    trial_bool = (overlap[0] <= trial.bins) * \
                                 (trial.bins <= overlap[1])
                    trial_vals = trial.vals[trial_bool]

                    td_bool = (overlap[0] <= td.bins) * \
                              (td.bins <= overlap[1])
                    td_vals = td.vals[td_bool]

                if any([td_vals.size == 0, trial_vals.size == 0]):
                    # no overlapping, only in pd
                    assert not trial.is_pcd(), \
                        'The distributions should have been pitch ' \
                        'distribution to become non-overlapping'
                    result[i][j] = 0
                else:
                    # Calls the distance function for each entry of the matrix
                    result[i][j] = cls._compute_measure(trial_vals, td_vals,
                                                        method=distance_method)
        return np.array(result)

    @staticmethod
    def _compute_measure(vals_1, vals_2, method='bhat'):
        """--------------------------------------------------------------------
         Computes the distance or dissimilairty between two 1-D lists of
         values. This function is called with pitch distribution values,
         while generating matrices. The function is symmetric, the two input
         lists are interchangable.
         ----------------------------------------------------------------------
         vals_1, vals_2 : The input value lists.
         method         : The choice of distance method
         ----------------------------------------------------------------------
         manhattan    : Minkowski distance of 1st degree
         euclidean    : Minkowski distance of 2nd degree
         l3           : Minkowski distance of 3rd degree
         bhat         : Bhattacharyya distance
         intersection : Intersection
         corr         : Correlation
         -------------------------------------------------------------------"""
        if method in ['manhattan', 'l1']:
            return spdistance.minkowski(vals_1, vals_2, 1)
        elif method in ['euclidean', 'l2']:
            return spdistance.euclidean(vals_1, vals_2)
        elif method == 'l3':
            return spdistance.minkowski(vals_1, vals_2, 3)
        elif method == 'bhat':  # bhattacharrya distance
            return -np.log(np.sum(np.sqrt(vals_1 * vals_2)))
        elif method == 'jeffrey':  # Jeffrey's divergence
            return (np.sum(vals_1 * np.log(vals_1 / vals_2)) +
                    np.sum(vals_2 * np.log(vals_2 / vals_1)))
        elif method == 'js':  # Jensen–Shannon distance
            return np.sqrt(
                np.sum(vals_1 * np.log(2 * vals_1 / (vals_1 + vals_2))) * 0.5 +
                np.sum(vals_2 * np.log(2 * vals_2 / (vals_1 + vals_2))) * 0.5)
        # Since correlation and intersection are actually similarity measures,
        # we convert them to dissimilarities, by taking 1 - similarity
        elif method == 'dis_intersect':
            return 1.0 - np.sum(np.minimum(vals_1, vals_2)) / np.size(vals_1)
        elif method == 'dis_corr':
            return 1.0 - np.correlate(vals_1, vals_2)
        else:
            return 0

    @staticmethod
    def get_nearest_neighbors(sorted_pair, k_neighbor):
        # parse mode/tonic pairs
        pairs = [pair for pair, dist in sorted_pair[:k_neighbor]]

        # find the most common pairs
        counter = collections.Counter(pairs)
        most_commons = counter.most_common(k_neighbor)
        max_cnt = most_commons[0][1]
        cand_pairs = [c[0] for c in most_commons if c[1] == max_cnt]

        return cand_pairs

    @staticmethod
    def classify(cand_pairs, sorted_pair):
        # in case there are multiple candidates get the pair sorted earlier
        for p in sorted_pair:
            if p[0] in cand_pairs:
                estimated_pair = p

                # pop the estimated pair from the sorted_pair list for ranking
                sorted_pair = [pp for pp in sorted_pair if pp[0] != p[0]]
                return estimated_pair, sorted_pair

        assert False, 'No pair selected, this should be impossible!'
