class ParamSetter(object):
    def _set_params(self, analyzer_str, **kwargs):
        analyzer = getattr(self, analyzer_str)
        attribs = self.get_public_attr(analyzer)

        ParamSetter.chk_params(attribs, kwargs)

        for key, value in kwargs.items():
            setattr(analyzer, key, value)

    @staticmethod
    def chk_params(attribs, kwargs):
        if any(key not in attribs for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(attribs))

    @staticmethod
    def get_public_attr(obj):
        return [name for name in obj.__dict__.keys()
                if not name.startswith('_')]
