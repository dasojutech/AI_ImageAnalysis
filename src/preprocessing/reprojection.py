import rasterio

def reproject_vector_to_raster(vector_gdf, raster_path):
    roads = roads.to_crs(raster_crs)
    admin = admin.to_crs(raster_crs)
    aoi = aoi.to_crs(raster_crs)
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        print(roads.crs)
        print(admin.crs)
        print(aoi.crs)
    return vector_gdf.to_crs(raster_crs)
def reproject_vectors_to_raster_crs(raster_path, vectors):
    import rasterio
    reprojected = []
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        for v in vectors:
            reprojected.append(v.to_crs(raster_crs))
    return reprojected