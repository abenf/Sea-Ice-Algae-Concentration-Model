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

from typing import Any, Tuple
from PIL import Image
from colorthief import ColorThief
from os import path
import pandas as pd
import json

try:
    ...
except FileNotFoundError:
    ...
except NotADirectoryError:
    ...
except PermissionError:
    ...

CLEAN_PATH          : str = path.dirname(path.realpath(__file__))
    # ~/[path of stored directory]/sea-ice_algae_image_recognition/clean
PROJECT_PATH        : str = path.dirname(CLEAN_PATH)
    # ~/[path of stored directory]/sea-ice_algae_image_recognition/
CLEANED_DATA_PATH   : str = CLEAN_PATH \
    + "/cleaned_data"
DATA_INFO_PATH      : str = CLEAN_PATH \
    + "/data_info.json"
IMAGE_DETAILS_PATH  : str = PROJECT_PATH \
    + "/data/WarmBuoys_Image_details.xlsx"

DATA_INFO           : dict[str, Any] = {}
DATASETS            : dict[str, pd.DataFrame] = {}
IMAGE_SETS          : dict[str, pd.DataFrame] = {}

TRANSFORMED_DATA    : pd.DataFrame = None

def run_clean(mmcq_quality: int=1) -> None:
    """
    Cleaning script; ingest data_info.json, ingest, clean, and rename data
    .csv's, open and store .jpg's as arrays.
    """
    load_data_info()
    read_data_from_info()
    read_images_as_PIL_objs()
    transform_data_for_modeling(mmcq_quality)
    export_csv_files()

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
    data_info, all_names = tuple(DATA_INFO.values())
    for dataset in data_info:
        id, csv_path, _, cols = tuple(dataset.values())
        csv_path = PROJECT_PATH + "/" + csv_path

        df = pd.read_csv(csv_path, usecols=cols, na_values=[-99,-999,-9999])
        if "SubmergedBool" in df.columns:
            df = df.astype({"SubmergedBool": bool})

        df.rename(columns= {"DataDateTime": "Timestamp"}, inplace=True)
        df.Timestamp = pd.to_datetime(df.Timestamp)
        df.set_index("Timestamp", drop=True, inplace=True)
        
        cols = list(df.columns)
        names = {k: all_names[k] for k in cols}
        df = df.rename(columns=names)

        DATASETS.update({id: df})

def read_images_as_PIL_objs() -> None:
    """
    Load image data corresponding to each .csv file into PIL Image objects and
    store in IMAGE_SETS by 'id'.
    """
    global IMAGE_SETS
    data_info, _ = tuple(DATA_INFO.values())
    xlsx = pd.ExcelFile(IMAGE_DETAILS_PATH)
    
    for dataset in data_info:
        id = dataset["id"]
        im_directory_path =\
              PROJECT_PATH + "/" + dataset["im_directory_path"]
        ims = get_image_details(xlsx, im_directory_path)
        ims["Filename"] = ims.apply(
            lambda row: im_directory_path + row["Filename"], axis=1)

        ims["Image_array"] = ims.apply(
            lambda row: 
                Image.open(
                    row["Filename"]
                    )
                if path.isfile(row["Filename"]) else None,
            axis=1
            )
        ims.dropna(inplace=True)

        ims.rename(columns={"DeviceDateTime": "Timestamp"}, inplace=True)
        ims.Timestamp = pd.to_datetime(ims.Timestamp)
        ims.set_index("Timestamp", drop=True, inplace=True)

        IMAGE_SETS.update({id: ims})

def transform_data_for_modeling(qual_level: int) -> None:
    global TRANSFORMED_DATA

    # 'r1', 'g1', 'b1' represent most dominant color; 
    # 'r2', 'g2', 'b2' the second.

    # qual_level: range 1-10
    # 1 is highest quality i.e. every image pixel is accounted for 
    # vs. 
    # 10 is lowest quality i.e. only every tenth pixel is accounted for.

    channels = ("r1", "g1", "b1", "r2", "g2", "b2")

    not_int = not isinstance(qual_level, int)
    val_oob = qual_level < 1 or qual_level > 10
    if not_int or val_oob:
        print("Quality level must be int between 1 and 10; set qual_level=1")
        qual_level = 1

    # Column columns that appear in every buoy set
    ds = list(DATASETS.values())
    common_features = set.intersection(
        set(ds[0].columns.values.tolist()),
        set(ds[1].columns.values.tolist()),
        set(ds[2].columns.values.tolist()),
        set(ds[3].columns.values.tolist()),
        set(ds[4].columns.values.tolist()),
        set(ds[5].columns.values.tolist())
        )

    transformed_sets = []
    for set_id in DATASETS.keys():
        print(f"Starting {set_id}...")
           
        # Copy data
        data = DATASETS[set_id].copy(deep=True)
        filenames = IMAGE_SETS[set_id]["Filename"].copy(deep=True)
        
        # Prune features to those common to all buoy experiments.
        data = data.reindex(list(common_features), axis="columns")
        chl = data["chl_fluorometer"].rename("chl")
        common_predictors = data.drop("chl_fluorometer", axis=1)
        
        # Condense response observations to 1-wide averages around image 
        # DateTime.
        condensed_response = condense_data_obs(1, chl, filenames)

        # Condense common factors as above.
        condensed_features_series = []
        for col in common_predictors:
            c_f_s = condense_data_obs(1, data[col], filenames)
            c_f_s.index = condensed_response.index.copy()
            condensed_features_series.append(c_f_s)
        condensed_features = pd.concat(condensed_features_series, axis=1)

        # Pull rgb channels of the two dominant colors of each image.
        ct = filenames.apply(ColorThief)
        dominant_colors = pd.DataFrame(
            [get_2_most_dominant(im, quality=qual_level) for im in ct], 
            columns=channels,
            index=condensed_response.index.copy()
            )
        
        # Move DateTime from index to new column.
        transformed = pd.concat(
            [condensed_response, filenames, condensed_features, dominant_colors], axis=1)
        transformed.reset_index(inplace=True)

        # Merge and add to list.
        transformed_sets.append(transformed)

    # Stack data vertically
    TRANSFORMED_DATA = pd.concat(
        transformed_sets, 
        axis=0
    ).reset_index(drop=True, names="Timestamp")

    # Convert DateTime to seconds passed since the beginning of that year
    TRANSFORMED_DATA["month_day_time_int"] = \
        TRANSFORMED_DATA["Timestamp"].apply(
        lambda x: int(
            (x.value - jan_1_12am(x.year))/10e9
            )
    )

def export_csv_files() -> None:
    cnn_modeling_data = TRANSFORMED_DATA.loc[:,["chl", "Filename"]]
    cnn_modeling_data.to_csv(
        CLEANED_DATA_PATH + "/cnn_modeling_data.csv",
        index=False
    )

    dominant_color_modeling_data = TRANSFORMED_DATA.copy(deep=True
        ).drop(["Filename"], axis=1)
    dominant_color_modeling_data.to_csv(
        CLEANED_DATA_PATH + "/dominant_color_modeling_data.csv",
        index=False
    )

def get_image_details(
        xlsx: pd.ExcelFile, im_directory_path: str) -> pd.DataFrame:
    """
    Extract image details from excel file and store as DataFrame.

    Get the sheet name by parsing the current image directory path; open
    and return the sheet.

    Parameters
    ----------
        xlsx : pd.ExcelFile
            An Excel workbook containing the image details.
        
        im_directory_path : str
            Path to the current image directory.
    
    Return
    ------
        im_details: pd.DataFrame
            The sheet containing details for the current image directory.
    """
    # f'#{n}', corresponds to buoy number n, i.e. "#8" for Buoy 8
    current_sheet = im_directory_path[-3:-1] 
    im_details = pd.read_excel(xlsx, current_sheet)
    im_details.dropna(axis=1, how='all', inplace=True)
    return im_details

def condense_data_obs(
        k:      int, 
        data:   pd.Series, 
        ims:    pd.Series
        ) ->    pd.Series:
    """"""
    col_name = data.name
    image_datetimes = pd.Series(ims.index)
    
    k_moving_average = image_datetimes.apply(
        lambda image_dt:
            avg_of_k_surrounding_obs(k, data, image_dt)
    )
    k_moving_average.index = ims.index
    k_moving_average.rename(col_name, inplace=True)

    return k_moving_average

def avg_of_k_surrounding_obs(
        k:      int, 
        data:   pd.Series, 
        dt:     pd.Timestamp
        ) ->    pd.Series:
    """"""
    a = b = 0
    i = data.index.get_indexer([dt], method="nearest")
    
    if i < k:
        a = k
    if abs(i - len(data)) < k:
        b = k

    low  = i[0] - k + a     # a accounts for i in the first-k rows of df
    high = i[0] + k - b + 1 # b accounts for i in the last-k rows of df
    k_nearest = data.iloc[low : high]

    avg = k_nearest.mean()    
    return avg

def get_2_most_dominant(ct, quality) -> list[int]:
    palette = ct.get_palette(color_count=2, quality=quality)
    first, second, _ = palette
    r1, g1, b1 = first
    r2, g2, b2 = second
    return [r1, g1, b1, r2, g2, b2]

def jan_1_12am(year: str) -> int: 
    dt_str = f"{year}-01-01 00:00:00"
    dt = pd.to_datetime(dt_str, yearfirst=True)
    return dt.value


def main():
    # run_clean()
    ...

main()