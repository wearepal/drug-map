from typing import List
import pandas as pd
import plotly as py
import plotly.express as px
import numpy as np

import functools
from pathlib import Path
from urllib.request import urlopen
import json

data_path = Path(__file__).parent.parent / "data"


def load_df():
    dfs = {}
    for file in data_path.iterdir():
        if file.is_dir():
            continue
        dfs[file.name] = pd.read_csv(str(data_path / file), dtype={"FIPS": str})
    return dfs


data_dict = load_df()


def disjunction(*conditions):
    """
    Function which takes a list of conditions and returns the logical OR of them.
    """
    return functools.reduce(np.logical_or, conditions)


def args_to_df(
    drug_type: str,
    citype: str,
    model: str,
    smoothed: bool,
    year: int = 2019,
    republican_cats: List[str] = ["<20%", "20-40%", "40-60%", "60-80%", "80-100%"],
    urban_filter: str = "2",
    smoothing_param: float = 1.0,
    usage_target: str = "using",
) -> pd.DataFrame:
    if citype == "wilson":
        filename = f"selection_ratio_county_2012-2019_{citype}"
    else:
        filename = f"selection_ratio_county_2012-2019_bootstraps_1000"
    if model == "poverty":
        filename += "_poverty"
    elif model == "urban":
        filename += "_urban"
    if urban_filter != "2":
        filename += f"_urban_filter_{urban_filter}"
    if smoothed:
        filename += "_smoothed"
    if smoothing_param != 1.0:
        filename += f"_{str(smoothing_param).replace('.', '-')}"
    if usage_target != "using":
        filename += f"_{usage_target}"
    df = data_dict[filename + ".csv"]
    df = df[df["year"] == year]
    df = df[disjunction(*[df.prop_republican == rc for rc in republican_cats])]
    return df
