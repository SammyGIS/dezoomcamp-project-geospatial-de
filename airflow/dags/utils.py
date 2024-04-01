import geopandas as gpd
from google.cloud import storage
import io

# Specify the path to your service account JSON credentials
json_credentials_path = '/opt/airflow/dags/key/data-enginerring-zoomcamp-b8719aa4a43e.json'



def upload_geodataframe_to_gcs(geodataframe: gpd.GeoDataFrame,
                               bucket_name: str,
                               destination_blob_path: str,
                                ):
    if not isinstance(geodataframe, gpd.GeoDataFrame):
        raise ValueError("Input geodataframe is not a GeoDataFrame")

    storage_client = storage.Client.from_service_account_json(json_credentials_path)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_path)

    # Convert GeoDataFrame to GeoJSON string
    geojson_str = geodataframe.to_json()

    # Upload GeoJSON string to GCS
    blob.upload_from_string(geojson_str)

    print(f'DataFrame uploaded to GCS: gs://{bucket_name}/{destination_blob_path}')



def download_geodataframe_from_gcs(bucket_name, file_path):
    client = storage.Client.from_service_account_json(json_credentials_path)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    data = blob.download_as_string()
    gdf = gpd.read_file(io.BytesIO(data))
    return gdf


