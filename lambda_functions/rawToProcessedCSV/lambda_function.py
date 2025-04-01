"""
AWS Lambda function to process a CSV file from S3, filter specific metrics,
and save the processed file back to S3.
"""

from datetime import datetime
from io import TextIOWrapper
import json
import boto3
import pandas as pd

# Constants
UPLOAD_PREFIX = "processedCSV/"
UPLOAD_FILENAME = "environmental_risk"
TZS = "GMT+11"

# Current timestamp
now = datetime.now()
date_time = now.strftime("%Y-%m-%d %H:%M:%S.%f")

# AWS S3 Client
s3_client = boto3.client("s3")


def lambda_handler(event, _context):
    """
    AWS Lambda handler function that processes a CSV file from S3, filters
    specific metrics, and stores the processed CSV back in S3.

    Parameters:
        event (dict): The AWS Lambda event object, triggered by an S3 upload.
        context (object): The AWS Lambda runtime context.

    Returns:
        dict: A response dictionary containing the statusCode and body message.
    """
    try:
        print("🚀 Starting CSV processing...")
        print("📩 Event received:", json.dumps(event))

        # Retrieve bucket name and file key
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"]
        print(f"🗂 File detected: s3://{bucket}/{key}")

        # Check and delete existing processed files
        print(f"🔍 Checking for existing files in {UPLOAD_PREFIX}")
        existing_files = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=UPLOAD_PREFIX)

        if "Contents" in existing_files:
            for obj in existing_files["Contents"]:
                print(f"🗑 Deleting existing file: {obj['Key']}")
                s3_client.delete_object(Bucket=bucket, Key=obj["Key"])
        else:
            print("✅ No existing processed files found.")

        # Download CSV from S3
        print("📥 Fetching CSV from S3...")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        data_to_string = TextIOWrapper(response["Body"], encoding="utf-8")

        # Read CSV into DataFrame
        print("📊 Loading CSV into DataFrame...")
        csv_data_frame = pd.read_csv(
            data_to_string,
            sep=r"[,\|]",
            engine="python")

        sample_lines = data_to_string.read(2048)

        if "|" in sample_lines and "," in sample_lines:
            print("⚠️ Warning: CSV contains both ',' and '|' delimiters.")

        # Reset stream position
        data_to_string.seek(0)

        # Log column names to check if "metric_name" exists
        print("🧐 CSV Columns Found:", csv_data_frame.columns.tolist())

        # Define filter list
        csv_data_frame_filter = [
            "CO2DIRECTSCOPE1", "CO2INDIRECTSCOPE2", "CO2INDIRECTSCOPE3",
            "CO2_NO_EQUIVALENTS", "NOXEMISSIONS", "SOXEMISSIONS",
            "VOCEMISSIONS",
            "WASTETOTAL", "HAZARDOUSWASTE", "PARTICULATE_MATTER_EMISSIONS",
            "AIRPOLLUTANTS_DIRECT", "AIRPOLLUTANTS_INDIRECT",
            "NATURAL_RESOURCE_USE_DIRECT", "WATERWITHDRAWALTOTAL",
            "WATER_USE_PAI_M10", "TOXIC_CHEMICALS_REDUCTION",
            "VOC_EMISSIONS_REDUCTION", "N_OXS_OX_EMISSIONS_REDUCTION"
        ]

        # Log unique metric names before filtering
        if "metric_name" in csv_data_frame.columns:
            unique_metric_names = (
                csv_data_frame["metric_name"]
                .unique()
                .tolist()
            )
            print(f"🔍 Unique metric_name values in CSV: {unique_metric_names}")
        else:
            print("❌ 'metric_name' column not found! Check CSV format.")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing 'metric_name' column in CSV"})
            }

        # Filter data based on metric_name
        filtered_data_frame = csv_data_frame[
            csv_data_frame["metric_name"].isin(csv_data_frame_filter)
        ]
        print("✅ Filtered DataFrame contains " +
              f"{len(filtered_data_frame)} rows.")

        # Save final processed CSV to S3
        print("📤 Saving final processed CSV to S3...")
        csv_output = filtered_data_frame.to_csv(index=False)
        s3_client.put_object(
            Bucket=bucket,
            Key=f"{UPLOAD_PREFIX}{UPLOAD_FILENAME}.csv",
            Body=csv_output,
        )

        print("🎉 CSV processing completed successfully.")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "Success"}),
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
