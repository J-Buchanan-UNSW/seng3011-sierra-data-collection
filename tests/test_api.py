"""
Test script to test authentication and access to API with
sample request to get s3 upload url
"""

import os
import requests

# Retrieve the environment variables
client_id = os.getenv("CLIENT_ID", "")
client_secret = os.getenv("CLIENT_SECRET", "")
api_endpoint = os.getenv("API_ENDPOINT", "")
cognito_domain = os.getenv("COGNITO_DOMAIN", "")


def get_token():
    """
    Handles getting token

    Args:
        None

    Returns:
        str: Access Token to be used for API access.
    """

    url = f"{cognito_domain}/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",  # Using client credentials grant
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "default-m2m-resource-server-u1isj/read"
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print("Error getting token:", response.text)
        raise Exception("Unable to get token")


def make_api_request(access_token):
    """
    Function to make the API request with the access token

    Args:
        str: Access Token to be used for API access.

    Returns:
        None
    """

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Send the GET request to the API
    response = requests.get(api_endpoint, headers=headers)

    if response.status_code == 200:
        print("Request was successful!")
        print("Response data:", response.json())
    else:
        print("Request failed!")
        print(f"Status Code: {response.status_code}")
        print("Response:", response.text)


def run():
    """
    Function to run the overall test

    Args:
        None

    Returns:
        None
    """
    access_token = get_token()
    print("Access token:", access_token)

    make_api_request(access_token)


if __name__ == "__main__":
    run()
