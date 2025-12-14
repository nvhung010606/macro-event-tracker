import pandas as pd
import os

EVENTS_FILE = "data/raw/events.csv"
MARKETS_FILE = "data/processed/markets_features.parquet"
OUTFILE = "data/processed/event_panel.parquet"

def main():
    events = pd.read_csv(EVENTS_FILE)
    events["event_date"] = pd.to_datetime(events["event_date"])

    m = pd.read_parquet(MARKETS_FILE)
    m["date"] = pd.to_datetime(m["date"])
    m = m.sort_values("date")

    # exact-date join first (good for v1)
    panel = events.merge(m, left_on="event_date", right_on="date", how="left")

    os.makedirs("data/processed", exist_ok=True)
    panel.to_parquet(OUTFILE, index=False)
    panel.to_csv("outputs/event_panel.csv", index=False)

    print("Saved", OUTFILE, "and outputs/event_panel.csv")
    print("Rows missing market match:", panel["severity_1d"].isna().sum())
    print(panel[["event_date","event_name","category","severity_1d","spx_ret_1d","vix_chg_1d","y10_chg_1d_bps"]].head(10))

if __name__ == "__main__":
    main()
