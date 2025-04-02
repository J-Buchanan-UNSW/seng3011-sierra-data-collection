"""
Test script to test authentication and access to API with
sample request to get s3 upload url
"""

import os
import requests

# Retrieve the environment variables
api_endpoint = os.getenv("API_ENDPOINT", "")

def make_api_request():
    """
    Function to make the API request

    Args:
        None

    Returns:
        None
    """

    # Send the GET request to the API
    response = requests.get(api_endpoint)

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
    make_api_request()


if __name__ == "__main__":
    run()
