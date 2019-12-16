import argparse
import json
import os
from zipfile import ZipFile

import requests


DIR_EXCLUDE = [".git", ".datalad"]
FILE_EXCLUDE = [".DS_Store", ".gitattributes"]


def _get_args():
    parser = argparse.ArgumentParser(description="Zenodo file uploader")
    parser.add_argument(
        "in_path", type=str, help="Path to file or folder to upload",
    )
    parser.add_argument("config", type=str, help="Path to config.json file")
    parser.add_argument(
        "token", type=str, help="Zenodo token",
    )
    parser.add_argument(
        "--sandbox", action="store_true", help="Flag to test on Zenodo sandbox",
    )
    return parser.parse_args()


def zip_files(in_path):
    with ZipFile("data.zip", "w") as myzip:

        # Verify that file exist
        if os.path.exists(in_path):

            # Check if input path is a file or folder
            if os.path.isfile(in_path):
                myzip.write(in_path)

            elif os.path.isdir(in_path):
                for dirpath, dirnames, filenames in os.walk(in_path):
                    if any(map(lambda x: x in dirpath, DIR_EXCLUDE)):
                        continue
                    for filename in filenames:
                        if any(map(lambda x: x in filename, FILE_EXCLUDE)):
                            continue
                        myzip.write(os.path.join(dirpath, filename))
            else:
                raise ValueError
        else:
            raise FileNotFoundError


def upload_to_zenodo(ACCESS_TOKEN, is_sandbox, config_file):
    sandbox = "sandbox." if is_sandbox else ""

    if not os.path.exists(config_file):
        raise FileNotFoundError

    with open(config_file) as fin:
        config = json.loads(fin.read())

    headers = {"Content-Type": "application/json"}

    # Retrieve deposition or create a new one if not specified.
    if "zenodo" in config \
        and "version" in config["zenodo"]:
        deposition_id = config["zenodo"]["version"]
    else:
        r = requests.post(
            f"https://{sandbox}zenodo.org/api/deposit/depositions",
            params={"access_token": ACCESS_TOKEN},
            json={},
            headers=headers,
        )
        deposition_id = r.json()["id"]

    # Update file in deposition.
    data = {"name": "data.zip"}
    with open("data.zip", "rb") as fin:
        r = requests.post(
            f"https://{sandbox}zenodo.org/api/deposit/depositions/%s/files" % deposition_id,
            params={"access_token": ACCESS_TOKEN},
            data=data,
            files={"file": fin},
        )

    data = {
        "metadata": {
            "title": config["title"],
            "upload_type": "dataset",
            "description": config["description"],
            "creators": [
                    {k:v for k, v in creator.items() if k in ["name", "affiliation", "orcid", "gnd"]}
                        for creator in config["creators"]
                ],
            "access_right": "restricted",
            "access_conditions": " ".join([
                    license["name"] for license in config["licenses"]
                ]),
            "keywords": ["canadian-open-neuroscience-platform",
                        *[kw["value"] for kw in config["keywords"]]
                    ],
        }
    }

    # Check or DOI
    if "doi" in config:
        data["metadata"].update({"doi": config["doi"]})

    # Upload metadata
    r = requests.put(
        f"https://{sandbox}zenodo.org/api/deposit/depositions/%s" % deposition_id,
        params={"access_token": ACCESS_TOKEN},
        data=json.dumps(data),
        headers=headers,
    )

    # Publish
    r = requests.post(
        f"https://{sandbox}zenodo.org/api/deposit/depositions/%s/actions/publish"
        % deposition_id,
        params={"access_token": ACCESS_TOKEN},
    )


def main():
    """Zip a folder or file and upload it to zenodo."""
    args = _get_args()
    #zip_files(args.in_path)
    upload_to_zenodo(args.token, args.sandbox, args.config)


if __name__ == "__main__":
    main()
