from utils import get_request, save_json


class Instrument:
    def __init__(self, type_):
        self.type_ = type_
        self.test_results = None

    @property
    def get_type_(self):
        return self.type_

    @property
    def get_test_results(self):
        return self.test_results

    def collect_data(self, api_url, header):
        self.test_results = get_request(
            url=f"{api_url}/instruments/{self.type_}", headers=header
        )
        if self.test_results is not None:
            self.test_results.pop("Meta", None)

    def save_data(self, path):
        filename = "_".join(
            path.split("/")[-3:-1] + [self.type_]
        )  # TODO manipulate api_url path to from the right path
        save_json(path=f"{path}/{filename}", data=self.test_results)
