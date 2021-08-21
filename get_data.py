import ast
from logging import Logger
import pdal
import json
import load_data
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

    def get_region(self, bounds: str) -> str:
        logger.info("Finding inputed bound's region")
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
        logger.info(f"region containing the boundaries are {regions}")
        return regions

    def load_pipeline(self, pipeline_filename='get_data.json'):
        try:
            with open(pipeline_filename) as json_file:
                the_json = json.load(json_file)

            self.external_pipeline = the_json
            logger.info("Template Pipeline Successfully Loaded")
        except Exception as e:
            print(e)
            logger.info("Template Pipeline Could not be Loaded")

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
        logger.info("Pipeline Complete Execution Successfully ")

    def get_geodataframe(self, tif_file: str, save: bool) -> gpd.GeoDataFrame:
        data = gr.from_file(tif_file)
        logger.info("GeoTiff File Loaded")

        df = data.to_pandas()

        df.drop(["row", "col"], axis=1)
        df.rename(columns={'value': 'elevation'}, inplace=True)
        df = df[['x', 'y', 'elevation']]

        self.gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.x, df.y))

        epsg = 'EPSG:' + str(self.crs)
        self.gdf.crs = epsg

        if save:
            self.save_geodataframe(csv_filename=f"{str(self.region).strip('/')}.csv")
            return self.gdf
        else:
            return self.gdf

    def save_geodataframe(self, csv_filename: str):
        self.gdf.to_csv(csv_filename, index=False)
        logger.info(f"GeoDataframe Elevation File Successfully Saved here {csv_filename}")

    def region_gpd_dict(self) -> dict:
        region_gpd = {}
        for region in self.regions:
            year = region.split("_")[-1][:-1]
            if not year.isdigit():
                year = region
            try:
                print("\n")
                self.get_raster_terrain(region)
                gpd = self.get_geodataframe(f"{str(region).strip('/')}.tif",
                                            False)
                region_gpd[year] = gpd
            except RuntimeError as e:
                logger.warning(e)
                logger.info(f"Pipeline Process Could not be completed for region {region}")
                if len(self.regions) > 1:
                    print("\n")
                    logger.info("fecthing the next region")

        return region_gpd

if __name__ == "__main__":
    BOUNDS = "([-10425171.940, -10423171.940], [5164494.710, 5166494.710])"
    # 32618

    raster = RasterGetter(bounds=BOUNDS, crs=3857)
    dict_region_gpd = raster.region_gpd_dict()
    pprint(dict_region_gpd)
