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


def upload_geojson_to_bigquery(table_id, bucket_name, blob_path, json_credentials_path):
    # Initialize BigQuery and GCS clients using service account credentials
    bigquery_client = bigquery.Client.from_service_account_json(json_credentials_path)
    storage_client = storage.Client.from_service_account_json(json_credentials_path)
    
    # Get the GeoJSON data from GCS
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    geojson_data = blob.download_as_string().decode('utf-8')
    geojson_lines = geojson_data.splitlines()

    # Define schema for BigQuery table
    schema = [
        bigquery.SchemaField("id", "INTEGER"),
        bigquery.SchemaField("statename", "STRING"),
        bigquery.SchemaField("lganame", "STRING"),
        bigquery.SchemaField("wardname", "STRING"),
        bigquery.SchemaField("urban", "BOOLEAN"),
        bigquery.SchemaField("landuse", "STRING"),
        bigquery.SchemaField("NDMI", "FLOAT"),  # Assuming NDMI is a float value
        bigquery.SchemaField("geometry", "GEOGRAPHY")
    ]

    # Load GeoJSON lines into BigQuery
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    job = bigquery_client.load_table_from_json(
        geojson_lines, table_id, job_config=job_config
    )

    # Wait for the job to complete
    job.result()

    print(f"Data uploaded from GCS bucket '{bucket_name}' and file '{blob_path}' to BigQuery table '{table_id}'.")


