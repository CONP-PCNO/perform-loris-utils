import argparse
import json
import os
import subprocess

import datalad.api


DIR_EXCLUDE = [".git", ".datalad"]
FILE_EXCLUDE = [".DS_Store", ".gitattributes"]


def _get_args():
    parser = argparse.ArgumentParser(
        description="Datalad crawler for LORIS file uploader."
    )
    parser.add_argument("loris_url", type=str, help="URL of a LORIS Candidate API.")
    parser.add_argument(
        "candidates",
        type=str,
        help="Path to file holding a list of candidates ID to upload on Zenodo.",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help='Bypass confirmation if a "candidates" folder alrady exist.',
    )
    return parser.parse_args()


def candidate_download(candidates_file):

    # Verify if folder already exists
    if os.path.exists("candidates"):
        answer = ""
        if not args.batch:
            while answer.lower() not in ["y", "n"]:
                answer = input(
                    'A folder "candidates" folder already exist. Are you sure you want to continue [Y/n] ? '
                )

            if answer.lower() != "y":
                system.exit(0)
    else:
        os.mkdir("candidates")

    # Download data from each candidate
    with open(candidates_file) as fin:
        ids = fin.read().split()

    os.chdir("candidates")
    pwd = os.getcwd()
    for id_ in ids:
        if not os.path.exists(id_):
            datalad.api.create(id_)
        os.chdir(id_)
        datalad.api.crawl_init(
            save=True,
            template="loris-candidate-api",
            args={"url": "{}/{}".format(args.loris_url, id_)},
        )
        datalad.api.crawl()
        os.chdir(pwd)


if __name__ == "__main__":
    args = _get_args()
    candidate_download(args.candidates)
