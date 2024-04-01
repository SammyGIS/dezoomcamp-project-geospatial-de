import ee
import dotenv
import os
from datetime import datetime, timedelta
from utils import shp_to_ee_fmt, process_zonal_stats_chunks
import geopandas as gpd
from utils import upload_dataframe_to_gcs

dotenv.load_dotenv()

# 2. Set JSON key as environment variable

email = os.getenv('EMAIL')
key_file = "data-enginering-zoom-camp-d547d133c38f.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=key_file

# Authenticate and initialize
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)
ee.Initialize(credentials)

# Get today's date
today = datetime.today()
search_start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
search_end = today.strftime('%Y-%m-%d')

def source_imagery(IMAGERY, BOUND):
    # Filter and process Sentinel-2 image collection
    dataset = (
        ee.ImageCollection(IMAGERY)
        .filterBounds(BOUND) # Filter to AOI box
        .filterDate(search_start, search_end)  # Filter for single day
        .sort("CLOUD_COVER") # .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))  # Pre-filter for less cloud cover
        .select(['B8', 'B11'])  # Select red (B4) and near-infrared (B8) bands
        .mosaic()
        .clip(BOUND)
    )
    return dataset

# def source_landsat_imagery(IMAGERY, BOUND):
#     # Filter and process Sentinel-2 image collection
#     dataset = (
#         ee.ImageCollection(IMAGERY)
#         .filterBounds(BOUND) # Filter to AOI box
#         .filterDate(search_start, search_end)  # Filter for single day
#         .sort("CLOUD_COVER")  # Pre-filter for less cloud cover
#         .select(['B4', 'B5'])  # Select red (B4) and near-infrared (B5) bands
#         .mosaic()
#         .clip(BOUND)
#     )
#     return dataset

def getNDVI(image):
    # Normalized difference vegetation index (NDVI)
    ndvi = image.normalizedDifference(['B8','B11']).rename("ndvi")
    image = image.addBands(ndvi)
    return image

if __name__ == '__main__':
    # Set analysis parameters
    scale = 100
    chunk_size = 4000  # Step size for subset iteration
    farmland = "farmland.geojson"
    farmland_gdf = gpd.read_file(farmland)

    imagery = "COPERNICUS/S2_SR_HARMONIZED"
    farm_boundary = ee.Geometry.MultiPolygon(shp_to_ee_fmt(farmland_gdf ))
    image = source_imagery(imagery, farm_boundary)
    ndvi = getNDVI(image)
    farmland_ndvi = process_zonal_stats_chunks(ndvi, scale,farmland_gdf,chunk_size)

    farmland_ndvi['processed_date'] = today.strftime('%Y-%m-%d')
    gdf_joined = farmland_ndvi.merge(farmland_gdf, how='inner', left_index=True, right_index=True)
    farmland_data = gdf_joined[['id', 'statename', 'lganame', 'wardname', 'urban', 'landuse', 'ndvi', 'processed_date', 'geometry_x']]
    # farmland_data.to_csv(f'ndvi_{today.strftime('%Y-%m-%d')}.csv',index=False)

    bucket_name = 'farm_project'
    destination_blob_path = f'ndvi/ndvi_{today.strftime('%Y-%m-%d')}.csv'


    upload_dataframe_to_gcs(farmland_data,bucket_name, destination_blob_path)