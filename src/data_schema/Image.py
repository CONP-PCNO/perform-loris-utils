import requests


class Image:
    def __init__(self, path, data=None):
        self.path = path
        self.data = data

    @property
    def get_path(self):
        return self.path

    @property
    def get_data(self):
        return self.data

    def collect_data(self, api_url, header):
        pass
