"""
AWS Lambda function to process a CSV file from S3, filter specific metrics,
and save the processed file back to S3.
"""

from io import StringIO
import json
import boto3
import pandas as pd
import csv
from botocore.exceptions import ClientError


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

    # Constants
    upload_prefix = "processedCSV/"
    upload_filename = "environmental_risk"

    # AWS S3 Client
    s3_client = boto3.client("s3")
    # New data uploaded and exisitng file to be amended
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    new_key = event["Records"][0]["s3"]["object"]["key"]
    existing_key = f"{upload_prefix}{upload_filename}.csv"

    try:
        print("🚀 Starting CSV processing...")
        print("📩 Event received:", json.dumps(event))

        # Get the data from the newly uploaded raw CSV file
        new_csv = s3_client.get_object(Bucket=bucket, Key=new_key)
        raw_bytes = new_csv["Body"].read()
        raw_str = raw_bytes.decode("utf-8")

        # Get the delimiter
        try:
            sample = raw_str[:1024]
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        new_data = pd.read_csv(StringIO(raw_str), sep=delimiter)

        print(f"🔍 Fetching existing files in {upload_prefix}")
        try:
            exist_csv = s3_client.get_object(Bucket=bucket, Key=existing_key)
            exist_data = pd.read_csv(exist_csv["Body"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                print("✅ No existing processed file found.")
                exist_data = pd.DataFrame()
            else:
                raise

        # Combine and deduplicate data
        combined = pd.concat([exist_data, new_data], ignore_index=True)
        combined.drop_duplicates(inplace=True)

        # Log column names to check if "metric_name" exists
        print("🧐 Combined CSV Columns:", combined.columns.tolist())

        # Define filter list
        metric_filter = [
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
        if "metric_name" not in combined.columns:
            print("❌ 'metric_name' column not found! Check CSV format.")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing 'metric_name' column in CSV"})
            }

        # Filter data based on metric_name
        unique_metrics = combined["metric_name"].unique().tolist()
        print(f"🔍 Unique metric_name values: {unique_metrics}")

        processed_df = combined[combined["metric_name"].isin(metric_filter)]
        print(f"✅ Filtered DataFrame rows: {len(processed_df)}")

        # Save final processed CSV to S3
        out_buffer = StringIO()
        processed_df.to_csv(out_buffer, index=False)
        s3_client.put_object(
            Bucket=bucket,
            Key=existing_key,
            Body=out_buffer.getvalue(),
            ContentType="text/csv",
        )
        print("🎉 CSV processing completed and amenended successfully.")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status":
                "CSV processed and amended successfully"}),
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
