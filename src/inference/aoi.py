import geopandas as gpd
from shapely.geometry import box

def create_aoi(minx, miny, maxx, maxy, crs="EPSG:4326"):
    aoi_geom = box(minx, miny, maxx, maxy)
    return gpd.GeoDataFrame({"geometry": [aoi_geom]}, crs=crs)