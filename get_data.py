import ast
import pdal
import json
import load_data

PUBLIC_DATA_PATH = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/"
REGION = 'IA_FullState/'
# ([minx, maxx], [miny, maxy])
BOUNDS = "([-10425171.940, -10423171.940], [5164494.710, 5166494.710])"
PUBLIC_ACCESS_PATH = PUBLIC_DATA_PATH + REGION + "ept.json"
OUTPUT_FILENAME_LAZ = "laz/iowa2.laz"
OUTPUT_FILENAME_TIF = "tif/iowa2.tif"
PIPELINE_PATH = 'get_data.json'

def get_region(bounds: str):
    region_ept_info = load_data.load_ept_json()
    user_bounds = ast.literal_eval(bounds)

    for key, value in region_ept_info.items():
        if value.bounds[0] <= user_bounds[0][0] and \
            value.bounds[1] <= user_bounds[1][0] and \
            value.bounds[3] >= user_bounds[0][1] and \
                value.bounds[4] >= user_bounds[1][1]:
            return key

def get_raster_terrain(bounds: str,
                       OUTPUT_FILENAME_LAZ: str = OUTPUT_FILENAME_LAZ,
                       OUTPUT_FILENAME_TIF: str = OUTPUT_FILENAME_TIF,
                       PIPELINE_PATH: str = PIPELINE_PATH) -> None:

    # print(BOUNDS)
    region = get_region(bounds)
    PUBLIC_ACCESS_PATH = PUBLIC_DATA_PATH + region + "ept.json"

    with open(PIPELINE_PATH) as json_file:
        the_json = json.load(json_file)

    the_json['pipeline'][0]['bounds'] = bounds
    the_json['pipeline'][0]['filename'] = PUBLIC_ACCESS_PATH
    the_json['pipeline'][3]['filename'] = OUTPUT_FILENAME_LAZ
    the_json['pipeline'][4]['filename'] = OUTPUT_FILENAME_TIF

    pipeline = pdal.Pipeline(json.dumps(the_json))

    try:
        pipe_exec = pipeline.execute()
        metadata = pipeline.metadata
        log = pipeline.log

        print('metadata', metadata)
        print('logs', log)

    except RuntimeError as e:
        print(e)
        # RuntimeError: filters.hag: Input PointView does not have any points classified as ground
        print('RunTime Error, writing 0s and moving to next bounds')
        pass


if __name__ == "__main__":
    get_raster_terrain(bounds=BOUNDS)
