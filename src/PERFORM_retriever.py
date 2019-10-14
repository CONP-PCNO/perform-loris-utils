import argparse
import os

from utils import post_request
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


def crawler(args):
    """Crawl LORIS database to obtain a candidate data.
    """

    credentials_file = args.credentials_file
    if not os.path.exists(credentials_file):
        raise FileNotFoundError

    # Retrieve authentification token
    token = None
    with open(credentials_file) as f_in:
        token = post_request(url=f"{PERFORM_API_URL}/login", data=f_in.read())["token"]
    TOKEN_HEADER = {"Authorization": f"Bearer {token}"}

    # Retrieve candidate information
    candidate = Candidate(args.candidate_id)
    candidate.collect_data(PERFORM_API_URL, header=TOKEN_HEADER)
    p = "/Users/math/Documents/opensource/RA-perform"
    candidate.save_data(path=p)


def zenodo_upload(args):
    """Upload a dataset to Zenodo

    Return
    ======
        None
    """
    pass


def main():
    args = parse_args()
    crawler(args)
    zenodo_upload(args)


if __name__ == "__main__":
    main()
