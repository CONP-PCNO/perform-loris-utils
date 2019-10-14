from utils import get_request
from .Instrument import Instrument
from .Image import Image


class Visit:
    def __init__(self, id):
        self.id = id
        self.meta = None
        self.instruments = []
        self.images = []

    @property
    def get_meta(self):
        return self.meta

    @property
    def get_instruments(self):
        return self.instruments

    @property
    def get_images(self):
        return self.images

    def collect_data(self, api_url, header):
        api_url += f"/{self.id}"
        self.meta = get_request(url=api_url, headers=header)

        # Retrieve all instruments and their metarmation
        instrument_ids = get_request(url=f"{api_url}/instruments", headers=header)[
            "Instruments"
        ]

        for instrument_id in instrument_ids:
            instrument = Instrument(instrument_id)
            self.instruments.append(instrument)
            instrument.collect_data(api_url, header=header)

        # Retrieve all images and their metarmation
        images_ids = get_request(url=f"{api_url}/images", headers=header)["Files"]

        for images_id in images_ids:
            image = Image(images_id["Filename"])
            self.images.append(image)
            image.collect_data(api_url, header=header)

    def save_data(self, path):
        for instrument in self.instruments:
            instrument.save_data(path=path + f"/{self.id}/instruments")

        for image in self.images:
            image.save_data(path=path + f"/{self.id}/images")
