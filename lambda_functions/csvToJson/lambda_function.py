"""
AWS Lambda function to convert a CSV file from S3 into JSON format and store
it back in S3.

Steps:
1. Detects new CSV file in S3 bucket via event trigger.
2. Deletes any previously processed JSON files in the target folder.
3. Reads and processes the CSV file.
4. Converts the data into a structured JSON format.
5. Uploads the new JSON file back to S3.

Author: Team Sierra
Date: 23/03/2025
"""

import csv
import json
from datetime import datetime
from io import TextIOWrapper
import boto3


def lambda_handler(event, _context):
    """
    AWS Lambda function to convert a CSV file from S3 to a JSON format
    and store it back in S3.

    Parameters:
        event (dict): Event data containing S3 bucket and object key.
        context (object): AWS Lambda runtime context.

    Returns:
        dict: HTTP response indicating success or failure.
    """

    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    TZS = 'GMT+11'

    s3_client = boto3.client('s3')

    UPLOAD_PREFIX = "processedJSON/"

    try:
        print("🚀 Starting Conversion of CSV to JSON and storing in",
              UPLOAD_PREFIX)
        print("📩 Event received:", json.dumps(event, indent=2))

        # Retrieves bucket name and file key
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        if "social" in key.lower():
            risk_type = "social"
        elif "governance" in key.lower():
            risk_type = "governance"
        else:
            risk_type = "environmental"
            print("⚠️ Unknown risk type. Defaulting to environmental.")

        filename = f"{risk_type}.json"

        print(f"🔍 Checking if files exist in {UPLOAD_PREFIX}...")

        exist_file = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=UPLOAD_PREFIX)

        if filename in [obj["Key"] for obj in exist_file.get("Contents", [])]:
            print(f"🗑 Deleting existing file: {filename}")
            s3_client.delete_object(Bucket=bucket, Key=filename)
        else:
            print("✅ No existing file found with that name.")

        print(f"📥 Downloading file from S3: {key}")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        data_to_string = TextIOWrapper(response['Body'], encoding='utf-8')

        # Standardized JSON format
        json_header = {
            "data_source": "ClarityAI_Dataset",
            "dataset_type": "Environmental_Risk",
            "dataset_id": "https://ap-southeast-2.console.aws.amazon.com" +
            "/s3/buckets/sierra-e-bucket",
            "time_object": {"timestamp": date_time, "timezone": TZS},
            "events": []
        }

        print("📊 Reading CSV file...")
        reader = csv.DictReader(data_to_string, delimiter=',')

        # Check if all expected columns are present
        expected_columns = {
            "reported_date", "company_name", "perm_id", "data_type",
            "disclosure",
            "metric_description", "metric_name", "metric_unit", "metric_value",
            "metric_year", "nb_points_of_observations", "metric_period",
            "provider_name", "pillar", "headquarter_country", "category"
        }

        actual_columns = set(reader.fieldnames)
        missing_columns = expected_columns - actual_columns
        if missing_columns:
            print(f"❌ Missing columns in CSV: {missing_columns}")
            return {"statusCode": 400, "body": json.dumps({
                "error": "Missing columns",
                "missing": list(missing_columns)})}
        print("✅ All expected columns are present.")

        # Debug: Print unique `metric_name` values
        metric_names = set()
        events_added = 0

        for row in reader:
            metric_name = row.get('metric_name', '').strip()
            metric_names.add(metric_name)  # Collect unique metric names

            event = {
                "time_object": {
                    "timestamp": row['reported_date'],
                    "duration": 1,
                    "duration_unit": "day",
                    "timezone": TZS
                },
                "event_type": "ESG data",
                "attribute": {
                    "company_name": row['company_name'],
                    "perm_id": row['perm_id'],
                    "data_type": row['data_type'],
                    "disclosure": row['disclosure'],
                    "metric_description": row['metric_description'],
                    "metric_name": metric_name,
                    "metric_unit": row['metric_unit'],
                    "metric_value": row['metric_value'],
                    "metric_year": row['metric_year'],
                    "nb_points_of_observations":
                    row['nb_points_of_observations'],
                    "metric_period": row['metric_period'],
                    "provider_name": row['provider_name'],
                    "pillar": row['pillar'],
                    "headquarter_country": row['headquarter_country']
                }
            }
            json_header["events"].append(event)
            events_added += 1

        print(f"📈 Unique metric names in CSV: {list(metric_names)}")
        print(f"✅ Total events processed: {events_added}")

        # Upload the converted JSON file
        json_output = json.dumps(json_header, indent=4)
        print("📤 Uploading JSON file to S3: " +
              f"{UPLOAD_PREFIX}{filename}")
        s3_client.put_object(
            Bucket=bucket,
            Key=f"{UPLOAD_PREFIX}{filename}",
            Body=json_output
        )

        print("🎉 Conversion of CSV to JSON completed successfully!")

        return {"statusCode": 200, "body": json.dumps({
            "status": "Success",
            "events_added": events_added})}

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Unexpected Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal Server Error"})}
