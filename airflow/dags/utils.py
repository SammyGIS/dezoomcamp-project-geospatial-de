import geopandas as gpd
from google.cloud import storage
from google.cloud import bigquery
import geojson
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



def upload_geojson_to_bigquery(table_id, bucket_name, destination_blob_path):
    # Initialize BigQuery client using service account credentials
    bigquery_client = bigquery.Client.from_service_account_json(json_credentials_path)
    
    # Get the GeoJSON data from GCS
    storage_client = storage.Client.from_service_account_json(json_credentials_path)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_path)
    geojson_data = blob.download_as_string()

    # Parse GeoJSON data
    features = geojson.loads(geojson_data)["features"]

    # Extract rows from features
    rows = []
    for feature in features:
        properties = feature["properties"]
        geometry = feature["geometry"]
        row = (properties['id'], properties['statename'], properties['lganame'], properties['wardname'], properties['urban'], properties['landuse'], properties['NDMI'], geometry)
        rows.append(row)

    # Define schema for BigQuery table
    schema = [
        bigquery.SchemaField("id", "INTEGER"),
        bigquery.SchemaField("statename", "STRING"),
        bigquery.SchemaField("lganame", "STRING"),
        bigquery.SchemaField("wardname", "STRING"),
        bigquery.SchemaField("urban", "BOOLEAN"),
        bigquery.SchemaField("landuse", "STRING"),
        bigquery.SchemaField("NDMI", "FLOAT"),
        bigquery.SchemaField("geometry", "GEOGRAPHY")
    ]

    # Insert rows into BigQuery table
    errors = bigquery_client.insert_rows(table_id, rows, selected_fields=schema)

    # Check for errors during insertion
    if errors:
        raise RuntimeError(f"Row insert failed: {errors}")
    else:
        print(f"Data uploaded from GCS bucket '{bucket_name}' and file '{destination_blob_path}' to BigQuery table '{table_id}'.")



