"""
AWS Lambda function to generate a presigned URL for uploading CSV files.
"""

import json
import os

import boto3
from botocore.config import Config

BUCKET_NAME = os.getenv("BUCKET_NAME", "dev-sierra-e-bucket")
UPLOAD_PREFIX = "rawCSV/"


def lambda_handler(event, _context):
    """
    Handles API Gateway requests to generate a presigned URL for uploading CSV.

    Args:
        event (dict): The event data received from API Gateway.
        _context: Unused AWS Lambda context parameter.

    Returns:
        dict: API Gateway-compatible response with a presigned URL.
    """
    try:
        print(f"🚀 Starting Upload of Raw CSV to {UPLOAD_PREFIX}")
        print("📩 Event received:", json.dumps(event))

        s3 = boto3.client(
            "s3",
            region_name="ap-southeast-2",
            config=Config(signature_version="s3v4"),
        )

        params = event.get("queryStringParameters", {})
        print("🔍 Query Parameters:", params)

        if not params:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No query parameters found"}),
            }

        file_name = params.get("file")
        if not file_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'file' parameter"}),
            }

        s3_key = f"{UPLOAD_PREFIX}{file_name}"
        print(f"📂 Bucket: {BUCKET_NAME}, File: {s3_key}")

        print(f"🔍 Checking if files exist in {UPLOAD_PREFIX}...")
        existing_files = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=UPLOAD_PREFIX)

        if "Contents" in existing_files:
            for obj in existing_files["Contents"]:
                print(f"🗑 Deleting existing file: {obj['Key']}")
                s3.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])
        else:
            print("✅ No files found in bucket.")

        # Generate pre-signed URL
        presigned_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": s3_key,
                "ContentType": "text/csv",
            },
            ExpiresIn=3600,
        )

        print("🔗 Generated Presigned URL:", presigned_url)
        print("🎉 Upload of Raw CSV completed.")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
                "Access-Control-Allow-Headers": "Content-Type, " +
                "Authorization, file, bucket",
            },
            "body": json.dumps({"URL": presigned_url}),
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal Server Error"})}
