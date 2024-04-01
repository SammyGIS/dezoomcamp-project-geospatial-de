import ee
import dotenv
import os
from datetime import datetime, timedelta
from utils import shp_to_ee_fmt, process_zonal_stats_chunks
import geopandas as gpd

dotenv.load_dotenv()

email = os.getenv('EMAIL')
key_file = "data-enginering-zoom-camp-d547d133c38f.json"

# Authenticate and initialize
credentials = ee.ServiceAccountCredentials(email=email, key_file=key_file)
ee.Initialize(credentials)

# Get today's date
today = datetime.today()
search_start = (today - timedelta(days=5)).strftime('%Y-%m-%d')
search_end = today.strftime('%Y-%m-%d')

def source_imagery(IMAGERY, BOUND,start,end,*args,**kwargs):
    # Filter and process Sentinel-2 image collection
    dataset = (
        ee.ImageCollection(IMAGERY)
        .filterBounds(BOUND) # Filter to AOI box
        .filterDate(start,end)  # Filter for single day
        )
    return dataset


if __name__ == '__main__':
    # Set analysis parameters
    scale = 11132
    chunk_size = 4000  # Step size for subset iteration

    farmland = "farmland.geojson"
    farmland_gdf = gpd.read_file(farmland)

    sentinel2_imagery = "ECMWF/ERA5_LAND/MONTHLY"
    farm_boundary = ee.Geometry.MultiPolygon(shp_to_ee_fmt(farmland_gdf ))

    image = source_imagery(sentinel2_imagery, farm_boundary,
                           '2015-01-01', '2021-12-31').select('temperature_2m').mean().clip(farm_boundary)

    farmland_clim = process_zonal_stats_chunks(image,scale,farmland_gdf,chunk_size)
    farmland_clim['Avg Temp'] = farmland_clim['mean']
    farmland_clim['processed_date'] = today.strftime('%Y-%m-%d')
    gdf_joined = farmland_clim.merge(farmland_gdf, how='inner', left_index=True, right_index=True)
    farmland_data = gdf_joined[['id', 'statename', 'lganame', 'wardname', 'urban', 'landuse', 'Avg Temp', 'processed_date', 'geometry_x']]
    farmland_data.to_csv('farm_temperature.csv')
