"""
Using a .json file, load and mutate data (numeric and image) for analysis.


data_info.json should be structured as such:

{
	"data_info":[
        {
            "id": # unique dataset identifier,
            "data_path": # path to a .csv file,
            "im_directory_path": # path to image directory,
            "cols":[

                # names of selected columns of the .csv

            ],
            .
            .
            .
        }
    "names":{ # for each unique column name across all imported datasets
              # (or each unique column name in a subset of selected columns)
        .
        .
        .
        # old name : # replacement name,
        .
        .
        .
    }
"""

from typing import Any
from PIL import Image
from os import scandir
import pandas as pd
import numpy as np
import json

DATA_INFO_PATH      : str = "./data_info.json"
IMAGE_DETAILS_PATH  : str = "../data/WarmBuoys_Image_details.xlsx"
DATA_INFO           : dict[str, Any] = {}
DATASETS            : dict[str, pd.DataFrame] = {}
IMAGE_SETS          : dict[str, list[np.ndarray[int]]] = {}

def set_DATA_INFO_PATH(path: str) -> None:
    """
    Set the filepath for data_info.json file.
    
    Stored in DATA_INFO_PATH.
    """
    global DATA_INFO_PATH
    DATA_INFO_PATH = path

def load_data_info() -> None:
    """
    From a .json file, gather info which will be used to load data.
    
    Stored as a dict that shares the file's structure, DATA_INFO.
    """
    global DATA_INFO
    with open(DATA_INFO_PATH, 'r') as f:
        DATA_INFO = json.load(f)

def read_data_from_info() -> None:
    """
    Load specified columns of each .csv file to its own DataFrame.
    
    Based on DATA_INFO; each set stored by 'id' in a dictionary, DATASETS.
    """
    global DATASETS
    data_info, names = tuple(DATA_INFO.values())
    for dataset in data_info:
        id, csv_path, im_path, cols = tuple(dataset.values())
        df = pd.read_csv(csv_path, usecols=cols)
        df = df.rename(names)

        DATASETS.update({id: df})

def get_image_details(
        xlsx: pd.ExcelFile, dataset: dict[str, Any]) -> pd.DataFrame:
    """
    Extract image details from excel file and store as DataFrame.
    """
    # f'#{n}', corresponding to buoy number n
    current_sheet = dataset["im_directory_path"][-2:-1] 
    im_details = pd.read(xlsx, current_sheet)
    return im_details

def read_images_from_info() -> None:
    """
    Load image data corresponding to each .csv file into numpy arrays and
    store in IMAGE_SETS by 'id'.

    Based on DATA_INFO; if image has available details in the .xlsx file 
    stored at IMAGE_DETAILS_PATH, then for each set stored by 'id' in a 
    dictionary, `DATASETS`, Images are decomposed into numeric 
    height/width/channels data.
    """
    data_info, names = tuple(DATA_INFO.values())
    xlsx = pd.ExcelFile(IMAGE_DETAILS_PATH)
    for dataset in data_info:
        id = dataset["id"]
        im_directory_path = dataset["im_directory_path"]
        im_details = get_image_details(xlsx, dataset)
        im_set = []

        im_directory = scandir(im_directory_path)
        for im in im_directory:
            # check that image details are present (unusable if not present)
            im_details_present: bool = im_details.isin({'Filename': im.name})
            if im_details_present:
                im_array = np.array(Image.open(im.path))
                im_set.append(im_array)
        
        IMAGE_SETS.update({id: im_set})

def cat_data_with_images() -> None:
    """Merge image data with numeric data into various configurations."""
    pass

def all_observations() -> pd.DataFrame:
    """Include all numeric readings."""
    pass

def average_observations(avg_radius: int) -> pd.DataFrame:
    """
    Include averaged measurements of the `avg_radius` observations below 
    to the `avging_radius`obervations above the observation corresponding to 
    approximate solar noon.

    parameters:
        avg_radius (int): the radius of observations to average with the 
        observation closest to best approximations of solarnoon at the center.
    """
    pass

def image_observations() -> pd.DataFrame:
    """Include only numeric data that corresponds to approximate solar noon."""
    pass

def main():
    load_data_info()
    read_data_from_info()
    read_images_from_info()
    cat_data_with_images()

if __name__ == "__main__":
    main()