# import unittest
# from lambda_function import lambda_handler

# class TestCSVRetrieval(unittest.TestCase):


#     def testget(self):

import base64
import json
import pytest
import os
from moto import mock_aws
import boto3
from pathlib import Path

from lambda_functions.rawToProcessedCSV.lambda_function import lambda_handler

# @pytest.fixture
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
        "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
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
#test expected file with correct suffix, using raw delimiter |
@mock_aws
def test_CorrectFileDelim1():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    RAW_CSV_FILE_PATH = "rawCSV/"

    TEST_FILE_PATH = Path(__file__).parent/"TestFilesRaw"/"testRaw.csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
    Bucket='testBucket',
    Key = RAW_CSV_FILE_PATH,
    Body = open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with no errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 200

#test expected file with correct suffix, using sorted delimiter ,
@mock_aws
def test_CorrectFileDelim2():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    RAW_CSV_FILE_PATH = "rawCSV/"

    TEST_FILE_PATH = Path(__file__).parent/"TestFilesRaw"/"testDelimiter(,).csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
    Bucket='testBucket',
    Key = RAW_CSV_FILE_PATH,
    Body = open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with no errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 200

    #test expected file with correct suffix, using sorted delimiter ,
@mock_aws
def test_EmptyCSV():
    # generates a mock s3
    s3_client = boto3.client('s3')
    testBucketName = 'testBucket'
    s3_client.create_bucket(Bucket=testBucketName)
    RAW_CSV_FILE_PATH = "rawCSV/"

    TEST_FILE_PATH = Path(__file__).parent/"TestFilesRaw"/"EmptyFile.csv"

    # inserts the sorted environmental_risk test file into the mock S3

    s3_client.put_object(
    Bucket='testBucket',
    Key = RAW_CSV_FILE_PATH,
    Body = open(TEST_FILE_PATH, "rb")
    )
    # test if it goes through with errors
    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 500

# #test incorrect file with wrong suffix
# @mock_aws
# def test_IncorrectFileSuffix():
#     # generates a mock s3
#     s3_client = boto3.client('s3')
#     testBucketName = 'testBucket'
#     s3_client.create_bucket(Bucket=testBucketName)
#     JSON_FILE_PATH = "processedCSV/environmental_risk.json"
#     TEST_FILE_PATH = Path(__file__).parent/"TestFiles"/"environmental_risk.json"

#     # inserts the sorted environmental_risk test file into the mock S3

#     s3_client.put_object(
#     Bucket='testBucket',
#     Key = JSON_FILE_PATH,
#     Body = open(TEST_FILE_PATH, "rb")
#     )
#     # test if it goes through with errors
#     response = lambda_handler(event=Generate_Mock_event(), _context=None)
#     assert response['statusCode'] == 500

# #test file is named wrong

# @mock_aws
# def test_FileWrongFileName():
#     # generates a mock s3
#     s3_client = boto3.client('s3')
#     testBucketName = 'testBucket'
#     s3_client.create_bucket(Bucket=testBucketName)
#     JSON_FILE_PATH = "processedCSV/incorrectlynamed_risk.csv"
#     TEST_FILE_PATH = Path(__file__).parent/"TestFiles"/"incorrectlynamed_risk.csv"

#     # inserts the sorted environmental_risk test file into the mock S3

#     s3_client.put_object(
#     Bucket='testBucket',
#     Key = JSON_FILE_PATH,
#     Body = open(TEST_FILE_PATH, "rb")
#     )
#     # test if it goes through errors
#     response = lambda_handler(event=Generate_Mock_event(), _context=None)
#     assert response['statusCode'] == 500