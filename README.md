# FarmWatch: Monitoring Agricultural Lands with Satellite Imagery

### FarmWatch Pipeline Overview
FarmWatch is an innovative pipeline dedicated to monitoring agricultural lands through the integration of satellite imagery analysis and geospatial data processing. Leveraging the wealth of digitized farmland data available on OpenStreetMap (OSM), FarmWatch focuses on Nigeria, utilizing OSM's collaborative mapping platform to continuously fetch and incorporate newly digitized farm land features. OpenStreetMap allows contributors to generate detailed geospatial data, making it a valuable resource for tracking changes in land use and land cover over time.

Following the extraction and transformation of farm land data from OSM, FarmWatch employs Google Cloud Functions to harness the latest satellite imagery captured within the past 7 days. Leveraging Google Earth Engine's capabilities, key vegetation indices such as the Normalized Difference Vegetation Index (NDVI) and Normalized Difference Moisture Index (NDMI) are computed periodically (More data can be added to this later on). This data is then stored securely in Google Cloud Storage for efficient management and retrieval.

Subsequently, the processed data is modeled and analyzed using BigQuery. To facilitate intuitive visualization and analysis, FarmWatch incorporates the use of Carto Dashboard. This powerful tool offers interactive spatial visualization capabilities, empowering users to explore and interpret geospatial data effortlessly.

### Tools Utilized
- **Google Compute Engine**: Provides scalable computing resources to execute processing tasks efficiently.
- **Docker**: Ensures consistent and reproducible environment configurations across various systems.
- **Airflow**: Orchestrates the pipeline's workflow, automating task execution and scheduling.
- **Google Scheduler**: Triggers periodic updates of the pipeline, ensuring timely data processing.
- **Terraform**: Manages infrastructure setup and configuration, enhancing deployment efficiency.
- **Google Cloud Function**: Executes specific tasks triggered by events, enhancing pipeline automation.
- **BigQuery**: Stores and analyzes large datasets, facilitating advanced querying and insights generation.
- **Google Cloud Storage**: Safely stores data assets and intermediate results, ensuring data integrity and accessibility.
- **Carto Dashboard**: Offers intuitive spatial visualization capabilities, enabling interactive data exploration and analysis.
- **Google Earth Engine**: Processes satellite imagery and computes key vegetation indices, providing valuable insights into agricultural conditions.

## Architecture Diagram
![alt text](architecture.jpg)

## Dashboard
![alt text](dashboard.jpg)
https://clausa.app.carto.com/map/262e9e12-4502-4415-ae4d-c8696a45dd00


### Pipeline Architecture
1. **OSM Data**: Fetches farmland data from OSM to establish baseline information.
2. **Data Transformation and Enrichment**: Utilizes Airflow to clean and augment OSM data with administrative details for better analysis.
3. **Data Storage**: Stores processed data and satellite imagery in Google Cloud Storage for efficient retrieval and management.
4. **Satellite Imagery Acquisition**: Utilizes Google Earth Engine to acquire Sentinel satellite imagery for specified areas.
5. **NDVI and NDMI Calculation**: Computes NDVI and NDMI from satellite imagery to assess vegetation health and moisture levels.
6. **Zonal Statistics Calculation**: Determines average NDVI and NDMI values for each farmland polygon.
7. **Data Modeling**: Uploads enriched data to BigQuery for storage, querying, and modeling purposes.
8. **Dashboard Visualization**: Leverages Carto Dashboard to visualize spatial data and provide insights for monitoring agricultural lands.

### Key Components
- **Automated Data Processing**: Leveraging Airflow for task orchestration ensures timely execution of data processing steps.
- **Cloud-Based Storage and Compute**: Utilizing Google Cloud Platform services enables scalable and cost-effective storage and computation.
- **Satellite Imagery Analysis**: Extracting NDVI and NDMI indices provides valuable insights into crop health and moisture levels.
- **Big Data Analytics**: Leveraging BigQuery allows for efficient querying and analysis of large datasets.
- **Interactive Dashboard**: Utilizing Carto Dashboard facilitates visualization of spatial data, aiding in monitoring and decision-making.

### References
https://medium.com/cloud-native-daily/deploy-cloud-functions-on-gcp-with-terraform-c6026be9d645
https://medium.com/geekculture/setup-gcp-cloud-functions-triggering-by-cloud-schedulers-with-terraform-1433fbf1abbe
https://cloud.google.com/bigquery/docs/geospatial-data#:~:text=Loading%20GeoJSON%20geometry%20data&text=To%20load%20this%20type%20of,data%20as%20a%20STRING%20value
https://mihaibojin.medium.com/deploy-and-configure-google-compute-engine-vms-with-terraform-f6b708b226c1
https://www.youtube.com/watch?v=49C7eE_mhm4
https://id.cloud-ace.com/using-geojson-in-bigquery-for-geospatial-analytics/