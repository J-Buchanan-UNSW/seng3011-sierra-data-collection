import json
from pathlib import Path

import boto3
from moto import mock_aws

from lambda_functions.rawToProcessedCSV.lambda_function import lambda_handler


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
            "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisaweso" +
            "me/mnopqrstuvwxyzABCDEFGH"
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
              "key": "rawCSV/",
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
def test_CorrectFileDelim1():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    RAW_CSV_FILE_PATH = "rawCSV/"

    test_folder = Path(__file__).parent / "TestFilesRaw"
    TEST_FILE_PATH = test_folder / "testRaw.csv"

    # inserts the raw test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=RAW_CSV_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with no errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 200
    assert 'Content-Type' in response['headers']
    assert response['headers']['Content-Type'] == 'application/json'


@mock_aws
def test_CorrectFileDelim2():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    RAW_CSV_FILE_PATH = "rawCSV/"
    test_folder = Path(__file__).parent / "TestFilesRaw"
    TEST_FILE_PATH = test_folder / "testDelimiter(,).csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=RAW_CSV_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with no errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 200
    assert 'Content-Type' in response['headers']
    assert response['headers']['Content-Type'] == 'application/json'


@mock_aws
def test_EmptyCSV():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    RAW_CSV_FILE_PATH = "rawCSV/"
    test_folder = Path(__file__).parent / "TestFilesRaw"
    TEST_FILE_PATH = test_folder / "EmptyFile.csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=RAW_CSV_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 500


@mock_aws
def test_MissingMetricCSV():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    RAW_CSV_FILE_PATH = "rawCSV/"
    test_folder = Path(__file__).parent / "TestFilesRaw"
    TEST_FILE_PATH = test_folder / "MissMetricNam.csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
      Bucket='testBucket',
      Key=RAW_CSV_FILE_PATH,
      Body=open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 400
    body = json.loads(response["body"]).get("error")
    assert body == "Missing 'metric_name' column in CSV"


@mock_aws
def test_EmptyBucket():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)

    # test if it goes through with errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 500
