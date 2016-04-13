from abc import ABCMeta, abstractmethod, abstractproperty
from IO import IO
import logging
import warnings
from six import iteritems


class Analyzer(object):
    __metaclass__ = ABCMeta

    def __init__(self, verbose):
        self.verbose = verbose

    @abstractproperty
    def _features(self):
        pass

    @abstractmethod
    def analyze(self, *args, **kwargs):
        pass

    @abstractmethod
    def plot(self):
        pass

    def _set_params(self, analyzer_str, **kwargs):
        analyzer = getattr(self, analyzer_str)
        attribs = IO.get_public_attr(analyzer)

        Analyzer.chk_params(attribs, kwargs)

        for key, value in kwargs.items():
            setattr(analyzer, key, value)

    def _parse_inputs(self, **kwargs):
        # initialize precomputed_features with the available analysis
        precomputed_features = dict((f, None)
                                    for f in self._features)
        for feature, val in iteritems(kwargs):
            if feature not in self._features:
                warn_str = u'Unrelated feature {0:s}: It will be kept, ' \
                           u'but it will not be used in the audio analysis.' \
                           u''.format(feature)
                warnings.warn(warn_str)
            precomputed_features[feature] = val

        return precomputed_features

    def _call_analysis_step(self, method_name, feature_flag,
                            *input_features):
        if feature_flag is False:  # call skipped
            return None
        elif feature_flag is None:  # call method
            method = getattr(self, method_name)
            try:
                return method(*input_features)
            except KeyError:
                logging.info('{0:s}.{1:s} failed.'.
                             format(self.__class__, method_name))
                return None
        else:  # flag is the precomputed feature itself
            return feature_flag

    @staticmethod
    def chk_params(attribs, kwargs):
        if any(key not in attribs for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(attribs))

    def vprint(self, vstr):
        """
        Prints the input string if the verbose flag of the object is set to
        True
        :param vstr: input string to print
        """
        if self.verbose is True:
            print(vstr)

    def vprint_time(self, tic, toc):
        self.vprint(u"  The call took {0:.2f} seconds to execute.".
                    format(toc - tic))
