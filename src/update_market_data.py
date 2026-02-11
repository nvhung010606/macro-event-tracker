"""
Automated Market Data Updater
Fetches daily SPX, VIX, and Treasury yields
Updates the markets_features.parquet file
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Try to import optional dependencies
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not installed. Run: pip install yfinance")

try:
    from fredapi import Fred
    FREDAPI_AVAILABLE = True
except ImportError:
    FREDAPI_AVAILABLE = False
    print("⚠️  fredapi not installed. Run: pip install fredapi")

# Configuration
MARKETS_FILE = "data/processed/markets_features.parquet"
START_DATE = "2020-01-01"  # Fetch from this date
OUTPUT_DIR = "data/processed"

def get_fred_api():
    """Get FRED API client"""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from config import FRED_API_KEY
            api_key = FRED_API_KEY
        except:
            pass

    if api_key and FREDAPI_AVAILABLE:
        return Fred(api_key)
    return None

def fetch_yahoo_data(ticker, start_date):
    """Fetch data from Yahoo Finance"""
    if not YFINANCE_AVAILABLE:
        return None

    try:
        print(f"   Fetching {ticker} from Yahoo Finance...")
        data = yf.download(ticker, start=start_date, progress=False)
        if len(data) == 0:
            return None

        # Return closing prices as a Series
        if 'Close' in data.columns:
            result = data['Close']
        elif isinstance(data.columns, pd.MultiIndex):
            result = data[('Close', ticker)]
        else:
            result = data.iloc[:, 0]  # First column

        # Ensure it's a Series with DatetimeIndex
        if isinstance(result, pd.DataFrame):
            result = result.squeeze()  # Convert single-column DataFrame to Series

        return result
    except Exception as e:
        print(f"   ⚠️  Error fetching {ticker}: {e}")
        return None

def fetch_fred_data(series_id, fred_client, start_date):
    """Fetch data from FRED"""
    if not fred_client:
        return None

    try:
        print(f"   Fetching {series_id} from FRED...")
        data = fred_client.get_series(series_id, observation_start=start_date)
        return data
    except Exception as e:
        print(f"   ⚠️  Error fetching {series_id}: {e}")
        return None

def calculate_features(df):
    """Calculate technical features"""
    print("\n   Calculating features...")

    # Returns
    df['spx_ret_1d'] = df['spx'].pct_change() * 100
    df['spx_ret_5d'] = df['spx'].pct_change(5) * 100
    df['spx_ret_30d'] = df['spx'].pct_change(30) * 100

    # VIX changes
    df['vix_chg_1d'] = df['vix'].diff()
    df['vix_chg_5d'] = df['vix'].diff(5)

    # Yield changes (in basis points)
    df['y10_chg_1d_bps'] = df['y10'].diff() * 100
    df['y10_chg_5d_bps'] = df['y10'].diff(5) * 100

    # Severity score (combining multiple indicators)
    # High severity = big SPX drop + VIX spike + yield movement
    df['severity_1d'] = (
        abs(df['spx_ret_1d']) * 0.5 +
        abs(df['vix_chg_1d']) * 0.3 +
        abs(df['y10_chg_1d_bps']) * 0.2
    )

    df['severity_5d'] = (
        abs(df['spx_ret_5d']) * 0.5 +
        abs(df['vix_chg_5d']) * 0.3 +
        abs(df['y10_chg_5d_bps']) * 0.2
    )

    return df

def update_market_data():
    """Main function to update market data"""
    print("\n" + "="*70)
    print("📊 AUTOMATED MARKET DATA UPDATE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize FRED client
    fred = get_fred_api()

    # Fetch data
    print("\n🔍 Fetching market data...")

    # SPX
    spx = fetch_yahoo_data("^GSPC", START_DATE)

    # VIX
    vix = fetch_yahoo_data("^VIX", START_DATE)

    # 10Y Treasury Yield
    y10 = fetch_fred_data("DGS10", fred, START_DATE) if fred else None

    # Check what we got
    if spx is None:
        print("\n❌ ERROR: Could not fetch S&P 500 data")
        return False

    if vix is None:
        print("\n⚠️  WARNING: Could not fetch VIX data")

    if y10 is None:
        print("\n⚠️  WARNING: Could not fetch 10Y yield data")

    # Combine into DataFrame
    print("\n🔄 Combining data...")

    # Start with SPX (convert Series to DataFrame)
    df = spx.reset_index()
    df.columns = ['date', 'spx']
    df['date'] = pd.to_datetime(df['date'])

    if vix is not None:
        vix_df = vix.reset_index()
        vix_df.columns = ['date', 'vix']
        vix_df['date'] = pd.to_datetime(vix_df['date'])
        df = df.merge(vix_df, on='date', how='left')

    if y10 is not None:
        y10_df = y10.reset_index()
        y10_df.columns = ['date', 'y10']
        y10_df['date'] = pd.to_datetime(y10_df['date'])
        df = df.merge(y10_df, on='date', how='left')

    # Forward fill missing values (markets closed on weekends)
    df = df.ffill()

    # Calculate features
    df = calculate_features(df)

    # Drop rows with NaN (early rows before enough data for calculations)
    df = df.dropna()

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save daily version
    df.to_parquet(f"{OUTPUT_DIR}/markets_daily.parquet", index=False)

    # Save features version (what the pipeline uses)
    df.to_parquet(MARKETS_FILE, index=False)

    print(f"\n✅ SUCCESS!")
    print(f"   Saved: {MARKETS_FILE}")
    print(f"   Rows: {len(df)}")
    print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"   Latest SPX: ${df['spx'].iloc[-1]:.2f}")
    if 'vix' in df.columns:
        print(f"   Latest VIX: {df['vix'].iloc[-1]:.2f}")
    if 'y10' in df.columns:
        print(f"   Latest 10Y: {df['y10'].iloc[-1]:.2f}%")

    print("\n" + "="*70)
    return True

def main():
    """Run the update"""
    success = update_market_data()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
