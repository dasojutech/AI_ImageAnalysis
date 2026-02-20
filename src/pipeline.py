# from visualisation.plotmap import plot_overlay
# # pipeline.py
# from ingestion.sentinel import download_sentinel
# from preprocessing.reprojection import reproject_vectors_to_raster_crs
# from utils.io import save_map
# import geopandas as gpd
# from shapely.geometry import box
# import osmnx as ox

# def run_pipeline(config):
#     # 1️⃣ Define AOI
#     minx = config["aoi"]["minx"]
#     miny = config["aoi"]["miny"]
#     maxx = config["aoi"]["maxx"]
#     maxy = config["aoi"]["maxy"]
#     aoi_geom = box(minx, miny, maxx, maxy)
#     aoi = gpd.GeoDataFrame({"geometry":[aoi_geom]}, crs="EPSG:4326")

#     # 2️⃣ Download Sentinel raster
#     raster_path = "../outputs/raster/S2A_sample_B04.tif"

#     # 3️⃣ Load vector layers
#     place_name = config["vector"]["place_name"]
#     roads = ox.graph_to_gdfs(ox.graph_from_place(place_name, network_type='drive'))[1]
#     admin = gpd.read_file(config["vector"]["admin"])

#     # 4️⃣ Reproject all vectors to raster CRS
#     roads, admin, aoi = reproject_vectors_to_raster_crs(
#     raster_path,
#     [roads, admin, aoi]  # admin should be a GeoDataFrame, not a path string
# )

#     # 5️⃣ Plot overlay
#     vector_layers = [roads, admin, aoi]
#     fig = plot_overlay(raster_path, vector_layers, save_path=config["output_map_name"])

#     return fig
# src/pipeline.py
import os
import geopandas as gpd
import rasterio
from ingestion.sentinel import download_sentinel
from preprocessing.reprojection import reproject_vectors_to_raster_crs
from visualisation.plotmap import plot_overlay

import osmnx as ox

def run_pipeline(config):
    # Download raster
    raster_path = "../outputs/raster/S2A_sample_B04.tif"

    # Load vectors
    place_name = config["vector"]["place_name"]

    # Roads and admin from OSM
    roads = ox.graph_to_gdfs(ox.graph_from_place(place_name, network_type="drive"))[1]
    admin = ox.geocode_to_gdf(place_name)

    # AOI
    from shapely.geometry import box
    aoi_bbox = config["aoi"]["bbox"]
    aoi_geom = box(*aoi_bbox)
    aoi = gpd.GeoDataFrame({"geometry": [aoi_geom]}, crs="EPSG:4326")

    # Reproject to raster CRS
    roads, admin, aoi = reproject_vectors_to_raster_crs(raster_path, [roads, admin, aoi])

    # Plot overlay
    fig = plot_overlay(raster_path, [roads, admin, aoi])
    fig.show()