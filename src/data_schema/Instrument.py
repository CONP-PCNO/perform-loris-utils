from utils import get_request


class Instrument:
    def __init__(self, type_):
        self.type_ = type_
        self.info = None

    @property
    def get_type_(self):
        return self.type_

    @property
    def get_info(self):
        return self.info

    def collect_data(self, api_url, header):
        api_url += "/instruments"
        self.info = get_request(url=f"{api_url}/{self.type_}", headers=header)
