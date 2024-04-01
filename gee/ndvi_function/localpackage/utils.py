import multiprocessing
from shapely.geometry import MultiPolygon
import pandas as pd
import geopandas as gpd
import json
import ee
from google.cloud import storage

# Define a helper function to put the GeoDataFrame in the right format for constructing an EE object
def shp_to_ee_fmt(geodf):
    combine_poly = geodf.dissolve('landuse')
    data = json.loads(combine_poly.to_json())
    return data['features'][0]['geometry']['coordinates']

def shapely_to_ee_feature(geom, tolerance=0.01):
    """Converts Shapely geometry to Earth Engine Feature."""
    # Simplify the geometry if it's a Polygon or MultiPolygon
    if geom.geom_type == 'Polygon':
        geom = geom.simplify(tolerance)
    elif geom.geom_type == 'MultiPolygon':
        simplified_geoms = [sub_geom.simplify(tolerance) for sub_geom in geom.geoms]
        geom = MultiPolygon(simplified_geoms)
    else:
        raise ValueError("Unsupported geometry type")

    # Convert the simplified geometry to EE Feature
    if geom.geom_type == 'MultiPolygon':
        coords = [list(sub_geom.exterior.coords) for sub_geom in geom.geoms]
    else:
        coords = list(geom.exterior.coords)
    return ee.Feature(ee.Geometry.Polygon(coords))

def get_ee_features(gdf):
    """Converts GeoDataFrame geometries to Earth Engine Features."""
    return [shapely_to_ee_feature(row.geometry) for idx, row in gdf.iterrows()]

# Function to process each subset and compute mean NDVI
def zonal_stats_mean(image, scale, subset):
    features = ee.FeatureCollection(get_ee_features(subset))  # Convert to EE Features
    zone_stats = image.reduceRegions(
        collection=features, reducer=ee.Reducer.mean(),
          scale=scale ,crs='EPSG:4326'
    ).getInfo()
    zone_stats_gdf = gpd.GeoDataFrame.from_features(zone_stats['features'], crs='EPSG:4326')
    return zone_stats_gdf

def process_zonal_stats_chunks(image, scale, farmland_gdf, chunk_size):    
    # Split farmland boundaries into subsets
    subsets = [farmland_gdf.iloc[i:i+chunk_size].copy() for i in range(0, len(farmland_gdf), chunk_size)]
    
    # Initialize a multiprocessing pool
    pool = multiprocessing.Pool()
    
    # Process subsets in parallel and collect results
    zone_stats_gdfs = pool.starmap(zonal_stats_mean, [(image, scale, subset) for subset in subsets])
    
    # Close the multiprocessing pool
    pool.close()
    pool.join()
    
    # Concatenate all GeoDataFrames in the list into a single GeoDataFrame
    final_zone_stats_gdf = pd.concat(zone_stats_gdfs, ignore_index=True)
    
    return final_zone_stats_gdf

def upload_dataframe_to_gcs(dataframe: pd.DataFrame, bucket_name: str, destination_blob_path: str):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_path)

    # Convert DataFrame to CSV bytes
    csv_bytes = dataframe.to_csv(index=False).encode('utf-8')  # Consider compression if needed

    # Upload DataFrame bytes to GCS
    blob.upload_from_string(csv_bytes)

    print(f'DataFrame uploaded to GCS: gs://{bucket_name}/{destination_blob_path}')



