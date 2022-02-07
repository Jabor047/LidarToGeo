import numpy as np

class Schema(object):
    """
    reads and processes the dictionary / json in the schema key of the ept.json files
    to a format we can call as attributes to the Schema class
    """
    def __init__(self, data) -> None:
        self.dimesions = self.get_dimensions(data)

    def length(self) -> int:
        """
        returns the length of the schema dictionary
        """
        return len(self.dimesions)

    def get_dimensions(self, data: dict) -> dict:
        """
        gets the data types of the schema elements

        Parameters
        ----------
        data : dictionary

        Returns: dictionary containing the name of the schema element and it's data type
        -------

        """
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
        """
        describes how the bytes in the fixed-size block of memory corresponding
        to a schema item should be interpreted
        """
        dt = []
        for d in self.dimesions:
            dim = self.dimesions[d]
            dt.append((dim['name'], dim['dtype']))

        return np.dtype(dt)
    dtype = property(get_dtype)
