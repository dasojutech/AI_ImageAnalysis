import os
import rasterio
import numpy as np
from shapely.geometry import box, mapping
import geopandas as gpd
import osmnx as ox
from pystac_client import Client
from planetary_computer import sign

# -----------------------------
# 1️⃣ Define AOI: San Francisco
# -----------------------------
lon_min, lat_min = -123.0, 37.6
lon_max, lat_max = -121.7, 38.2
aoi_geom = mapping(box(lon_min, lat_min, lon_max, lat_max))

# -----------------------------
# 2️⃣ Create directories
# -----------------------------
DATA_DIR = r"C:\projects\image_analysis\AI_ImageAnalysis\data"
IMG_DIR = os.path.join(DATA_DIR, "sentinel")
RGB_DIR = os.path.join(DATA_DIR, "RGB2")
VECTOR_DIR = os.path.join(DATA_DIR, "vectors")

for d in [IMG_DIR, RGB_DIR, VECTOR_DIR]:
    os.makedirs(d, exist_ok=True)

# -----------------------------
# 3️⃣ Download Sentinel-2 imagery (COGs)
#    Source: Microsoft Planetary Computer
# -----------------------------
catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

search = catalog.search(
    collections=["sentinel-2-l2a-cogs"],
    intersects=aoi_geom,
    datetime="2024-01-01/2024-12-31",
    query={"eo:cloud_cover": {"lt": 20}},
    max_items=5
)

items = list(search.get_all_items())
print(f"Found {len(items)} Sentinel-2 images covering San Francisco in 2024.\n")

# Bands at 10m resolution
bands = ["B02", "B03", "B04", "B08"]

for item in items:
    print(f"Processing {item.id} ...")
    available_bands = {}

    for band in bands:
        asset_name = f"{band}_10m"

        if asset_name in item.assets:
            signed_url = sign(item.assets[asset_name].href)
            out_path = os.path.join(IMG_DIR, f"{item.id}_{band}_10m.tif")

            try:
                with rasterio.open(signed_url) as src:
                    meta = src.meta.copy()
                    data = src.read()

                with rasterio.open(out_path, "w", **meta) as dst:
                    dst.write(data)

                available_bands[band] = out_path
                print(f"  ✅ Downloaded {band}")

            except Exception as e:
                print(f"  ⚠️ Failed {band}: {e}")

    # -----------------------------
    # Create RGB Composite
    # -----------------------------
    if all(b in available_bands for b in ["B04", "B03", "B02"]):

        red_path = available_bands["B04"]
        green_path = available_bands["B03"]
        blue_path = available_bands["B02"]

        with rasterio.open(red_path) as r:
            red = r.read(1)
            meta = r.meta.copy()

        with rasterio.open(green_path) as g:
            green = g.read(1)

        with rasterio.open(blue_path) as b:
            blue = b.read(1)

        # Stack RGB
        rgb = np.stack([red, green, blue])

        meta.update(count=3)

        rgb_out = os.path.join(RGB_DIR, f"{item.id}_RGB.tif")

        with rasterio.open(rgb_out, "w", **meta) as dst:
            dst.write(rgb)

        print(f"  🎨 RGB composite saved: {rgb_out}")

    else:
        print(f"  ⚠️ Skipping RGB for {item.id}, missing bands")

# -----------------------------
# 4️⃣ Download OSM vector data
#    Source: OpenStreetMap
# -----------------------------
place_name = "San Francisco, California, USA"

# Buildings
print("\nDownloading OSM building footprints...")
buildings = ox.features_from_place(place_name, tags={"building": True})
buildings_file = os.path.join(VECTOR_DIR, "sf_buildings.geojson")
buildings.to_file(buildings_file, driver="GeoJSON")
print(f"  ✅ Saved {len(buildings)} buildings → {buildings_file}")

# Roads (drivable network)
print("Downloading OSM road network...")
roads = ox.graph_from_place(place_name, network_type="drive")
roads_file = os.path.join(VECTOR_DIR, "sf_roads.gpkg")
ox.save_graph_geopackage(roads, filepath=roads_file)
print(f"  ✅ Saved roads → {roads_file}")

print("\n✅ Done! Your raster and vector datasets are ready.")