import os
import ast
import pdal
import json
import src.lidarToGeo.load_data
from osgeo import ogr, gdal
import numpy as np
import geopandas as gpd
from src.lidarToGeo.logger import setup_logger

logger = setup_logger("get_data")

class RasterGetter:
    """
    fetches the point cloud data from the usgs-lidar-public bucket and converts it
    to a geopandas dataframe

    dataset: https://registry.opendata.aws/usgs-lidar/
    """

    def __init__(self, bounds: str, crs: int) -> None:
        self.bounds = bounds
        self.crs = crs
        self.public_data_path = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/"
        # get region based in bounds
        self.regions = self.get_region(bounds)
        self.path = os.getcwd()
        self.construct_pipeline()

    def get_region(self, bounds: str) -> list:
        """

        Gets all the regions the given boundaries lie in

        Parameters
        ----------
        bounds: str : a string containing the bounds you wish to get a
                    geodataframe of. e.g "([-10425171.940, -10423171.940], [5164494.710, 5166494.710])"

        Returns: a list with all the regions the give bounds
                lie inf
        -------

        """
        logger.info("Finding Entered bound's region")
        region_ept_info = src.lidarToGeo.load_data.load_ept_json()
        user_bounds = ast.literal_eval(bounds)
        regions = []

        for key, value in region_ept_info.items():
            if value.bounds[0] <= user_bounds[0][0] and \
                value.bounds[1] <= user_bounds[1][0] and \
                value.bounds[3] >= user_bounds[0][1] and \
                    value.bounds[4] >= user_bounds[1][1]:
                regions.append(key)

        print("\n")
        logger.info(f"regions containing the boundaries are {regions}")
        return regions

    def construct_pipeline(self):
        """
        creates a list containing a json of the pipeline to pass into the PDAL
        library
        """
        self.dynamic_pipeline = []
        reader = {
            "bounds": "",
            "filename": "",
            "type": "readers.ept",
            "tag": "readdata"
        }
        self.dynamic_pipeline.append(reader)
        classification_filter = {
            "limits": "Classification![2:7], Classification![9:9]",
            "type": "filters.range",
            "tag": "nonoise"

        }
        self.dynamic_pipeline.append(classification_filter)
        reprojection = {
            "in_srs": "EPSG:3857",
            "out_srs": "EPSG:3857",
            "tag": "reprojectUTM",
            "type": "filters.reprojection"
        }
        self.dynamic_pipeline.append(reprojection)
        laz_writer = {
            "filename": "",
            "inputs": ["reprojectUTM"],
            "tag": "writerslas",
            "type": "writers.las"
        }
        self.dynamic_pipeline.append(laz_writer)
        tif_writer = {
            "filename": "",
            "gdalopts": "tiled=yes,     compress=deflate",
            "inputs": ["writerslas"],
            "nodata": -9999,
            "output_type": "idw",
            "resolution": 5,
            "type": "writers.gdal",
            "window_size": 6
        }
        self.dynamic_pipeline.append(tif_writer)

    def get_raster_terrain(self, region: str) -> None:
        """

        Generates the region's las and tif files using the pdal library

        Parameters
        ----------
        region: str : region where bounds occur
        """

        logger.info(f"Fetching Laz and tiff files for {region}")
        PUBLIC_ACCESS_PATH = self.public_data_path + region + "ept.json"

        # dynamically update template pipeline
        self.dynamic_pipeline[0]['bounds'] = self.bounds
        self.dynamic_pipeline[0]['filename'] = PUBLIC_ACCESS_PATH
        self.dynamic_pipeline[2]['in_srs'] = f"EPSG:{self.crs}"
        self.dynamic_pipeline[2]['out_srs'] = f"EPSG:{self.crs}"
        self.dynamic_pipeline[3]['filename'] = self.path + f"/{str(region).strip('/')}.laz"
        self.dynamic_pipeline[4]['filename'] = self.path + f"/{str(region).strip('/')}.tif"

        # create pdal pipeline
        pipeline = pdal.Pipeline(json.dumps(self.dynamic_pipeline))
        logger.info("Pipeline Dumped and Read for use")

        # execute pipeline
        pipe_exec = pipeline.execute()
        metadata = pipeline.metadata
        log = pipeline.log
        logger.info("Pipeline Completed Execution Successfully ")

    def get_geodataframe(self, region: str, save_png: bool, resolution: int) -> gpd.GeoDataFrame:
        """

        Converts the pdal generated tif file into a shp file and creates a geodataframe from the
        shp file and calculates it topographic wetness index

        Parameters
        ----------
        region: str : region where bounds occur

        save_png: bool : Whether to save the plot of the region (takes a significant amount of time
        to save the plot)

        resolution: int : resolution of the points

        Returns: a geopandas dataframe
        -------

        """
        self.tif_to_shp(self.path + f"/{str(region).strip('/')}.tif",
                        self.path + f"/{str(region).strip('/')}.shp")
        self.gdf = gpd.read_file(self.path + f"/{str(region).strip('/')}.shp")

        self.gdf["area"] = self.gdf["geometry"].area
        self.gdf["denom"] = self.gdf["elevation"] / resolution
        self.gdf["TWI"] = np.log(self.gdf["area"] / self.gdf["denom"])

        self.gdf.drop(["area", "denom"], axis=1, inplace=True)

        self.gdf["geometry"] = self.gdf["geometry"].centroid

        if save_png:
            logger.info(f"saving plot as {str(region).strip('/')}.png")
            plot = self.gdf.plot(column="elevation", kind='geo', legend=True)
            fig = plot.get_figure()
            fig.set_size_inches(18.5, 10.5)
            fig.savefig(f"{str(region).strip('/')}.png")

        return self.gdf

    def save_as_geojson(self, filename: str) -> None:
        """

        saves the geopandas datafrme in the geojson format

        Parameters
        ----------
        filename: str : what you want the json saved as

        Returns
        -------

        """
        self.gdf.to_file(filename, driver="GeoJSON")
        logger.info(f"GeoDataframe Elevation File Successfully Saved as {filename}")

    def region_gdf_dict(self, saved_png: bool, resolution: int = 5) -> dict:
        """

        creates a dictionary where the keys are the regions or the years where
        the entered boundaries fall in

        Parameters
        ----------
        saved_png: bool : save the plot of the region the bounds fall in

        resolution: int : resolution of the geometric points
             (Default value = 5)

        Returns: a dictionary of form {"year / region": geopandas.DataFrame}
        -------

        """
        region_gdf = {}
        for region in self.regions:
            year = region.split("_")[-1][:-1]
            if not year.isdigit():
                year = region
            try:
                print("\n")
                self.get_raster_terrain(region)
                gdf = self.get_geodataframe(region, saved_png, resolution)
                region_gdf[year] = gdf
            except RuntimeError as e:
                logger.warning(e)
                logger.info(f"Pipeline Process Could not be completed for region {region}")
                if len(self.regions) > 1:
                    print("\n")
                    logger.info("fecthing the next region")

        return region_gdf

    def tif_to_shp(self, tif_filename: str, shp_filename: str) -> None:
        """
        Converts the pdal generated tif file into a shp file

        Parameters
        ----------
        tif_filename: str : name of the created tif file

        shp_filename: str : name of the shp file to be saved as

        Returns
        -------

        """
        # mapping between gdal type and ogr field type
        type_mapping = {gdal.GDT_Byte: ogr.OFTInteger,
                        gdal.GDT_UInt16: ogr.OFTInteger,
                        gdal.GDT_Int16: ogr.OFTInteger,
                        gdal.GDT_UInt32: ogr.OFTInteger,
                        gdal.GDT_Int32: ogr.OFTInteger,
                        gdal.GDT_Float32: ogr.OFTReal,
                        gdal.GDT_Float64: ogr.OFTReal,
                        gdal.GDT_CInt16: ogr.OFTInteger,
                        gdal.GDT_CInt32: ogr.OFTInteger,
                        gdal.GDT_CFloat32: ogr.OFTReal,
                        gdal.GDT_CFloat64: ogr.OFTReal}

        gdal.UseExceptions()
        logger.info("Converting tif file to shp")
        try:
            ds = gdal.Open(tif_filename)
        except RuntimeError as e:
            logger.error(f"could not open {tif_filename}")
            exit()

        try:
            srcband = ds.GetRasterBand(1)
        except RuntimeError as e:
            # for example, try GetRasterBand(10)
            logger.error('Band ( %i ) not found' % 1)
            logger.error(e)
            exit()

        # create shapefile datasource from geotiff file
        logger.info(f"saving shapefile to {shp_filename}")
        dst_layername = "Shape"
        drv = ogr.GetDriverByName("ESRI Shapefile")
        dst_ds = drv.CreateDataSource(shp_filename)
        dst_layer = dst_ds.CreateLayer(dst_layername, srs=None)
        raster_field = ogr.FieldDefn('elevation', type_mapping[srcband.DataType])
        dst_layer.CreateField(raster_field)
        gdal.Polygonize(srcband, None, dst_layer, 0, [], callback=None)

if __name__ == "__main__":
    BOUNDS = "([-10425171.940, -10423171.940], [5164494.710, 5166494.710])"
    # 32618

    raster = RasterGetter(bounds=BOUNDS, crs=3857)
    dict_region_gpd = raster.region_gdf_dict(False, 5)
