import os
import pandas as pd
from fredapi import Fred

START = "2005-01-01"
END = None

SERIES = {
    "spx": "SP500",
    "vix": "VIXCLS",
    "y10": "DGS10",
}

def main():
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing FRED_API_KEY. In the terminal run:\n"
            "export FRED_API_KEY='YOUR_KEY'"
        )

    fred = Fred(api_key=api_key)

    frames = []
    for col, sid in SERIES.items():
        s = fred.get_series(sid, observation_start=START, observation_end=END)
        frames.append(s.rename(col).to_frame())

    df = pd.concat(frames, axis=1)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index().reset_index().rename(columns={"index": "date"})

    os.makedirs("data/processed", exist_ok=True)
    df.to_parquet("data/processed/markets_daily.parquet", index=False)

    print("Saved data/processed/markets_daily.parquet")
    print(df.head())
    print("Missing values:")
    print(df.isna().sum())

if __name__ == "__main__":
    main()
