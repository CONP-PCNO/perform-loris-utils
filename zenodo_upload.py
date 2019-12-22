import argparse
import json
import os
from zipfile import ZipFile

import requests


DIR_EXCLUDE = [".git", ".datalad"]
FILE_EXCLUDE = [".gitattributes"]


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

        if os.path.exists(in_path):

            # Handle file and folder seperately
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

    # Update deposition or create a new one if not specified.
    if "zenodo" in config and "version" in config["zenodo"]:
        deposition_id = config["zenodo"]["version"]
        r = requests.post(
            "https://{}zenodo.org/api/deposit/depositions/{}/actions/newversion".format(
                sandbox, deposition_id
            ),
            params={"access_token": ACCESS_TOKEN},
        )

        latest_draft = r.json()["links"]["latest_draft"]
        r = requests.get(latest_draft, params={"access_token": ACCESS_TOKEN})
        deposition_id = latest_draft.split("/")[-1]

        # Delete files from previous deposition.
        res = requests.get(
            "https://{}zenodo.org/api/deposit/depositions/{}/files".format(
                sandbox, deposition_id
            ),
            params={"access_token": ACCESS_TOKEN},
        )

        files = res.json()
        for file_ in files:
            file_id = file_["id"]
            requests.delete(
                "https://{}zenodo.org/api/deposit/depositions/{}/files/{}".format(
                    sandbox, deposition_id, file_id
                ),
                params={"access_token": ACCESS_TOKEN},
            )

    else:
        r = requests.post(
            "https://{}zenodo.org/api/deposit/depositions".format(sandbox),
            params={"access_token": ACCESS_TOKEN},
            json={},
            headers=headers,
        )
        deposition_id = r.json()["id"]

    # Upload file in new deposition.
    bucket_url = r.json()["links"]["bucket"]
    with open("data.zip", "rb") as fin:
        r = requests.put(
            bucket_url + "/data.zip", data=fin, params={"access_token": ACCESS_TOKEN},
        )

    # Populate metadata fields.
    data = {
        "metadata": {
            "title": config["title"],
            "upload_type": "dataset",
            "description": config["description"],
            "creators": [
                {
                    k: v
                    for k, v in creator.items()
                    if k in ["name", "affiliation", "orcid", "gnd"]
                }
                for creator in config["creators"]
            ],
            "access_right": "restricted",
            "access_conditions": " ".join(
                [license["name"] for license in config["licenses"]]
            ),
            "keywords": [
                "canadian-open-neuroscience-platform",
                *[kw["value"] for kw in config["keywords"]],
            ],
        }
    }

    if "doi" in config:
        data["metadata"].update({"doi": config["doi"]})

    r = requests.put(
        "https://{}zenodo.org/api/deposit/depositions/{}".format(
            sandbox, deposition_id
        ),
        params={"access_token": ACCESS_TOKEN},
        data=json.dumps(data),
        headers=headers,
    )

    # Publish new depostion.
    r = requests.post(
        "https://{}zenodo.org/api/deposit/depositions/{}/actions/publish".format(
            sandbox, deposition_id
        ),
        params={"access_token": ACCESS_TOKEN},
    )


def main():
    """Zip a folder or file and upload it to zenodo."""
    args = _get_args()
    zip_files(args.in_path)
    upload_to_zenodo(args.token, args.sandbox, args.config)


if __name__ == "__main__":
    main()
