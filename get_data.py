import ast
import math
import pdal
import json
import load_data
from osgeo import ogr, gdal
import numpy as np
import georasters as gr
import geopandas as gpd
from pprint import pprint
from logger import setup_logger

logger = setup_logger("get_data")

class RasterGetter:

    def __init__(self, bounds: str, crs: int) -> None:
        self.bounds = bounds
        self.crs = crs
        self.public_data_path = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/"
        # get region based in bounds
        self.regions = self.get_region(bounds)
        self.load_pipeline()

    def get_region(self, bounds: str) -> list:
        logger.info("Finding Entered bound's region")
        region_ept_info = load_data.load_ept_json()
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
            "resolution": 1,
            "type": "writers.gdal",
            "window_size": 6
        }
        self.dynamic_pipeline.append(tif_writer)

        return self.dynamic_pipeline

    def load_pipeline(self):
        try:
            self.external_pipeline = self.construct_pipeline()
            logger.info("Template Pipeline Successfully created")
        except Exception as e:
            print(e)
            logger.info("Template Pipeline Could not be created")

    def get_raster_terrain(self, region: str) -> None:

        logger.info(f"Fetching Laz and tiff files for {region}")
        PUBLIC_ACCESS_PATH = self.public_data_path + region + "ept.json"

        # dynamically update template pipeline
        self.external_pipeline['pipeline'][0]['bounds'] = self.bounds
        self.external_pipeline['pipeline'][0]['filename'] = PUBLIC_ACCESS_PATH
        self.external_pipeline['pipeline'][2]['in_srs'] = f"EPSG:{self.crs}"
        self.external_pipeline['pipeline'][2]['out_srs'] = f"EPSG:{self.crs}"
        self.external_pipeline['pipeline'][3]['filename'] = f"{str(region).strip('/')}.laz"
        self.external_pipeline['pipeline'][4]['filename'] = f"{str(region).strip('/')}.tif"

        # create pdal pipeline
        pipeline = pdal.Pipeline(json.dumps(self.external_pipeline))
        logger.info("Pipeline Dumped and Read for use")

        # execute pipeline
        pipe_exec = pipeline.execute()
        metadata = pipeline.metadata
        log = pipeline.log
        logger.info("Pipeline Completed Execution Successfully ")

    def get_geodataframe(self, region: str, save_png: bool, resolution: int) -> gpd.GeoDataFrame:
        self.tif_to_shp(f"{str(region).strip('/')}.tif", f"{str(region).strip('/')}.shp")
        gdf = gpd.read_file(f"{str(region).strip('/')}.shp")

        gdf["area"] = gdf["geometry"].area
        gdf["denom"] = gdf["elevation"] / resolution
        gdf["TWI"] = np.log(gdf["area"] / gdf["denom"])

        gdf.drop(["area", "denom"], axis=1, inplace=True)

        gdf["geometry"] = gdf["geometry"].centroid

        if save_png:
            logger.info(f"saving plot as {str(region).strip('/')}.png")
            plot = self.gdf.plot(column="elevation", kind='geo', legend=True)
            fig = plot.get_figure()
            fig.set_size_inches(18.5, 10.5)
            fig.savefig(f"{str(region).strip('/')}.png")

        return gdf

    def save_as_geojson(self, filename: str) -> None:
        self.gdf.to_file(filename, driver="GeoJSON")
        logger.info(f"GeoDataframe Elevation File Successfully Saved as {filename}")

    def region_gdf_dict(self, saved_png: bool, resolution: int = 5) -> dict:
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
