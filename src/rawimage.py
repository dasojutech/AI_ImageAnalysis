import os
import requests
import numpy as np
import rasterio
from rasterio.plot import reshape_as_image
from shapely.geometry import box, mapping
from pystac_client import Client
from planetary_computer import sign

# -----------------------------
# 1️⃣ Define AOI: San Francisco
# -----------------------------
lon_min, lat_min = -123.0, 37.6
lon_max, lat_max = -121.7, 38.2
aoi_geom = mapping(box(lon_min, lat_min, lon_max, lat_max))

# -----------------------------
# 2️⃣ Connect to Planetary Computer STAC
# -----------------------------
catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

# -----------------------------
# 3️⃣ Search for Sentinel-2 L2A images
# -----------------------------
items = list(catalog.search(
    collections=["sentinel-2-l2a"],
    intersects=aoi_geom,
    datetime="2024-01-01/2024-12-31",  # adjust as needed
    query={"eo:cloud_cover": {"lt": 20}},
    max_items=5
).get_all_items())

print(f"Found {len(items)} images covering San Francisco.")

# -----------------------------
# 4️⃣ Prepare directories
# -----------------------------
DATA_DIR = r'd:/Laxmi/JPMC/repo_portfolio/AI_ImageAnalysis/data'
RGB_DIR = os.path.join(DATA_DIR, "RGB")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RGB_DIR, exist_ok=True)

# -----------------------------
# 5️⃣ Process each item
# -----------------------------
for item in items:
    print(f"\nProcessing {item.id}")
    band_files = {}

    # 5a: Download all available bands
    for band_name, asset in item.assets.items():
        if "B0" in band_name:  # filter for Sentinel-2 bands
            filename = os.path.join(DATA_DIR, f"{item.id}_{band_name}.tif")
            if not os.path.exists(filename):
                url = sign(asset.href)
                print(f"Downloading {band_name} ...")
                try:
                    r = requests.get(url, stream=True, timeout=60)
                    if r.status_code == 200:
                        with open(filename, "wb") as f:
                            for chunk in r.iter_content(8192):
                                f.write(chunk)
                        print(f"✅ Saved {filename}")
                        band_files[band_name] = filename
                    else:
                        print(f"⚠️ Failed {band_name}, status code {r.status_code}")
                except Exception as e:
                    print(f"⚠️ Error downloading {band_name}: {e}")
            else:
                print(f"{filename} already exists")
                band_files[band_name] = filename

    # 5b: Determine available RGB band keys
    red_key = next((k for k in band_files if "B04" in k), None)
    green_key = next((k for k in band_files if "B03" in k), None)
    blue_key = next((k for k in band_files if "B02" in k), None)

    if red_key and green_key and blue_key:
        try:
            with rasterio.open(band_files[red_key]) as r:
                red_data = r.read(1)
                profile = r.profile

            with rasterio.open(band_files[green_key]) as g:
                green_data = g.read(1)
            with rasterio.open(band_files[blue_key]) as b:
                blue_data = b.read(1)

            rgb_array = np.stack([red_data, green_data, blue_data])
            rgb_profile = profile.copy()
            rgb_profile.update(count=3)

            rgb_filename = os.path.join(RGB_DIR, f"{item.id}_RGB.tif")
            with rasterio.open(rgb_filename, "w", **rgb_profile) as dst:
                dst.write(rgb_array)

            print(f"✅ Created RGB composite: {rgb_filename}")
        except Exception as e:
            print(f"⚠️ Failed to create RGB for {item.id}: {e}")
    else:
        missing = []
        if not red_key: missing.append("B04")
        if not green_key: missing.append("B03")
        if not blue_key: missing.append("B02")
        print(f"⚠️ Skipping RGB for {item.id}, missing bands: {missing}")

print("\n✅ Done! Check your 'data/' and 'data/RGB/' folders.")