import unittest
import sys
import geopandas as gpd
from pathlib import Path

test_file = Path(__file__).resolve()
parent_dir = test_file.parents[1]
sys.path.append(str(parent_dir))

from get_data import RasterGetter

class TestRasterGetter(unittest.TestCase):
    """
        A class for unit-testing function in the ept_info.py file

        Args:
        -----
            unittest.TestCase this allows the new class to inherit
            from the unittest module
    """

    def setUp(self):
        self.region = "IA_FullState/"
        self.bounds = "([-10425171.940, -10423171.940], [5164494.710, 5166494.710])"
        self.crs = 3857
        self.raster = RasterGetter(self.bounds, self.crs)

    def test_get_region(self):
        self.assertIn(self.region, self.raster.get_region(self.bounds))

    def test_get_geodataframe(self):
        self.assertIsInstance(self.raster.get_geodataframe(self.region, False, 5),
                              gpd.GeoDataFrame)

    def test_region_gdf_dict(self):
        self.assertIsInstance(self.raster.region_gdf_dict(False, 5), dict)
