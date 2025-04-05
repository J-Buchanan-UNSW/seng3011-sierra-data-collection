import json
from moto import mock_aws
import boto3

from lambda_functions.uploadRawCSV.lambda_function import lambda_handler


def Generate_Mock_event():
    s3_event = {
        "queryStringParameters": {
            "file": "test.csv"
        }
    }
    return s3_event


def NoFileParamEvent():
    s3_event = {
        "queryStringParameters": {
            "file": ""
        }
    }
    return s3_event


def NoQueryParamEvent():
    s3_event = {
        "queryStringParameters": {
        }
    }
    return s3_event


@mock_aws
def test_Generate_Mock_s3():
    s3_client = boto3.client('s3')
    testBucketName = 'dev-sierra-e-bucket'
    s3_client.create_bucket(Bucket=testBucketName)

    response = lambda_handler(event=Generate_Mock_event(), _context=None)
    assert response['statusCode'] == 200
    # check presigned url is generated
    presigned_URL = json.loads(response["body"]).get("URL")
    assert presigned_URL is not None


@mock_aws
def test_NoQueryParam():
    s3_client = boto3.client('s3')
    testBucketName = 'dev-sierra-e-bucket'
    s3_client.create_bucket(Bucket=testBucketName)

    response = lambda_handler(event=NoQueryParamEvent(), _context=None)
    # checks if the right error was passed
    assert response['statusCode'] == 400
    body = json.loads(response["body"]).get("error")
    assert body == "No query parameters found"


@mock_aws
def test_NoFileParam():
    s3_client = boto3.client('s3')
    testBucketName = 'dev-sierra-e-bucket'
    s3_client.create_bucket(Bucket=testBucketName)

    response = lambda_handler(event=NoFileParamEvent(), _context=None)
    # checks if the right error was passed
    assert response['statusCode'] == 400
    body = json.loads(response["body"]).get("error")
    assert body == "Missing 'file' parameter"


@mock_aws
def test_NoEvent():
    s3_client = boto3.client('s3')
    testBucketName = 'dev-sierra-e-bucket'
    s3_client.create_bucket(Bucket=testBucketName)

    # checks if the right error was passed
    response = lambda_handler(event=None, _context=None)
    assert response['statusCode'] == 500
    body = json.loads(response["body"]).get("error")
    assert body == "Internal Server Error"
