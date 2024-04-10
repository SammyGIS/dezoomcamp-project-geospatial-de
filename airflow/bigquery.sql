-- load ndvi data
CREATE OR REPLACE EXTERNAL TABLE `data-enginerring-zoomcamp.farm_dataset.ndvi`
OPTIONS (
  format = 'CSV',
  uris = ['gs://sammy_project_bucket2024/ndvi/*.csv']);

  -- load ndvi data
CREATE OR REPLACE EXTERNAL TABLE `data-enginerring-zoomcamp.farm_dataset.ndmi`
OPTIONS (
  format = 'CSV',
  uris = ['gs://sammy_project_bucket2024/ndmi/*.csv']);


-- load 
CREATE OR REPLACE EXTERNAL TABLE `data-enginerring-zoomcamp.farm_dataset.farm_boundary2` OPTIONS (
  format="NEWLINE_DELIMITED_JSON",
  json_extension = 'GEOJSON',
  uris = ['gs://sammy_project_bucket2024/farmland_features.json']
);




CREATE OR REPLACE TABLE `data-enginerring-zoomcamp.farm_dataset.farm_info` AS
-- Create or replace the table `farm_info` in the dataset `data-enginerring-zoomcamp.farm_dataset`

SELECT
    farm.id,
    farm.statename,
    farm.lganame,
    farm.wardname,
    farm.urban,
    farm.landuse,
    ROUND(veg_indices.ndvi, 2) AS farm_ndvi, -- Select and round the `ndvi` values to two decimal places
    ROUND(veg_indices.ndmi, 2) AS farm_ndmi, -- Select and round the `ndmi` values to two decimal places
    veg_indices.processed_date,
    farm.geometry
FROM
  `data-enginerring-zoomcamp.farm_dataset.farm_boundary2` as farm

LEFT JOIN
   
   (SELECT DISTINCT ndvi.id, ndvi.ndvi, ndmi.ndmi, ndvi.processed_date
    FROM
        farm_dataset.ndvi AS ndvi -- Alias the `ndvi` table as `ndvi`
    INNER JOIN 
        farm_dataset.ndmi AS ndmi -- Alias the `ndmi` table as `ndmi`
    ON 
        ndvi.id = ndmi.id ) as veg_indices
ON
    farm.id = veg_indices.id

