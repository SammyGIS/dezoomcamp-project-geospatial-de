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


# create google bucket
resource "google_storage_bucket" "function_bucket" {
  name     = var.func_bucket
  project  = var.project
  location = var.location
}


# create bigquery datasets
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.dataset
  project    = var.project
  location   = var.location
}

resource "google_cloudfunctions_function" "gee_functions" {
  name                   = "gee_functions"
  description            = "My function"
  project                = "data-enginerring-zoomcamp"
  runtime                 = "python39"
  available_memory_mb     = 128
  source_archive_bucket = google_storage_bucket.data_lake.name  # Reference the bucket resource
  trigger_http           = true
  entry_point            = "helloGET"
}
