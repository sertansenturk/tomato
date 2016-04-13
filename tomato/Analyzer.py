from abc import ABCMeta, abstractmethod


class Analyzer(object):
    __metaclass__ = ABCMeta

    def __init__(self, verbose):
        self.verbose = verbose

    @abstractmethod
    def analyze(self, *args, **kwargs):
        pass

    def _set_params(self, analyzer_str, **kwargs):
        analyzer = getattr(self, analyzer_str)
        attribs = self.get_public_attr(analyzer)

        Analyzer.chk_params(attribs, kwargs)

        for key, value in kwargs.items():
            setattr(analyzer, key, value)

    @staticmethod
    def chk_params(attribs, kwargs):
        if any(key not in attribs for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(attribs))

    def get_public_attr(self):
        return [name for name in self.__dict__.keys()
                if not name.startswith('_')]

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
