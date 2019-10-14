from utils import get_request
from .Visit import Visit


class Candidate:
    def __init__(self, id):
        self.id = id
        self.meta = None
        self.visits = []

    @property
    def get_id(self):
        return self.id

    @property
    def get_meta(self):
        return self.meta

    @property
    def get_visits(self):
        return self.visits

    def collect_data(self, api_url, header):
        api_url += f"/candidates/{self.id}"
        self.meta = get_request(url=api_url, headers=header)

        for visit_id in self.meta["Visits"]:
            visit = Visit(visit_id)
            self.visits.append(visit)

            visit.collect_data(api_url, header=header)

    def save_data(self, path):
        for visit in self.visits:
            visit.save_data(path + f"/candidates/{self.id}")
