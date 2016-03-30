# import json
# import pickle
# import os
# import tempfile

from tomato.MCRCaller import MCRCaller

# instantiate a mcr_caller
_mcr_caller = MCRCaller()


class JointAnalyzer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
