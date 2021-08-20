import geopandas as gpd
import geoplot as gplt


def heatmap(region: str):
    gdf = gpd.read_file(region + ".csv")
    gdf.plot()
