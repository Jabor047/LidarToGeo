# LidarToGeo

Contains code that goes through the [usgs-lidar-public](https://registry.opendata.aws/usgs-lidar/) dataset, fetches the las and tif files from a region specified by an input, processes these files to give a dictionary that contains a key of year or region of the data and a value of geodataframe that has the elevation, geometry point and the topographic wetness index of the geometry point

This package will write the following to the directory you are running the script in: a laz file, tif file, shp file and a png file depending on the saved_png flag below.

## installation
```
pip install lidar_to_geo

```

## Usage
```python
import lidar_to_geo
# bounds = "([xMin, xMax], [yMin, yMax])"
raster = lidar_to_geo.RasterGetter(bounds, crs)
gpd_dict = raster.region_gdf_dict(saved_png=False, resolution=5)
```