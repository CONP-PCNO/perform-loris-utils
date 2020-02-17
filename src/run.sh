#!/bin/bash

python3 /app/src/loris_crawl.py $1 $2 --batch
python3 /app/src/zenodo_upload.py "candidates" $3 $4 $5 $6
