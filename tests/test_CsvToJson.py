import json
from pathlib import Path

import boto3
from moto import mock_aws

from lambda_functions.csvToJson.lambda_function import lambda_handler


def Generate_Mock_event():
    s3_event = {
      "Records": [
        {
          "eventVersion": "2.0",
          "eventSource": "aws:s3",
          "awsRegion": "us-east-1",
          "eventTime": "1970-01-01T00:00:00.000Z",
          "eventName": "ObjectCreated:Put",
          "userIdentity": {
            "principalId": "EXAMPLE"
          },
          "requestParameters": {
            "sourceIPAddress": "127.0.0.1"
          },
          "responseElements": {
            "x-amz-request-id": "EXAMPLE123456789",
            "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/" +
                          "mnopqrstuvwxyzABCDEFGH"
          },
          "s3": {
            "s3SchemaVersion": "1.0",
            "configurationId": "testConfigRule",
            "bucket": {
              "name": "testBucket",
              "ownerIdentity": {
                "principalId": "EXAMPLE"
              },
              "arn": "arn:aws:s3:::testBucket"
            },
            "object": {
              "key": "processedCSV/environmental_risk.csv",
              "size": 1024,
              "eTag": "0123456789abcdef0123456789abcdef",
              "sequencer": "0A1B2C3D4E5F678901"
            }
          }
        }
      ]
    }

    return s3_event


@mock_aws
def test_ExpectedFile():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    Processed_CSV_FILE_PATH = "processedCSV/environmental_risk.csv"
    test_folder = Path(__file__).parent / "TestFilesSorted"
    TEST_FILE_PATH = test_folder / "environmental_risk.csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=Processed_CSV_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with no errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 200


@mock_aws
def test_IncorrectFileSuffix():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    JSON_FILE_PATH = "processedCSV/environmental_risk.json"
    test_folder = Path(__file__).parent / "TestFilesSorted"
    TEST_FILE_PATH = test_folder / "environmental_risk.json"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=JSON_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 500


@mock_aws
def test_FileWrongFileName():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    JSON_FILE_PATH = "processedCSV/incorrectlynamed_risk.csv"
    test_folder = Path(__file__).parent / "TestFilesSorted"
    TEST_FILE_PATH = test_folder / "incorrectlynamed_risk.csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=JSON_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 500


@mock_aws
def test_EmptyCSV():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    JSON_FILE_PATH = "processedCSV/environmental_risk.csv"
    test_folder = Path(__file__).parent / "TestFilesSorted"
    TEST_FILE_PATH = test_folder / "EmptyFile.csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=JSON_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 500


@mock_aws
def test_EmptyBucket():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)

    # test if it goes through with errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 500


@mock_aws
def test_FileMissingColumns():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    Processed_CSV_FILE_PATH = "processedCSV/environmental_risk.csv"
    test_folder = Path(__file__).parent / "TestFilesSorted"
    TEST_FILE_PATH = test_folder / "missingColumns.csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=Processed_CSV_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if the file is missing columns
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 400
    body = json.loads(response["body"]).get("error")
    assert body == "Missing columns"
    missing = json.loads(response["body"]).get("missing")

    # checks if the missing columns are in the list
    assert "pillar" in missing
    assert "category" in missing
    assert "headquarter_country" in missing
