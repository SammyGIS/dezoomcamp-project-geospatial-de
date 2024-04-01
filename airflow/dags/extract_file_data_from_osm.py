import airflow
from datetime import datetime, timedelta
import requests
import json
import osm2geojson
import geopandas as gpd
from airflow.decorators import dag, task
from airflow.models import Variable
from utils import download_geodataframe_from_gcs,upload_geodataframe_to_gcs
import io

# Define the Overpass URL
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

# Define the Overpass QL query
OVERPASS_QUERY = """
                [out:json][timeout:50];
                area["ISO3166-1"="NG"][admin_level=2];
                (
                way["landuse"="farmland"](area);
                relation["landuse"="farmland"](area);
                );
                (._;>;);
                out body;    """

# Default DAG task arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': None,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Define GCS bucket and file paths
GCS_BUCKET = Variable.get("gcs_bucket")  # Get GCS bucket name from Airflow Variables
GCS_INTERMEDIATE_PATH = "osm_farmland.geojson"
GCS_RESULT_PATH = "Nigeria_farmland.geojson"


# Define the DAG
@dag(
    schedule=None,
    catchup=False,
    tags=['farm_data'],
    default_args=default_args,
    dag_id='extract_osm_farmland',
    template_searchpath='/tmp'
)
def extract_osm_farmland():

    @task
    def load_farmland_from_api():
        response = requests.get(OVERPASS_URL, params={'data': OVERPASS_QUERY})
        if response.status_code == 200:
            json_data = response.json()

            # Normalize JSON data
            geojson_data = osm2geojson.json2geojson(json_data)
            farm_gdf = gpd.read_file(json.dumps(geojson_data))
            farm_gdf.reset_index(inplace=True)
            farm_gdf["id"] = farm_gdf["id"].astype(str)
            farm_gdf["landuse"] = farm_gdf['tags'].apply(lambda x: x['landuse'])
            farm_gdf = farm_gdf[['id','landuse','geometry']]

            # Save GeoDataFrame to GCS
            upload_geodataframe_to_gcs(farm_gdf, GCS_BUCKET, GCS_INTERMEDIATE_PATH)

            # Return GCS path
            return f"gs://{GCS_BUCKET}/{GCS_INTERMEDIATE_PATH}"
        else:
            print("Failed to fetch data: HTTP Status Code", response.status_code)
            return None

    @task
    def transform_farmland(farm_gdf_path):
        # Download GeoDataFrame from GCS
        farm_gdf = download_geodataframe_from_gcs(GCS_BUCKET, GCS_INTERMEDIATE_PATH)
        
        url = 'https://raw.githubusercontent.com/SammyGIS/data/main/Nigeria_Ward.geojson'
        ward_shapefile = gpd.read_file(url)
        ward_shapefile.drop(columns=['lgacode','statecode','source','wardcode', 'FID_1'], axis=1, inplace=True)
        ward_shapefile.to_crs(epsg=4326, inplace=True)
        gdf_joined = farm_gdf.sjoin(ward_shapefile, how='inner')

        # Save transformed GeoDataFrame to GCS
        upload_geodataframe_to_gcs(gdf_joined, GCS_BUCKET, GCS_RESULT_PATH)

        return f"gs://{GCS_BUCKET}/{GCS_RESULT_PATH}"

    # Define the tasks
    get_farmland = load_farmland_from_api()
    transform_data = transform_farmland(get_farmland)

    # Set task dependencies
    get_farmland >> transform_data

# Instantiate the DAG
extract_osm_farmland()
