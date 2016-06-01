from abc import ABCMeta, abstractmethod, abstractproperty
from io import IO
import logging
import warnings
from six import iteritems


class Analyzer(object):
    __metaclass__ = ABCMeta

    def __init__(self, verbose):
        self.verbose = verbose

    @abstractproperty
    def _inputs(self):
        pass

    @abstractmethod
    def analyze(self, *args, **kwargs):
        pass

    @abstractmethod
    def plot(self):
        pass

    def _set_params(self, analyzer_str, **kwargs):
        analyzer = getattr(self, analyzer_str)
        attribs = IO.public_noncallables(analyzer)

        Analyzer.chk_params(attribs, kwargs)

        for key, value in kwargs.items():
            setattr(analyzer, key, value)

    @staticmethod
    def chk_params(attribs, kwargs):
        if any(key not in attribs for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(attribs))

    def _parse_inputs(self, **kwargs):
        # initialize precomputed_features with the available analysis
        precomputed_features = dict((f, None)
                                    for f in self._inputs)
        for feature, val in iteritems(kwargs):
            if feature not in self._inputs:
                warn_str = u'Unrelated feature {0:s}: It will be kept, ' \
                           u'but it will not be used in the audio analysis.' \
                           u''.format(feature)
                warnings.warn(warn_str, stacklevel=2)
            precomputed_features[feature] = val

        return precomputed_features

    @staticmethod
    def _partial_caller(flag, func, *input_args, **input_kwargs):
        if flag is False:  # call skipped
            return None
        elif flag is None:  # call method
            try:
                return func(*input_args, **input_kwargs)
            except (RuntimeError, KeyError, IndexError, ValueError):
                logging.info('{0:s} failed.'.format(func.__name__))
                return None
        else:  # flag is the precomputed feature itself
            return flag

    @staticmethod
    def _get_first(feature):
        if isinstance(feature, list):  # list of features given
            return feature[0]  # for now get the first feature
        return feature

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
