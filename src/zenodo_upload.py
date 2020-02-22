import argparse
import json
import os
from zipfile import ZipFile

import humanize
import requests


EXCLUDED_DIRS = [".git", ".datalad"]
EXCLUDED_FILES = [".gitattributes"]
CONP_FILES = ["DATS.json", "logo.png"]


def _get_args():
    parser = argparse.ArgumentParser(description="Zenodo file uploader.")
    parser.add_argument(
        "in_path", type=str, help="Path to file or folder to upload.",
    )
    parser.add_argument(
        "metadata",
        type=str,
        help="Path to a DATS.json file containing zenodo metadata.",
    )
    parser.add_argument(
        "token", type=str, help="Zenodo token.",
    )
    parser.add_argument(
        "--conceptdoi", nargs="?", type=str, help="Zenodo dataset concept DOI.",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Flag to do a test upload on Zenodo sandbox.",
    )
    return parser.parse_args()


def generate_dats(dats_file, in_path, concept_doi):
    with open(dats_file) as fin:
        metadata = json.load(fin)

    # Dataset stats
    nb_subjects = len(
        [
            dirname
            for dirname in os.listdir(in_path)
            if os.path.isdir(os.path.join(in_path, dirname))
        ]
    )
    nb_files = 0
    data_size = 0
    for root, dirs, files in os.walk(in_path):
        if any(map(lambda x: x in root, EXCLUDED_DIRS)):
            continue
        for name in files:
            if any(map(lambda x: x in name, EXCLUDED_FILES + CONP_FILES)):
                continue
            nb_files += 1
            data_size += os.stat(os.path.join(root, name)).st_size

    # Convert to human readable
    data_size, data_unit = humanize.naturalsize(data_size).split(" ")
    data_size = float(data_size)

    if "distributions" not in metadata:
        metadata["distributions"] = []
        metadata["distributions"].append(
            {
                "size": data_size,
                "unit": {"value": data_unit},
                "access": {
                    "landingPage": "https://zenodo.org/record/" + concept_doi,
                    "authorizations": [{"value": "restricted"}],
                },
            }
        )
    else:
        for dist in metadata["distributions"]:
            dist["size"] = data_size
            dist["unit"] = {"value": data_unit}
            dist["access"] = {
                "landingPage": "https://zenodo.org/record/" + concept_doi,
                "authorizations": [{"value": "restricted"}],
            }

    if "extraProperties" not in metadata:
        metadata["extraProperties"] = [
            {"category": "CONP_status", "values": [{"value": "CONP"}]},
            {"category": "files", "values": [{"value": nb_files}]},
            {"category": "subjects", "values": [{"value": nb_subjects}]},
        ]
    else:
        property_to_modify = {
            "CONP_status": "CONP",
            "files": nb_files,
            "subjects": nb_subjects,
        }
        for extra_property in metadata["extraProperties"]:
            if extra_property["category"] in property_to_modify:
                extra_property["values"] = [
                    {"value": property_to_modify[extra_property["category"]]}
                ]
                del property_to_modify[extra_property["category"]]

        for extra_property, value in property_to_modify.items():
            metadata["extraProperties"].append(
                {"category": extra_property, "values": [{"value": value}]}
            )

    with open(in_path + "/DATS.json", "w") as fout:
        json.dump(metadata, fout, indent=4)


def zip_files(in_path):
    with ZipFile("data.zip", "w") as myzip:

        if os.path.exists(in_path):

            # Handle file and folder seperately
            if os.path.isfile(in_path):
                myzip.write(in_path)

            elif os.path.isdir(in_path):
                for root, dirs, files in os.walk(in_path):
                    if any(map(lambda x: x in root, EXCLUDED_DIRS)):
                        continue
                    for name in files:
                        if any(map(lambda x: x in name, EXCLUDED_FILES)):
                            continue

                        # Zip files at root if they are required for CONP protal.
                        if any(map(lambda x: x in name, CONP_FILES)):
                            myzip.write(os.path.join(root, name), name)
                        else:
                            myzip.write(os.path.join(root, name))
            else:
                raise ValueError

        else:
            raise FileNotFoundError


def upload_to_zenodo(config_file, in_path, ACCESS_TOKEN, concept_doi, is_sandbox):
    sandbox = "sandbox." if is_sandbox else ""

    if not os.path.exists(config_file):
        raise FileNotFoundError

    with open(config_file) as fin:
        config = json.loads(fin.read())

    headers = {"Content-Type": "application/json"}

    # Update deposition or create a new one if not specified.
    if concept_doi:
        # We retrieve the first version of the data set
        # and it has doi one more than the concept_doi.
        deposition_id = int(concept_doi) + 1
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
    concept_doi = r.json()["conceptrecid"]

    # Upload file in new deposition.
    generate_dats(config_file, in_path, concept_doi)
    zip_files(in_path)

    bucket_url = r.json()["links"]["bucket"]
    with open("data.zip", "rb") as fin:
        r = requests.put(
            bucket_url + "/data.zip", data=fin, params={"access_token": ACCESS_TOKEN},
        )

    # Validate metadata fields
    if "title" not in config or "description" not in config or "creators" not in config:
        raise ValueError

    if "licenses" not in config:
        config["licenses"] = {}
    if "keywords" not in config:
        config["keywords"] = {}

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
    upload_to_zenodo(
        args.metadata, args.in_path, args.token, args.conceptdoi, args.sandbox
    )


if __name__ == "__main__":
    main()
