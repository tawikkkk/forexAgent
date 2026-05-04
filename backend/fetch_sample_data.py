import yfinance as yf
import pandas as pd
import os

def fetch_xauusd_data():
    print("Fetching XAU/USD (Gold Futures) data from Yahoo Finance...")
    data = yf.download("GC=F", start="2020-01-01", end="2026-05-01", interval="1d")
    
    if data.empty:
        print("Failed to fetch data. Using dummy data...")
        date_rng = pd.date_range(start='2020-01-01', end='2026-01-01', freq='D')
        data = pd.DataFrame({'time': date_rng})
        data['open'] = 1800.0
        data['high'] = 1810.0
        data['low'] = 1790.0
        data['close'] = 1805.0
        data['volume'] = 1000
    else:
        # Handle yfinance multi-index if necessary
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        data = data.reset_index()
        data.columns = [col.lower() for col in data.columns]
        data = data.rename(columns={'date': 'time'})
    
    # Ensure columns exist as requested: time, open, high, low, close, volume
    required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
    data = data[required_cols]
    
    os.makedirs("../data/raw", exist_ok=True)
    data.to_csv("../data/raw/xauusd.csv", index=False)
    print(f"Data saved to data/raw/xauusd.csv ({len(data)} rows)")

if __name__ == "__main__":
    fetch_xauusd_data()
