import argparse
import json
import os
import subprocess


DIR_EXCLUDE = [".git", ".datalad"]
FILE_EXCLUDE = [".DS_Store", ".gitattributes"]


def _get_args():
    parser = argparse.ArgumentParser(description="Datalad crawler for LORIS file uploader")
    parser.add_argument(
        "candidates", type=str, help="Path to file holding a list of candidates ID to upload on Zenodo."
    )
    return parser.parse_args()


def datalad_download(candidates_file):

    if os.path.exists("candidates"):
        while answer.lower() not in ["y", "n"]
            answer = input("A folder \"candidates\" folder already exist. Are you sure you want to continue ?")

        if answer.lower() == "y": system.exit(0)
    else:
        os.mkdir("candidates")
    
    with open(candidates_file) as fin:
        ids = fin.read().split()

    # Download data from each candidate
    pwd = os.getcwd()
    for id_ in ids:
        subprocess.run([
            f"datlad create candidates/{id_}",
        ])
        os.chdir(os.path.join(pwd, f"candidates/{id_}"))
        subprocess.run([
            f"datalad crawl-init --template=loris-candidate-api url=https://loris.concordia.ca/api/v0.0.2/candidates/{id_}",
            f"datalad crawl",
        ])
        os.chdir(pwd)       

if __name__ == "__main__":
    args = _get_args()
    datalad_download(args.candidates)
