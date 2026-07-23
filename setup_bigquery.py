# Copyright 2026 Google LLC
# Licensed under the Apache License, Version 2.0

import os
import logging
from google.cloud import bigquery
from google.cloud import storage
from google.api_core.exceptions import Conflict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "vertexsearch-447722")
REGION = "us-central1"
BUCKET_NAME = "slice_n_rise_scans"
DATASET_ID = "slice_n_rise"
TABLE_ID = "pizza_evaluations"

def setup_gcs():
    """Creates the GCS bucket for Slice_n_Rise if it doesn't exist."""
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    try:
        bucket.storage_class = "STANDARD"
        new_bucket = storage_client.create_bucket(bucket, location=REGION)
        logger.info(f"Created bucket {new_bucket.name} in {new_bucket.location}")
    except Conflict:
        logger.info(f"Bucket {BUCKET_NAME} already exists.")
    except Exception as e:
        logger.error(f"Error creating bucket: {e}")

def setup_bigquery():
    """Creates the BigQuery dataset and table for Slice_n_Rise if they don't exist."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # 1. Create Dataset
    dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = REGION
    try:
        dataset = bq_client.create_dataset(dataset, timeout=30)
        logger.info(f"Created dataset {dataset.project}.{dataset.dataset_id}")
    except Conflict:
        logger.info(f"Dataset {DATASET_ID} already exists.")
    except Exception as e:
        logger.error(f"Error creating dataset: {e}")

    # 2. Create Table
    table_ref = dataset_ref.table(TABLE_ID)
    schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("store_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("pizza_profile_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("overall_grade", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("gcs_uri", "STRING", mode="NULLABLE"),
        # Machine ratings
        bigquery.SchemaField("edge_height", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("edge_width", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("center_volume", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("top_color", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("bottom_color", "INTEGER", mode="NULLABLE"),
        # Human corrected ratings
        bigquery.SchemaField("human_edge_height", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("human_edge_width", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("human_center_volume", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("human_top_color", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("human_bottom_color", "INTEGER", mode="NULLABLE"),
        # Validation status
        bigquery.SchemaField("verified", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("user_corrected", "BOOLEAN", mode="NULLABLE"),
    ]
    table = bigquery.Table(table_ref, schema=schema)
    try:
        table = bq_client.create_table(table)
        logger.info(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Conflict:
        logger.info(f"Table {TABLE_ID} already exists.")
    except Exception as e:
        logger.error(f"Error creating table: {e}")

if __name__ == "__main__":
    logger.info("Starting Slice_n_Rise infrastructure setup...")
    setup_gcs()
    setup_bigquery()
    logger.info("Setup process complete.")
