import argparse
import json
import os
from zipfile import ZipFile

import requests


DIR_EXCLUDE = [".git", ".datalad"]
FILE_EXCLUDE = [".gitattributes"]


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
        "--sandbox",
        action="store_true",
        help="Flag to do a test upload on Zenodo sandbox.",
    )
    return parser.parse_args()


def generate_dats(dats_file, concept_doi, version):
    with open(dats_file) as fin:
        metadata = json.load(fin)

    # Dataset stats
    nb_subjects = len(
        [
            dirname
            for dirname in os.listdir("candidates")
            if os.path.isdir(os.path.join("candidates", dirname))
        ]
    )
    nb_files = 0
    data_size = 0
    for root, dirs, files in os.walk("candidates"):
        if any(map(lambda x: x in root, DIR_EXCLUDE)):
            continue
        for f in files:
            if any(map(lambda x: x in f, FILE_EXCLUDE + ["DATS.json"])):
                continue
            nb_files += 1
            data_size += os.stat(os.path.join(root, f)).st_size
    data_size /= 1024 ** 3  # Convert from Bytes to GB

    if "distributions" not in metadata:
        metadata["distributions"] = []
        metadata["distributions"].append(
            {"size": f"{data_size:.2f}", "unit": {"value": "GB"}}
        )
    else:
        for dist in metadata["distributions"]:
            dist["size"] = f"{data_size:.2f}"
            dist["unit"] = "GB"

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

    # Update zenodo fields
    metadata["zenodo"] = {}
    metadata["zenodo"]["concept_doi"] = concept_doi
    metadata["zenodo"]["version"] = version

    with open("candidates/DATS.json", "w") as fout:
        json.dump(metadata, fout, indent=4)


def zip_files(in_path, metadata):
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
    concept_doi = r.json()["conceptrecid"]

    # Upload file in new deposition.
    generate_dats(config_file, concept_doi, deposition_id)
    zip_files("candidates", config_file)

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
    upload_to_zenodo(args.token, args.sandbox, args.metadata)


if __name__ == "__main__":
    main()
