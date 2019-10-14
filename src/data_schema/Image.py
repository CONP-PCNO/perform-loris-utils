import requests

from requests.exceptions import HTTPError

from utils import save_binary


class Image:
    def __init__(self, filename, data=None):
        self.filename = filename
        self.data = data

    @property
    def get_filename(self):
        return self.filename

    @property
    def get_data(self):
        return self.data

    def collect_data(self, api_url, header):
        print("img-url:", api_url + "/" + self.filename)
        with requests.Session() as s:
            try:
                response = s.get(
                    url=f"{api_url}/images/{self.filename}", headers=header
                )
                response.raise_for_status()
                self.data = response.content

            except HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except Exception as err:
                print(f"Other error occurred: {err}")

    def save_data(self, path):
        save_binary(path=f"{path}/{self.filename}", data=self.data)

