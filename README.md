# Modeling Arctic Sea-Ice Algae Data

The presence and intensity of algal blooms beneath arctic ice sheets is modeled using RGB image data across two sepearte studies.

## Repeating Model Building...
Build the environment in the local directory where you've stored the project using either `environment.yml` or `requirments.txt` located in the `dependencies` directory.

Modeling scripts are located in `modeling` as well as a saved CNN model which can be uploaded using keras in TensorFlow.

## For Data Preparation...
As part of `clean/dominant_color_analysis.ipynb`, the `run_clean` function located in the `clean/clean.py` script is called. This will overwrite modeling data sets located in `clean/cleaned_data`. Otherwise, use the `explore_data.ipynb` notebook.

Raw data is located in the `data` folder while cleaned and transformed data is located in `clean/cleaned_data`. .jpg images are located in `images`.

## Further Reading...
The `reference` directory contains relevant journal articles, some meta data (more is located in `data`), and various reports and posters including a report of this project (`reference/BDA_450_Report.pdf`).
