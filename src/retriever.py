import argparse
import os
import requests


def crawler():
    """Crawl LORIS database to obtain a candidate data.
    """

    API_URL = "https://loris.concordia.ca/api/v0.0.2"

    parser = argparse.ArgumentParser(description="Perform data retriver for LORIS")
    parser.add_argument(
        "credentials",
        type=str,
        help="Path to a json file contianing the user credentials",
    )
    parser.add_argument(
        "candidate",
        type=str,
        help="Candidate ID for which the information should be retirvied",
    )
    args = parser.parse_args()

    creds_file = None
    if os.path.exists(args.credentials):
        creds_file = args.credentials
    else:
        raise FileNotFoundError

    # Retrieve authentification token
    token = ""
    with open(creds_file) as f_in:
        response = requests.post(f"{API_URL}/login", data=f_in.read())
        if response.status_code != 200:
            raise ConnectionError

        token = response.json()["token"]

    TOKEN_HEADER = {"Authorization": f"Bearer {token}"}
    

    # TODO Retrieve candidate info
    candidate_info = requests.get(
        f"{API_URL}/candidates/{args.candidate}", headers=TOKEN_HEADER
    ).json()

    visits = candidate_info["Visits"]

    # TODO Retrieve visits info
    visits_info = list()
    for visit in visits:
        requests.get(
            f"{API_URL}/candidates/{args.candidate}/{visit}", headers=TOKEN_HEADER
        )

    # TODO Get list of available instruments

    # TODO Get instrument / test results

    # TODO Get list of images

    # TODO Download images


def zenodo_upload():
    """
    """
    pass


def main():
    crawler()
    zenodo_upload()


if __name__ == "__main__":
    main()
