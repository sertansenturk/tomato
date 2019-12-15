#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 - 2018 Altuğ Karakurt & Sertan Şentürk
#
# This file is part of tomato: https://github.com/sertansenturk/tomato/
#
# tomato is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License v3.0
# along with this program. If not, see http://www.gnu.org/licenses/
#
# If you are using this extractor please cite the following paper:
#
# Karakurt, A., Şentürk S., and Serra X. (2016). MORTY: A toolbox for mode
# recognition and tonic identification. In Proceedings of 3rd International
# Digital Libraries for Musicology Workshop (DLfM 2016). pages 9-16,
# New York, NY, USA

import copy
import json
import pickle

import numpy as np

from .inputparser import InputParser
from .knn import KNN
from ..pitchdistribution import PitchDistribution
from ...converter import Converter


class KNNClassifier(InputParser):
    def __init__(self, step_size=7.5, kernel_width=15.0, feature_type='pcd',
                 model=None):
        """--------------------------------------------------------------------
        These attributes are wrapped as an object since these are used in both
        training and estimation stages and must be consistent in both processes
        -----------------------------------------------------------------------
        step_size       : Step size of the distribution bins
        kernel_width    : Standart deviation of the gaussian kernel used to
                          smoothen the distributions. For further details,
                          see generate_pd() of ModeFunctions.
        feature_type    : The feature type to be used in training and testing
                          ("pd" for pitch distribution, "pcd" for pitch
                          class distribution)
        model           : Pre-trained model
        --------------------------------------------------------------------"""
        super(KNNClassifier, self).__init__(
            step_size=step_size, kernel_width=kernel_width,
            feature_type=feature_type, model=model)

    def train(self, pitches, tonics, modes, sources=None, model_type='multi'):
        if model_type == 'single':
            return self._train_single_distrib_per_mode(
                pitches, tonics, modes, sources=sources)
        elif model_type == 'multi':
            return self._train_multi_distrib_per_mode(
                pitches, tonics, modes, sources=sources)
        else:
            raise ValueError("Unknown training model")

    def _train_single_distrib_per_mode(self, pitches, tonics, modes,
                                       sources=None):
        """--------------------------------------------------------------------
        For the mode trainings, the requirements are a set of recordings with
        annotated tonics for each mode under consideration. This function only
        expects the recordings' pitch tracks and corresponding tonics as lists.
        The two lists should be indexed in parallel, so the tonic of ith pitch
        track in the pitch track list should be the ith element of tonic list.
        Once training is completed for a mode, the model would be generated
        as a PitchDistribution object and saved in a JSON file. For loading
        these objects and other relevant information about the data structure,
        see the PitchDistribution class.
        -----------------------------------------------------------------------
        pitches       : List of pitch tracks or the list of files with
                        stored pitch tracks (i.e. single-column
                        lists/numpy arrays/files with frequencies)
        tonics        : List of annotated tonic frequencies of recordings
        modes         : Name of the modes of each training sample.
        --------------------------------------------------------------------"""

        assert len(pitches) == len(modes) == len(tonics), \
            'The inputs should have the same length!'

        # get the pitch tracks for each mode and convert them to cent unit
        tmp_model = {m: {'sources': [], 'cent_pitch': []} for m in set(modes)}
        for p, t, m, s in zip(pitches, tonics, modes, sources):
            # parse the pitch track from txt file, list or numpy array and
            # normalize with respect to annotated tonic
            pitch_cent = self._parse_pitch_input(p, t)

            # convert to cent track and append to the mode data
            tmp_model[m]['cent_pitch'].extend(pitch_cent)
            tmp_model[m]['sources'].append(s)

        # compute the feature for each model from the normalized pitch tracks
        for data_point in tmp_model.values():
            data_point['feature'] = PitchDistribution.from_cent_pitch(
                data_point.pop('cent_pitch', None),
                kernel_width=self.kernel_width, step_size=self.step_size)

            # convert to pitch-class distribution if requested
            if self.feature_type == 'pcd':
                data_point['feature'].to_pcd()

        # make the model a list of dictionaries by collapsing the mode keys
        # inside the values
        model = []
        for mode_name, data_point in tmp_model.items():
            data_point['mode'] = mode_name
            model.append(data_point)

        self.model = model

    def _train_multi_distrib_per_mode(self, pitches, tonics, modes,
                                      sources=None):
        """--------------------------------------------------------------------
        For the mode trainings, the requirements are a set of recordings with
        annotated tonics for each mode under consideration. This function only
        expects the recordings' pitch tracks and corresponding tonics as lists.
        The two lists should be indexed in parallel, so the tonic of ith pitch
        track in the pitch track list should be the ith element of tonic list.

        Each pitch track would be sliced into chunks of size chunk_size and
        their pitch distributions are generated. Then, each of such chunk
        distributions are appended to a list. This list represents the mode
        by sample points as much as the number of chunks. So, the result is
        a list of PitchDistribution objects, i.e. list of structured
        dictionaries and this is what is saved.
        -----------------------------------------------------------------------
        mode_name     : Name of the mode to be trained. This is only used for
                        naming the resultant JSON file, in the form
                        "mode_name.json"
        pitch_files   : List of pitch tracks (i.e. 1-D list of frequencies)
        tonic_freqs   : List of annotated tonics of recordings
        feature       : Whether the model should be octave wrapped (Pitch Class
                        Distribution: PCD) or not (Pitch Distribution: PD)
        save_dir      : Where to save the resultant JSON files.
        --------------------------------------------------------------------"""
        assert len(pitches) == len(modes) == len(tonics), \
            'The inputs should have the same length!'

        # get the pitch tracks for each mode and convert them to cent unit
        model = []
        for p, t, m, s in zip(pitches, tonics, modes, sources):
            # parse the pitch track from txt file, list or numpy array and
            # normalize with respect to annotated tonic
            pitch_cent = self._parse_pitch_input(p, t)
            feature = PitchDistribution.from_cent_pitch(
                pitch_cent, kernel_width=self.kernel_width,
                step_size=self.step_size)

            # convert to pitch-class distribution if requested
            if self.feature_type == 'pcd':
                feature.to_pcd()

            data_point = {'source': s, 'tonic': t, 'mode': m,
                          'feature': feature}
            # convert to cent track and append to the mode data
            model.append(data_point)

        self.model = model

    def identify_tonic(self, test_input, mode, min_peak_ratio=0.1,
                       distance_method='bhat', k_neighbor=15, rank=1):
        """--------------------------------------------------------------------
        Tonic Identification: The mode of the recording is known and the
        tonic is to be estimated.
        :param test_input: - precomputed feature (PD or PCD in Hz)
                           - pitch track in Hz (list or numpy array)
        :param mode: input mode label
        :param min_peak_ratio: The minimum ratio between the max peak value and
                               the value of a detected peak
        :param distance_method: distance used in KNN
        :param k_neighbor: number of neighbors to select in KNN classification
        :param rank: number of estimations to return
        :return: ranked mode estimations
        --------------------------------------------------------------------"""
        test_feature = self._parse_tonic_and_joint_estimate_input(test_input)

        # Tonic Estimation
        estimations = self._estimate(
            test_feature, est_tonic=True, mode=mode,
            min_peak_ratio=min_peak_ratio, distance_method=distance_method,
            k_neighbor=k_neighbor, rank=rank)

        # remove the dummy tonic estimation
        tonics_ranked = [(e[0][0], e[1]) for e in estimations]

        return tonics_ranked

    def estimate_tonic(self, test_input, mode, min_peak_ratio=0.1,
                       distance_method='bhat', k_neighbor=1, rank=1):
        """
        Alias of "identify_tonic" method. See the documentation of
        "identify_tonic" for more information.
        """
        return self.identify_tonic(
            test_input, mode, min_peak_ratio=min_peak_ratio,
            distance_method=distance_method, k_neighbor=k_neighbor, rank=rank)

    def recognize_mode(self, feature_in, tonic=None, distance_method='bhat',
                       k_neighbor=15, rank=1):
        """--------------------------------------------------------------------
        Mode recognition: The tonic of the recording is known and the mode is
        to be estimated.
        :param feature_in: - precomputed feature (PitchDistribution object)
                           - pitch track (list or numpy array)
        :param tonic: tonic frequency (float). It is needed if the feature_in
                      has not been normalized with respect to the tonic earlier
        :param distance_method: distance used in KNN
        :param k_neighbor: number of neighbors to select in KNN classification
        :param rank: number of estimations to return
        :return: ranked mode estimations
        --------------------------------------------------------------------"""
        test_feature = self._parse_mode_estimate_input(feature_in, tonic)

        # Mode Estimation
        estimations = self._estimate(
            test_feature, est_tonic=False, mode=None,
            distance_method=distance_method, k_neighbor=k_neighbor, rank=rank)

        # remove the dummy tonic estimation
        modes_ranked = [(e[0][1], e[1]) for e in estimations]

        return modes_ranked

    def estimate_mode(self, feature_in, tonic=None, distance_method='bhat',
                      k_neighbor=15, rank=1):

        return self.recognize_mode(
            feature_in, tonic=tonic, distance_method=distance_method,
            k_neighbor=k_neighbor, rank=rank)

    def estimate_joint(self, test_input, min_peak_ratio=0.1,
                       distance_method='bhat', k_neighbor=15, rank=1):
        """--------------------------------------------------------------------
        Joint estimation: Estimate both the tonic and mode together
        :param test_input: - precomputed feature (PD or PCD in Hz)
                           - pitch track in Hz (list or numpy array)
        :param min_peak_ratio: The minimum ratio between the max peak value and
                               the value of a detected peak
        :param distance_method: distance used in KNN
        :param k_neighbor: number of neighbors to select in KNN classification
        :param rank: number of estimations to return
        :return: ranked mode and tonic estimations
        --------------------------------------------------------------------"""
        test_feature = self._parse_tonic_and_joint_estimate_input(test_input)

        # Mode Estimation
        joint_estimations = self._estimate(
            test_feature, est_tonic=True, mode=None,
            min_peak_ratio=min_peak_ratio, distance_method=distance_method,
            k_neighbor=k_neighbor, rank=rank)

        return joint_estimations

    def _estimate(self, test_feature, mode=None, est_tonic=True,
                  min_peak_ratio=0.1, distance_method='bhat', k_neighbor=15,
                  rank=1):
        assert est_tonic or mode is None, 'Nothing to estimate.'

        if est_tonic is True:
            # find the tonic candidates of the input feature
            test_feature, tonic_cands, peak_idx = self._get_tonic_candidates(
                test_feature, min_peak_ratio=min_peak_ratio)
        else:
            # dummy assign the first index
            tonic_cands = np.array([test_feature.ref_freq])
            peak_idx = np.array([0])

        training_features, training_modes = self._get_training_model(mode)
        dist_mat = KNN.generate_distance_matrix(
            test_feature, peak_idx, training_features,
            distance_method=distance_method)

        # sort results
        sorted_idx = np.argsort(dist_mat, axis=None)
        sorted_dists = np.sort(dist_mat, axis=None)
        sorted_tonic_cand_idx, sorted_mode_idx = np.unravel_index(
            sorted_idx, dist_mat.shape)

        # convert from sorted index to sorted tonic frequency and mode
        sorted_tonics = tonic_cands[sorted_tonic_cand_idx]
        sorted_modes = training_modes[sorted_mode_idx]
        sorted_pairs = [((t, m), d) for t, m, d in
                        zip(sorted_tonics, sorted_modes, sorted_dists)]

        # there might be enough options to get estimations up to the
        # requested rank. Max is the number of unique sortd pairs
        max_rank = len(set(sp[0] for sp in sorted_pairs))

        # compute ranked estimations
        ranked_pairs = []
        for _ in range(min(rank, max_rank)):
            cand_pairs = KNN.get_nearest_neighbors(sorted_pairs, k_neighbor)
            estimation, sorted_pairs = KNN.classify(cand_pairs, sorted_pairs)
            ranked_pairs.append(estimation)

        return ranked_pairs

    @staticmethod
    def _get_tonic_candidates(test_feature, min_peak_ratio=0.1):
        # find the global minima and shift the distribution there so
        # peak detection does not fail locate a peak in the boundary in
        # octave-wrapped features. For features that are not
        # octave-wrapped this step is harmless.
        shift_feature = copy.deepcopy(test_feature)
        global_minima_idx = np.argmin(shift_feature.vals)
        shift_feature.shift(global_minima_idx)

        # get the peaks of the feature as the tonic candidate indices and
        # compute the stable frequencies from the peak indices
        peak_idx = shift_feature.detect_peaks(min_peak_ratio=min_peak_ratio)[0]
        peaks_cent = shift_feature.bins[peak_idx]
        freqs = Converter.cent_to_hz(peaks_cent, shift_feature.ref_freq)

        # return the shifted feature, stable frequencies and their
        # corresponding index in the shifted feature
        return shift_feature, freqs, peak_idx

    def _get_training_model(self, mode):
        if mode is None:
            training_features = [m['feature'] for m in self.model]
            feature_modes = np.array([m['mode'] for m in self.model])
        else:
            training_features = [m['feature'] for m in self.model
                                 if m['mode'] == mode]
            # create dummy array with annotated mode
            feature_modes = np.array(
                [mode for _ in range(len(training_features))])
        return training_features, feature_modes

    def model_from_pickle(self, input_str):
        try:  # file given
            self.model = pickle.load(open(input_str, 'rb'))
        except IOError:  # string given
            self.model = pickle.loads(input_str, 'rb')

    @staticmethod
    def model_to_pickle(model, file_name=None):
        if file_name is None:
            return pickle.dumps(model)
        else:
            pickle.dump(model, open(file_name, 'wb'))

    def model_from_json(self, file_name):
        """--------------------------------------------------------------------
        Loads a the training model from JSON file.
        -----------------------------------------------------------------------
        file_name    : The filename of the JSON file
        --------------------------------------------------------------------
        """
        try:
            temp_model = json.load(open(file_name, 'r'))
        except IOError:  # json string
            temp_model = json.loads(file_name)

        for tm in temp_model:
            tm['feature'] = tm['feature'] if isinstance(tm['feature'], dict) \
                else tm['feature'][0]
            tm['feature'] = PitchDistribution.from_dict(tm['feature'])

        self.model = temp_model

    @staticmethod
    def model_to_json(model, file_name=None):
        """--------------------------------------------------------------------
        Saves the training model to a JSON file.
        -----------------------------------------------------------------------
        model        : Training model
        file_name    : The file path of the JSON file to be created. None to
                       return a json string
        --------------------------------------------------------------------"""
        temp_model = copy.deepcopy(model)
        for tm in temp_model:
            try:
                tm['feature'] = tm['feature'].to_dict()
            except AttributeError:  # already a dict
                assert isinstance(tm['feature'], dict), \
                    'The feature should have been a dict'

        if file_name is None:
            return json.dumps(temp_model, indent=4)
        else:
            json.dump(temp_model, open(file_name, 'w'), indent=4)
