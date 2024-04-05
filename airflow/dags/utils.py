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

def geodataframe_to_json_dict(geojson_gdf):
    try:
        # Convert GeoDataFrame to GeoJSON string
        geojson_str = geojson_gdf.to_json()

        # Parse GeoJSON string to Python dictionary
        data = json.loads(geojson_str)

        # Check if the GeoJSON is a FeatureCollection
        if data['type'] == 'FeatureCollection':
            features = data['features']
            return features
        else:
            print("The GeoDataFrame does not contain a FeatureCollection.")
            return None

    except Exception as e:
        print("Error while converting GeoDataFrame to JSON dictionary:", e)
        return None

def upload_features_to_bigquery(table_id, bucket_name, blob_path, json_credentials_path):
    try:
        # Initialize BigQuery and GCS clients using service account credentials
        bigquery_client = bigquery.Client.from_service_account_json(json_credentials_path)

        # Download GeoDataFrame from GCS
        geojson_gdf = download_geodataframe_from_gcs(bucket_name, blob_path)
        
        # Convert GeoDataFrame to a list of dictionaries in JSON format
        json_features = geodataframe_to_json_dict(geojson_gdf)
        
        # Upload JSON features to BigQuery (Append to existing table)
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        # Convert features to newline-delimited JSON string
        json_string = '\n'.join(json.dumps(feature) for feature in json_features)

        job = bigquery_client.load_table_from_json(
            json_rows=json_string,
            destination=table_id,
            job_config=job_config,
        )

        # Wait for the job to complete
        job.result()

        print(f"All features uploaded to BigQuery table {table_id} successfully.")
    
    except Exception as e:
        print(f"Error uploading features to BigQuery: {e}")

