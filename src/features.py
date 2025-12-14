import os
import pandas as pd

INFILE = "data/processed/markets_daily.parquet"
OUTFILE = "data/processed/markets_features.parquet"

def zscore(s: pd.Series) -> pd.Series:
    mu = s.mean()
    sd = s.std(ddof=0)
    if sd == 0 or pd.isna(sd):
        return s * 0
    return (s - mu) / sd

def main():
    df = pd.read_parquet(INFILE).copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Keep only rows where all core series exist
    df = df.dropna(subset=["spx", "vix", "y10"]).reset_index(drop=True)

    # 1-day reactions
    df["spx_ret_1d"] = df["spx"].pct_change()
    df["vix_chg_1d"] = df["vix"].diff()
    df["y10_chg_1d_bps"] = df["y10"].diff() * 100

    # 1-day magnitudes + z-scores
    df["spx_mag_1d"] = df["spx_ret_1d"].abs()
    df["vix_mag_1d"] = df["vix_chg_1d"].abs()
    df["y10_mag_1d"] = df["y10_chg_1d_bps"].abs()

    df["spx_z_1d"] = zscore(df["spx_mag_1d"])
    df["vix_z_1d"] = zscore(df["vix_mag_1d"])
    df["y10_z_1d"] = zscore(df["y10_mag_1d"])

    df["severity_1d"] = (df["spx_z_1d"] + df["vix_z_1d"] + df["y10_z_1d"]) / 3

    df["severity"] = df["severity_1d"]  # For backward compatibility

    # 3-day reactions
    df["spx_ret_3d"] = df["spx"].pct_change(3)
    df["vix_chg_3d"] = df["vix"].diff(3)
    df["y10_chg_3d_bps"] = df["y10"].diff(3) * 100

    # 3-day magnitudes + z-scores
    df["spx_mag_3d"] = df["spx_ret_3d"].abs()
    df["vix_mag_3d"] = df["vix_chg_3d"].abs()
    df["y10_mag_3d"] = df["y10_chg_3d_bps"].abs()

    df["spx_z_3d"] = zscore(df["spx_mag_3d"])
    df["vix_z_3d"] = zscore(df["vix_mag_3d"])
    df["y10_z_3d"] = zscore(df["y10_mag_3d"])

    df["severity_3d"] = (df["spx_z_3d"] + df["vix_z_3d"] + df["y10_z_3d"]) / 3

    os.makedirs("data/processed", exist_ok=True)
    df.to_parquet(OUTFILE, index=False)

    print("Saved", OUTFILE)
    print("Date range:", df["date"].min().date(), "to", df["date"].max().date())
    print("Rows:", len(df))
    print(df[["date", "severity_1d", "severity_3d"]].tail(5))

if __name__ == "__main__":
    main()
