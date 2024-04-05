import geopandas as gpd
from google.cloud import storage
from google.cloud import bigquery
import json
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



def create_geo_table_bquery(table_id):
    # Construct a BigQuery client object.
    client = bigquery.Client.from_service_account_json(json_credentials_path)

    schema = [
        bigquery.SchemaField("id", "INTEGER"),
        bigquery.SchemaField("statename", "STRING"),
        bigquery.SchemaField("lganame", "STRING"),
        bigquery.SchemaField("wardname", "STRING"),
        bigquery.SchemaField("urban", "STRING"),
        bigquery.SchemaField("landuse", "STRING"),
        bigquery.SchemaField("geometry", "GEOGRAPHY")
    ]

    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table)  # Make an API request.
    print(
        "Created table {}.{}.{}".format(table.project, table.dataset_id, table.table_id)
    )

# def upload_features_to_bigquery(table_id, bucket_name, blob_path):
#     # Initialize BigQuery and GCS clients using service account credentials
#     bigquery_client = bigquery.Client.from_service_account_json(json_credentials_path)
#     create_geo_table_bquery(table_id)
#     geojson_gdf = download_geodataframe_from_gcs(bucket_name, blob_path)

#     # Loop through each feature in the GeoDataFrame and upload it to BigQuery
#     for feature in geojson_gdf.iterfeatures():
#         # Convert feature to GeoJSON
#         geojson_feature = json.dumps(feature)

#         # Upload JSON feature to BigQuery
#         job_config = bigquery.LoadJobConfig(
#             source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
#             autodetect=True,
#         )
#         job = bigquery_client.load_table_from_json(
#             json_rows=geojson_feature,
#             destination=table_id,
#             job_config=job_config,
#         )

#         # Wait for the job to complete
#         job.result()

#     print(f"All features uploaded to BigQuery table {table_id} successfully.")
