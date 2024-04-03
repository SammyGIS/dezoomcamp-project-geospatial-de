import ee
import geopandas as gpd
from datetime import datetime, timedelta
from localpackage.utils import upload_dataframe_to_gcs, shp_to_ee_fmt, process_zonal_stats_chunks
from localpackage.utils import  download_geodataframe_from_gcs


# 2. Set JSON key as environment variable
email = "farm-watch-project@data-enginerring-zoomcamp.iam.gserviceaccount.com"
key_file = "./data-enginerring-zoomcamp-b8719aa4a43e.json"

# Authenticate and initialize
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)
ee.Initialize(credentials)

# Get today's date
today = datetime.today()
search_start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
search_end = today.strftime('%Y-%m-%d')


GCS_BUCKET = "sammy_project_bucket2024"
GEOJSON_DATA = 'Nigeria_farmland.geojson'

def source_imagery(IMAGERY, BOUND):
    # Filter and process Sentinel-2 image collection
    dataset = (
        ee.ImageCollection(IMAGERY)
        .filterBounds(BOUND) # Filter to AOI box
        .filterDate(search_start, search_end)  # Filter for single day
        .sort("CLOUD_COVER") # .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))  # Pre-filter for less cloud cover
        .select(['B4', 'B8'])  # Select red (B4) and near-infrared (B8) bands
        .mosaic()
        .clip(BOUND)
    )
    return dataset

def getNDVI(image):
    # Normalized difference vegetation index (NDVI)
    ndvi = image.normalizedDifference(['B8','B4']).rename("ndvi")
    image = image.addBands(ndvi)
    return image

def main():
    # Set analysis parameters
    scale = 100
    chunk_size = 4000  # Step size for subset iteration
    farm_gdf = download_geodataframe_from_gcs(GCS_BUCKET, GEOJSON_DATA,key_file)
    imagery = "COPERNICUS/S2_SR_HARMONIZED"
    farm_boundary = ee.Geometry.MultiPolygon(shp_to_ee_fmt(farm_gdf))
    image = source_imagery(imagery, farm_boundary)
    ndvi = getNDVI(image)
    farmland_ndvi = process_zonal_stats_chunks(ndvi, scale,farm_gdf,chunk_size)

    farmland_ndvi['processed_date'] = today.strftime('%Y-%m-%d')
    gdf_joined = farmland_ndvi.merge(farm_gdf, how='inner', left_index=True, right_index=True)
    farmland_data = gdf_joined[['id', 'ndvi', 'processed_date']]
    # farmland_data.to_csv(f'ndmi_{today.strftime('%Y-%m-%d')}.csv',index=False)

    bucket_name = 'sammy_project_bucket2024'
    destination_blob_path = f'ndvi/ndvi_{today.strftime("%Y-%m-%d")}.csv'

    upload_dataframe_to_gcs(farmland_data,bucket_name, destination_blob_path)

main()