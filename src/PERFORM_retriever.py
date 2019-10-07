import argparse
import os
import requests
from requests.exceptions import HTTPError
import sys

from data_schema.Candidate import Candidate


PERFORM_API_URL = "https://loris.concordia.ca/api/v0.0.2"


def parse_args():
    """Return parsed arguments from the command line.

    Return
    ======
        Parsed arguments from the command line.
    """
    parser = argparse.ArgumentParser(description="Perform data retriver for LORIS")
    parser.add_argument(
        "credentials_file",
        type=str,
        help="Path to a json file contianing the user credentials",
    )
    parser.add_argument(
        "candidate_id",
        type=str,
        help="Candidate ID for which the information should be retirvied",
    )
    return parser.parse_args()


def authentification_token(credentials_file):
    """Return an authetification token.

    Parameters
    ==========
        credentials_file: str - path to a file containing the user credentials.

    Return
    ======
        token: str - Authentification token.
    """
    with open(credentials_file) as f_in:
        with requests.Session() as s:
            try:
                response = s.post(f"{PERFORM_API_URL}/login", data=f_in.read())
                response.raise_for_status()

                return response.json()["token"]

            except HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")
                sys.exit(-1)
            except Exception as err:
                print(f"Other error occurred: {err}")


def crawler():
    """Crawl LORIS database to obtain a candidate data.
    """

    args = parse_args()

    credentials_file = args.credentials_file
    if not os.path.exists(credentials_file):
        raise FileNotFoundError

    # Retrieve authentification token
    token = authentification_token(args.credentials_file)
    TOKEN_HEADER = {"Authorization": f"Bearer {token}"}

    # Retrieve candidate information
    candidate = Candidate(args.candidate_id)
    candidate.collect_data(PERFORM_API_URL, header=TOKEN_HEADER)


def zenodo_upload():
    """Upload a dataset to Zenodo

    Return
    ======
        None
    """
    pass


def main():
    crawler()
    zenodo_upload()


if __name__ == "__main__":
    main()
