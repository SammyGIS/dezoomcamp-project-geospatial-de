terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.51.0"
    }
  }
}

provider "google" {
  credentials = file("./keys/data-enginerring-zoomcamp-b8719aa4a43e.json")
  project     = var.project
  region      = var.region
}


## create google cloud compute
resource "google_compute_instance" "default" {
  name         = "my-instance"
  machine_type = "e2-standard-4"
  zone         = var.region
  project      = var.project

  boot_disk {
    initialize_params {
      image = "ubuntu-2004-lts"
      size   = 100
      labels = {
        my_label = "project"
      }
    }
  }

  network_interface {
    network = "default"

    access_config {
      # Ephemeral public IP
    }
  }

  metadata_startup_script = "${file("./install_docker.sh")}"
  
  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = "farm-watch-project@data-enginerring-zoomcamp.iam.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }
}


# create google bucket
resource "google_storage_bucket" "data_lake" {
  name     = var.bucket
  project  = var.project
  location = var.location
}

# create bigquery datasets
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.dataset
  project    = var.project
  location   = var.location
}


# create google bucket to store the function
resource "google_storage_bucket" "function_bucket" {
  name     = var.func_bucket
  project  = var.project
  location = var.location
}



# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "ndvi_source" {
    type        = "zip"
    source_dir  = "../src"
    output_path = "./tmp/ndvi_function.zip"
}


# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "zipped_data" {
    source = data.archive_file.ndvi_source.output_path
    content_type = "application/zip"

    # Append to the MD5 checksum of the files's content
    # to force the zip to be updated as soon as a change occurs
    name  = "src-${data.archive_file.ndvi_source.output_md5}.zip"
    bucket = google_storage_bucket.function_bucket.name

    # Dependencies are automatically inferred so these lines can be deleted
    depends_on   = [
        google_storage_bucket.function_bucket,  # declared in `storage.tf`
        data.archive_file.ndvi_source
    ]
}

# Create the Cloud function 
resource "google_cloudfunctions_function" "function" {
    name                  = "gee_ndvi_function"
    runtime               = "python37"  # of course changeable

    # Get the source code of the cloud function as a Zip compression
    source_archive_bucket = google_storage_bucket.function_bucket.name
    source_archive_object = google_storage_bucket_object.zipped_data.name

    # Must match the function name in the cloud function `main.py` source code
    entry_point           = "hello_gcs"
    

    # Dependencies are automatically inferred so these lines can be deleted
    depends_on            = [
        google_storage_bucket.function_bucket,  # declared in `storage.tf`
        google_storage_bucket_object.zip
    ]
}