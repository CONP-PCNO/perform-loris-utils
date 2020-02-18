# loris2zenodo: A tool to crawl a loris database by candidates and store the data on Zenodo

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Requirements:
- Install Docker
- [Create a Zenodo token](https://www.zenodo.org/account/settings/applications/tokens/new/)

## Usage:
```bash
docker run -it --rm \
  -v $PWD/candidates:/app/candidates \
  -v $PWD/config:/app/config:ro \
  # Mount Datalad provider configuration here, if needed. See note below.
  mathdugre/loris2zenodo loris_url candidates_file metadata_file zenodo_token [--conceptdoi CONCEPTDOI] [--sandbox]
```
**Note:** If the LORIS database you are trying to crawl requires
authentifcation you will need to pass a provider configuration file to docker.

1. Create a Datalad provider file using [this template](template.cfg).
2. Mount the volume with the datalad provider configuration when starting the container.
  
  Linux:
  ```
  -v ~/.config/datalad/providers/$PROVIDER_CONFIG:~/.config/datalad/providers/$PROVIDER_CONFIG:ro
  ```
  
  OSX:
  ```
  -v ~/Library/Application\ Support/datalad/providers/$PROVIDER_CONFIG:~/.config/datalad/providers/$PROVIDER_CONFIG:ro
  ```
  
## Parameters:

**loris_url:** URL pointing to the Candidate API of a LORIS database. More
*information about the LORIS API can be found in the [LORIS API
*wiki](https://github.com/aces/Loris/blob/master/docs/API/LorisRESTAPI.md).

**candidates_file:** A `.txt` file containing a candidate id, to upload on
*zenodo, on each line. 

**metadata_file:** A `DATS.json` file containing the metadata for the dataset.
For more information about the DATS format see [their
documentation](https://datatagsuite.github.io/docs/html/)
It must contain the following fields:
- "title"
- "description"
- "creators"

**zenodo_token:** Authentification token created from your Zenodo account.

**--conceptdoi (optional):** This flag allows to update a current
dataset instead of creating a new one. It require to pass the concept DOI of
the initial dataset; it can be found on Zenodo.

**--sandbox (optional):** This flag allows to do test upload on the Zenodo
*sandbox. Note that you will need a authentification token from [Zenodo
*sandbox](https://sandbox.zenodo.org/account/settings/applications/tokens/new/).
