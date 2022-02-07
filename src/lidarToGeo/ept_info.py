import json
import src.lidarToGeo.schema
import pyproj
import numpy as np
from pyproj import CRS
from src.lidarToGeo.schema import Schema

class Info(object):
    """
    This class takes in the ept.json and processes the data in the json file
    to a format that we can easily call as attributes of the class

    reference: https://entwine.io/entwine-point-tile.html

    """
    def __init__(self, data) -> None:
        self.data = json.loads(data)

    def length(self) -> int:
        """
        reads the data in the points key in the ept json i.e
        all the data points in this particular data
        """
        return int(self.data['points'])

    def get_schema(self) -> src.lidarToGeo.schema.Schema:
        """
        reads the data in the schema key and passes that data to the Schema class
        """
        return Schema(self.data['schema'])
    schema = property(get_schema)

    def get_span(self) -> int:
        """
        reads the data in the span key in the ept json
        """
        return int(self.data['span'])
    span = property(get_span)

    def get_version(self) -> str:
        """
        reads the data in the version key in the ept json
        """
        return self.data['version']
    version = property(get_version)

    def get_bounds(self) -> list:
        """
        reads the data in the bounds key in the ept json
        """
        return self.data['bounds']
    bounds = property(get_bounds)

    def get_conforming(self) -> list:
        """
        reads the data in the boundsConforming key in the ept json
        """
        return self.data['boundsConforming']
    conforming = property(get_conforming)

    def get_datatype(self) -> str:
        """
        reads what type of data format the point clouds are in
        """
        return self.data['dataType']
    datatype = property(get_datatype)

    def get_hierarchytype(self) -> str:
        """
        reads the data in the hierarchyType key in the ept json
        """
        return self.data['hierarchyType']
    hierarchytype = property(get_hierarchytype)

    def get_srs(self) -> pyproj.crs.crs.CRS:
        """
        reads the data in the 'srs' key and computes a CRS from the 'wkt' value
        in the 'srs' key

        returns: a pyproj.crs
        """
        wkt = self.data['srs']['wkt']
        crs = CRS.from_user_input(wkt)
        return crs
    srs = property(get_srs)
