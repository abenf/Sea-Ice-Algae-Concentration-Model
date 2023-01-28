#!/bin/bash

source ~/miniconda3/Scripts/activate sea-ice_algae

conda list --export > requirements.txt
conda env export > environment.yml
git add ./dependencies/environment.yml ./dependencies/requirements.txt && git commit -m "Updated dependencies."

echo "Press any key..."
read
exit 0