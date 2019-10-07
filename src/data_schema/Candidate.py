from utils import get_request
from .Visit import Visit


class Candidate:
    def __init__(self, id):
        self.id = id
        self.info = None
        self.visits = []

    @property
    def get_id(self):
        return self.id

    @property
    def get_info(self):
        return self.info

    @property
    def get_visits(self):
        return self.visits

    def collect_data(self, api_url, header):
        api_url += f"/candidates/{self.id}"
        self.info = get_request(url=api_url, headers=header)

        for visit_id in self.info["Visits"]:
            visit = Visit(visit_id)
            self.visits.append(visit)

            visit.collect_data(api_url, header=header)
