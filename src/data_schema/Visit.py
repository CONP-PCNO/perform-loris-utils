from utils import get_request
from .Instrument import Instrument
from .Image import Image


class Visit:
    def __init__(self, id):
        self.id = id
        self.info = None
        self.instruments = []
        self.images = []

    @property
    def get_info(self):
        return self.info

    @property
    def get_instruments(self):
        return self.instruments

    @property
    def get_images(self):
        return self.images

    def collect_data(self, api_url, header):
        api_url += f"/{self.id}"
        self.info = get_request(url=api_url, headers=header)

        # Retrieve all instruments and their information
        instrument_ids = get_request(url=f"{api_url}/instruments", headers=header)[
            "Instruments"
        ]

        for instrument_id in instrument_ids:
            instrument = Instrument(instrument_id)
            self.instruments.append(instrument)
            instrument.collect_data(api_url, header=header)

        # Retrieve all images and their information
        images_ids = get_request(url=f"{api_url}/images", headers=header)

        for images_id in images_ids:
            images = Image(images_id)
            self.images.append(images)
            images.collect_data(api_url, header=header)
