"""
data_info.json should be structured as such:

{
	"data_info":[
        {
            "id": # unique dataset identifier,
            "path": # path to a .csv file,
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
import pandas as pd
import json

DATA_INFO_PATH  : str = "./data_info.json"
DATA_INFO       : dict[str, Any] = {}
DATASETS        : dict[str, pd.DataFrame] = {}

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
    data_info, names = DATA_INFO.values()
    for dataset in data_info:
        id, path, cols = dataset.values()
        df = pd.read_csv(path, usecols=cols)
        df = df.rename(names)
        DATASETS.update({id: df})



    


