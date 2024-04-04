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

resource "google_compute_instance" "compute-instance" {
  name               = "my-instance"
  machine_type       = var.machine_type
  zone               = var.region
  project             = var.project

  boot_disk {
    initialize_params {
      image = "ubuntu-2004-lts"
      size  = 100
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

  metadata_startup_script = file("./install_docker.sh")

  service_account {
    email  = var.service_account_email  # Assuming this variable holds the service account email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

resource "google_storage_bucket" "data_lake" {
  name     = var.bucket
  project  = var.project
  location = var.location
  force_destroy = true
}

resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.dataset
  project    = var.project
  location   = var.location
}

resource "google_storage_bucket" "function_bucket" {
  name     = var.func_bucket
  project  = var.project
  location = var.location
  force_destroy = true
}

data "archive_file" "ndvi_source" {
  type        = "zip"
  source_dir  = "${path.module}/ndvi_function"
  output_path = "${path.module}/ndvi_function.zip"
}

resource "google_storage_bucket_object" "zipped_code" {
  source       = data.archive_file.ndvi_source.output_path
  content_type = "application/zip"

  name   = "src-${data.archive_file.ndvi_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "gee_ndvi_function" {
  name     = "gee_ndvi_function"
  runtime = "python39"
  region   = var.region_function
  
  # Set the timeout duration here
  timeout = 300  # 5 minutes

  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.zipped_code.name

  available_memory_mb = 4098

  trigger_http = true
  entry_point  = "main"
  environment_variables = {
    # Use a more descriptive variable name here
    deployment_name = "terraform"
  }
}

resource "google_cloud_scheduler_job" "automate_ndvi" {
  name               = "gee_ndvi_function"
  description        = "get ndvi data every 7 days"
  region              = var.region_function
  schedule           = "0/2 * * * *"
  time_zone = "Africa/Lagos"
  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions_function.gee_ndvi_function.https_trigger_url
    oidc_token {
      service_account_email = var.service_account_email
    }
  }
}



data "archive_file" "ndmi_source" {
  type        = "zip"
  source_dir  = "${path.module}/ndmi_function"
  output_path = "${path.module}/ndmi_function.zip"
}

resource "google_storage_bucket_object" "ndmi_zipped_code" {
  source       = data.archive_file.ndmi_source.output_path
  content_type = "application/zip"

  name   = "src-${data.archive_file.ndmi_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "gee_ndmi_function" {
  name     = "gee_ndmi_function"
  runtime = "python39"
  region   = var.region_function
  
  # Set the timeout duration here
  timeout = 300  # 5 minutes

  source_archive_bucket = google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.ndmi_zipped_code.name

  available_memory_mb = 4098

  trigger_http = true
  entry_point  = "main"
  environment_variables = {
    # Use a more descriptive variable name here
    deployment_name = "terraform"
  }
}

resource "google_cloud_scheduler_job" "automate_ndmi" {
  name               = "gee_ndmi_function"
  description        = "get ndmi data every 7 days"
  region              = var.region_function
  schedule           = "0/2 * * * *"
  time_zone = "Africa/Lagos"
  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions_function.gee_ndmi_function.https_trigger_url
    oidc_token {
      service_account_email = var.service_account_email
    }
  }
}
