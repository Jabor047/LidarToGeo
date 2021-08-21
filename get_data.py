import ast
import pdal
import json
import load_data
import logging
import georasters as gr
import geopandas as gpd
from pprint import pprint

form = logging.Formatter("%(asctime)s : %(levelname)-5.5s : %(message)s")
logger = logging.getLogger()


consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(form)
logger.addHandler(consoleHandler)

logger.setLevel(logging.INFO)

class RasterGetter:

    def __init__(self, bounds: str, crs: int) -> None:
        self.bounds = bounds
        self.crs = crs
        self.public_data_path = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/"
        # get region based in bounds
        self.regions = self.get_region(bounds)
        self.load_pipeline()

    def get_region(self, bounds: str) -> str:
        logger.info("\n\n Finding bounds region")
        region_ept_info = load_data.load_ept_json()
        user_bounds = ast.literal_eval(bounds)
        regions = []

        for key, value in region_ept_info.items():
            if value.bounds[0] <= user_bounds[0][0] and \
                value.bounds[1] <= user_bounds[1][0] and \
                value.bounds[3] >= user_bounds[0][1] and \
                    value.bounds[4] >= user_bounds[1][1]:
                regions.append(key)

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
        self.external_pipeline['pipeline'][3]['filename'] = f"{str(region).strip('/')}.laz"
        self.external_pipeline['pipeline'][4]['filename'] = f"{str(region).strip('/')}.tif"

        # create pdal pipeline
        pipeline = pdal.Pipeline(json.dumps(self.external_pipeline))
        logger.info("Pipeline Dumped and Read for use")

        # execute pipeline
        try:
            pipe_exec = pipeline.execute()
            metadata = pipeline.metadata
            log = pipeline.log
            logger.info("Pipeline Complete Execution Successfully ")

        except RuntimeError as e:
            print(e)
            logger.info("Pipeline Process Could not be completed")

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

        print(self.gdf.head())

        if save:
            self.save_geodataframe(csv_filename=f"{str(self.region).strip('/')}.csv")
            return self.gdf
        else:
            return self.gdf

    def save_geodataframe(self, csv_filename: str):
        self.gdf.to_csv(csv_filename, index=False)
        logger.info(f"GeoDataframe Elevation File Successfully Saved here {csv_filename}")

    def year_gpd_dict(self) -> dict:
        year_gpd = {}
        for region in self.regions:
            year = region.split("_")[-1][:-1]
            if not year.isdigit():
                year = region

            self.get_raster_terrain(region)
            year_gpd[year] = self.get_geodataframe(f"{str(region).strip('/')}.tif", False)

        return year_gpd

if __name__ == "__main__":
    BOUNDS = "([-10425171.940, -10423171.940], [5164494.710, 5166494.710])"
    # 32618

    raster = RasterGetter(bounds=BOUNDS, crs=32618)
    dict_year_gpd = raster.year_gpd_dict()
    pprint(dict_year_gpd)
