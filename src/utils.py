import json
import os
import sys

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


def post_request(url, *args, **kwargs):
    with requests.Session() as s:
        try:
            response = s.post(url, *args, **kwargs)
            response.raise_for_status()

            return response.json()

        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            sys.exit(-1)
        except Exception as err:
            print(f"Other error occurred: {err}")


def save_json(path, data):
    if data is None:
        return

    save_dir = "/".join(path.split("/")[:-1])
    os.makedirs(save_dir, exist_ok=True)
    with open(path, "w") as f_out:
        json_data = json.dumps(data, indent=4)
        f_out.write(json_data)


def save_binary(path, data):
    save_dir = "/".join(path.split("/")[:-1])
    os.makedirs(save_dir, exist_ok=True)
    with open(path, "wb") as f_out:
        f_out.write(data)

