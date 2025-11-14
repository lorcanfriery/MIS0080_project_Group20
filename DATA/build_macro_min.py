import pandas as pd
from pathlib import Path

DATA_DIR = Path("DATA")
GDP_FILE = DATA_DIR / "gdp_data.csv"  
INF_FILE = DATA_DIR / "inf_data.csv"
OUT_FILE = DATA_DIR / "macro_data.csv"

START_YEAR = 2000
END_YEAR = 2024

def read_wb_wide(path: Path, value_name: str) -> pd.DataFrame:
    last_err = None
    for skip in (4, 3, 0):
        try:
            df = pd.read_csv(
                path,
                skiprows=skip,
                sep=",",
                encoding="utf-8-sig",
                na_values=[".."]
            )
            if {"Country Name", "Country Code"}.issubset(df.columns):
                break
        except Exception as e:
            last_err = e
            df = None
    if df is None or not {"Country Name", "Country Code"}.issubset(df.columns):
        raise RuntimeError(
            f"Could not read World Bank file {path}. "
            f"Tried skiprows 4/3/0. Last error: {last_err}"
        )

  
    year_cols = [c for c in df.columns if str(c).isdigit()]
    if not year_cols:
        raise RuntimeError(f"No year columns found in {path}.")

    long_df = df.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=year_cols,
        var_name="year",
        value_name=value_name
    )
    long_df = long_df.rename(columns={"Country Name": "country", "Country Code": "iso3c"})
    long_df["year"] = long_df["year"].astype(int)
    long_df = long_df[(long_df["year"] >= START_YEAR) & (long_df["year"] <= END_YEAR)]
    return long_df


def main():

    gdp_df = read_wb_wide(GDP_FILE, "gdp_growth")
    inf_df = read_wb_wide(INF_FILE, "inflation")

    # merge on country code and year
    merged = pd.merge(gdp_df, inf_df, on=["iso3c", "year"], how="outer", suffixes=("", "_inf"))

    # fill missing country names
    if "country_inf" in merged.columns:
        merged["country"] = merged["country"].fillna(merged["country_inf"])
        merged = merged.drop(columns=["country_inf"], errors="ignore")

    # reorder columns
    merged = merged[["country", "iso3c", "year", "gdp_growth", "inflation"]].sort_values(["iso3c", "year"])

    # save the new tidy file
    merged.to_csv(OUT_FILE, index=False)
    print(f"✅ Saved {OUT_FILE} (rows={len(merged)})")

if __name__ == "__main__":
    main()





