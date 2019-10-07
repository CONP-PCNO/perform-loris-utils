import requests
from requests.exceptions import HTTPError


def get_request(url, *args, **kwargs):
    with requests.Session() as s:
        try:
            response = s.get(url, *args, **kwargs)
            response.raise_for_status()
            return response.json()

        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"Other error occurred: {err}")


