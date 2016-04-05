class ParamSetter(object):
    def set_params(self, analyzer_str, **kwargs):
        analyzer = getattr(self, analyzer_str)
        attribs = [name for name in analyzer.__dict__.keys()
                   if not name.startswith('_')]

        if any(key not in attribs for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(attribs))

        for key, value in kwargs.items():
            setattr(analyzer, key, value)
