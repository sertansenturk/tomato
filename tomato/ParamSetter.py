class ParamSetter(object):
    def _set_params(self, analyzer_str, **kwargs):
        analyzer = getattr(self, analyzer_str)
        attribs = self._get_public_attr(analyzer)

        if any(key not in attribs for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(attribs))

        for key, value in kwargs.items():
            setattr(analyzer, key, value)

    @staticmethod
    def _get_public_attr(obj):
        return [name for name in obj.__dict__.keys()
                if not name.startswith('_')]
