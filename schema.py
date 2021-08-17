import numpy as np

class Schema(object):
    def __init__(self, data) -> None:
        self.dimesions = self.get_dimensions(data)

    def length(self) -> int:
        return len(self.dimesions)

    def get_dimensions(self, data) -> dict:
        dimensions = {}

        for d in data:
            name = d['name']

            kind = 'i'
            if d['type'] == 'unsigned':
                kind = 'u'
            elif d['type'] == "signed":
                kind = 'i'
            elif d['type'] == 'float':
                kind = 'f'
            else:
                raise TypeError(f"Unrecognised type{d['type']}, cannot convert {d['type']}"
                                "to numpy dtype")

            d['dtype'] = kind + str(d['size'])
            dimensions[name] = d

        return dimensions

    def get_dtype(self) -> np.dtype:
        dt = []
        for d in self.dimesions:
            dim = self.dimesions[d]
            dt.append((dim['name'], dim['dtype']))

        return np.dtype(dt)
    dtype = property(get_dtype)
