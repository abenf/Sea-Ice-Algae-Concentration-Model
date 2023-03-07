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

from typing import Any, Tuple, List
from PIL import Image
from sys import argv
import pandas as pd
import numpy as np
import json

PROJECT_DIRECTORY   : str = \
    "C:/Users/Andrew/OneDrive/Desktop/sea-ice_algae_image_recognition/"
DATA_INFO_PATH      : str = "clean/data_info.json"
IMAGE_DETAILS_PATH  : str = "data/WarmBuoys_Image_details.xlsx"
DATA_INFO           : dict[str, Any] = {}
DATASETS            : dict[str, pd.DataFrame] = {}
IMAGE_SETS          : dict[str, list[np.ndarray[int]]] = {}

def set_PROJECT_DIRECTORY(path: str) -> None:
    global PROJECT_DIRECTORY
    if path is not None:
        PROJECT_DIRECTORY = path

def set_DATA_INFO_PATH(
        path: str, add_proj_dir: bool=False) -> None:
    """
    Set the filepath for data_info.json file.
    
    Stored in DATA_INFO_PATH.
    """
    global PROJECT_DIRECTORY, DATA_INFO_PATH
    
    if path is not None:
        DATA_INFO_PATH = path
    if add_proj_dir:
        DATA_INFO_PATH = PROJECT_DIRECTORY + DATA_INFO_PATH

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
        df.DataDateTime = pd.to_datetime(df.DataDateTime)
        df.set_index("DataDateTime", drop=True, inplace=True)
        df = df.rename(names)

        DATASETS.update({id: df})

def get_image_details(
        xlsx: pd.ExcelFile, im_directory_path: str) -> pd.DataFrame:
    """
    Extract image details from excel file and store as DataFrame.
    """
    # f'#{n}', corresponds to buoy number n, i.e. "#8" for Buoy 8
    current_sheet = im_directory_path[-2:-1] 
    im_details = pd.read_excel(xlsx, current_sheet)
    return im_details

def read_images_as_arrays() -> None:
    """
    Load image data corresponding to each .csv file into numpy arrays
    from PIL Image objects and store in IMAGE_SETS by 'id'.
    """
    global IMAGE_SETS
    data_info, names = tuple(DATA_INFO.values())
    xlsx = pd.ExcelFile(IMAGE_DETAILS_PATH)
    
    for dataset in data_info:
        id = dataset["id"]
        im_directory_path = dataset["im_directory_path"] + "/"
        ims = get_image_details(xlsx, dataset)
    
        ims["Image_array"] = ims.apply(
            lambda row: 
                np.asarray(
                    Image.open(
                        im_directory_path + row["Filename"]
                        )
                    ), 
                axis=1
            )
        
        IMAGE_SETS.update({id: ims})

def cat_data_with_images() -> None:
    """
    Merge image data with numeric data into various configurations.
    """
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

def run_clean() -> None:
    """"""
    load_data_info()
    read_data_from_info()
    read_images_as_arrays()
    cat_data_with_images()

def set_IMAGE_DETAILS_PATH(
        path: str, add_proj_dir: bool=False) -> None:
    """
    Set the filepath for the WarmBuoys_Image_details.xlsx file.
    
    Stored in IMAGE_DETAILS_PATH.
    """
    global PROJECT_DIRECTORY, IMAGE_DETAILS_PATH
    
    if path is not None:
        IMAGE_DETAILS_PATH = path
    if add_proj_dir:
        IMAGE_DETAILS_PATH = PROJECT_DIRECTORY + IMAGE_DETAILS_PATH

def load_data_info() -> None:
    """
    From a .json file, gather info which will be used to load data.
    
    Stored as a dict that shares the file's structure, DATA_INFO.
    """
    global DATA_INFO
    with open(DATA_INFO_PATH, 'r') as f:
        DATA_INFO = json.load(f)

def handle_argv(args: Tuple[str]) -> Tuple[str, bool]:
    """"""
    cl_args: list[str] = [args[i] for i in range(1, len(args))]
    new_data_info_path, new_image_details_path, new_project_dir_path = None
    abort = False
    if cl_args and cl_args[0][0] != "-":
        abort = True
        print(f"Unknown options: {cl_args}")
    else:
        flag = cl_args[0]
        if 'h' in flag:
            print("help message")
            abort = True
        else:
            d_pos = flag.find('d')
            i_pos = flag.find('i')
            p_pos = flag.find('p')

            change_data_info_path = bool(1 + d_pos) # False if not found
            change_image_details_path = bool(1 + i_pos) # False if not found
            change_project_directory = bool(1 + p_pos) # False if not found            
            if change_data_info_path:
                new_data_info_path = cl_args[d_pos]
            if change_image_details_path:
                new_image_details_path = cl_args[i_pos]
            if change_project_directory:
                new_project_dir_path = cl_args[p_pos]

    return (new_data_info_path, 
            new_image_details_path, 
            new_project_dir_path, 
            abort)

def main(*args: Tuple[str]):
    data_info_path, image_details_path, proj_dir_path, abort = handle_argv(args)
    if not abort:
        set_PROJECT_DIRECTORY(proj_dir_path)    
        set_DATA_INFO_PATH(data_info_path, add_proj_dir=True)
        set_IMAGE_DETAILS_PATH(image_details_path, add_proj_dir=True)
        run_clean()

if __name__ == "__main__":
    main(*argv)