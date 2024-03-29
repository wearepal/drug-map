import pandas as pd
from pathlib import Path
import numpy as np
from functools import partial
from scipy.stats import percentileofscore

data_path = Path(__file__).parent.parent / "data"

def load_df():
    dfs = {}
    for file in data_path.iterdir():
        dfs[file.name] = pd.read_csv(str(data_path / file), dtype={"FIPS": str})
    return dfs

def confidence_categorization(df: pd.DataFrame, value_col: str, ci_col: str) -> pd.DataFrame:
    def _categorization(v, ci):
        if v - ci > 5:
            return "S>5"
        if v - ci > 2:
            return "S>2"
        if v - ci > 1:
            return "S>1"
        if v + ci < 1:
            return "S<1"
        if v + ci < 0.5:
            return "S<0.5"
        if v + ci < 0.2:
            return "S<0.2"
        return "Low confidence"
    df["cat"] = df.apply(lambda x: _categorization(x[value_col], x[ci_col]), axis=1)
    return df

def confidence_categorization_alt(df: pd.DataFrame, value_col: str, ub_col: str, lb_col: str) -> pd.DataFrame:
    def _categorization(v, lb, ub):
        if lb > 5:
            return "S>5"
        if lb > 2:
            return "S>2"
        if lb > 1:
            return "S>1"
        if ub < 1:
            return "S<1"
        if ub < 0.5:
            return "S<0.5"
        if ub < 0.2:
            return "S<0.2"
        return "Low confidence"
    df["cat"] = df.apply(lambda x: _categorization(x[value_col], x[lb_col], x[ub_col]), axis=1)
    return df

def republican_categorization(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    def _categorization(v):
        if v < 0.2:
            return "<20%"
        if v < 0.4:
            return "20-40%"
        if v < 0.6:
            return "40-60%"
        if v < 0.8:
            return "60-80%"
        if v <= 1:
            return "80-100%"
        return ">100% ???"
    df["prop_republican"] = df.apply(lambda x: _categorization(x[value_col]), axis=1)
    return df

def add_quantiles(df: pd.DataFrame, quantile_col: str, output_col: str, q: int = 4) -> pd.DataFrame:
    vals = np.nan_to_num(df[quantile_col])
    dq = np.quantile(vals, q=np.linspace(0, 1, q + 1)[1:])
    quantile_conv = lambda x: int(percentileofscore(dq, x, kind="weak"))
    df[output_col] = [quantile_conv(vi) for vi in vals]
    return df

  
def additions(df: pd.DataFrame) -> pd.DataFrame:
    if "ci" in df.columns:
        df = confidence_categorization(df, "selection_ratio", "ci")
    elif "lb" in df.columns:
        df = confidence_categorization_alt(df, "selection_ratio", "ub", "lb")
        
    election = pd.read_csv(data_path / "election_results_x_county.csv", dtype={"FIPS": str}, usecols=["year", "FIPS", "perc_republican_votes"])
    
    election = election[election.year == 2020]
    
    election = election.drop(columns={"year"})
    
    df = df.merge(election, on="FIPS", how="left")
    
    df = republican_categorization(df, "perc_republican_votes")
    
    df["perc_republican_votes"] = (df["perc_republican_votes"] * 100).astype(int)

    df["frequency"] = df["frequency"].apply(lambda x: f'{int(x):,}')
    df["bwratio"] = df["bwratio"].apply(lambda x: f'{x:.3f}')
    
    if "ci" in df.columns:
        df["slci"] = df["selection_ratio"].round(3).astype(str) + " ± " + df["ci"].round(3).astype(str)
    elif "lb" in df.columns:
        df["slci"] = df["selection_ratio"].round(3).astype(str) + "(" + df["lb"].round(3).astype(str) + " - " + df["ub"].round(3).astype(str) + ")"

    df["selection_ratio_log10"] = np.log10(df["selection_ratio"])
    
    df = add_quantiles(df, "selection_ratio", "quantiles", q=4)
    df = add_quantiles(df, "selection_ratio", "percentiles", q=100)
    
    df["selection_ratio"] = df["selection_ratio"].apply(lambda x: f'{x:.3f}')
    
    return df

if __name__ == "__main__":
    for file in (data_path / "raw").iterdir():
        if "selection" not in str(file):
            continue
        df = additions(pd.read_csv(str(file), dtype={"FIPS": str}))
        df.to_csv(data_path / file.name, index=False)
