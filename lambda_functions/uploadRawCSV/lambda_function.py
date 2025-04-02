import json
import os
import boto3
import requests
import jwt
from botocore.config import Config

BUCKET_NAME = os.getenv("BUCKET_NAME", "dev-sierra-e-bucket")
UPLOAD_PREFIX = "rawCSV/"
COGNITO_POOL_ID = os.getenv("COGNITO_POOL_ID", "")
COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN", "")
JWKS_URL = COGNITO_DOMAIN + "/" + COGNITO_POOL_ID + "/.well-known/jwks.json"


# Fetch Cognito JWKS keys
def get_jwks():
    try:
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching JWKS: {str(e)}")
        return None


# Verify the JWT using the appropriate key
def verify_jwt(token):
    jwks = get_jwks()
    if not jwks:
        raise Exception("Could not fetch JWKS")

    unverified_header = jwt.get_unverified_header(token)
    if unverified_header is None or 'kid' not in unverified_header:
        raise Exception('Invalid token header')

    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
            break

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=os.getenv("API_AUDIENCE"),
                issuer=COGNITO_DOMAIN + "/" + COGNITO_POOL_ID
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.JWTClaimsError:
            raise Exception("Invalid claims")
        except Exception as e:
            raise Exception(f"Token validation error: {str(e)}")
    else:
        raise Exception("Unable to find appropriate key")


def lambda_handler(event, _context):
    try:
        print(f"🚀 Starting Upload of Raw CSV to {UPLOAD_PREFIX}")
        print("📩 Event received:", json.dumps(event))

        # Get the Authorization token
        token = event['headers'].get('Authorization')
        if not token:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'error': 'Authorization token missing'
                })}

        # Validate the token
        payload = verify_jwt(token)
        print(f"Valid token payload: {payload}")

        s3 = boto3.client(
            "s3",
            region_name="ap-southeast-2",
            config=Config(signature_version="s3v4"),
        )

        params = event.get("queryStringParameters", {})
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
        existing_files = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=UPLOAD_PREFIX)

        if "Contents" in existing_files:
            for obj in existing_files["Contents"]:
                s3.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])

        presigned_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": s3_key,
                "ContentType": "text/csv",
            },
            ExpiresIn=3600,
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
            "body": json.dumps({"URL": presigned_url}),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal Server Error: {str(e)}"})
        }
