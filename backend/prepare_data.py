import pandas as pd
import os
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange

def prepare_data():
    print("Preparing data...")
    raw_path = "../data/raw/xauusd.csv"
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found.")
        return

    df = pd.read_csv(raw_path)
    
    # Ensure correct columns
    required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Missing column {col}")
            return

    # Add Indicators
    print("Adding indicators (RSI, MACD, EMA, ATR)...")
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    
    df['ema_20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
    
    df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range()

    # Remove null rows (indicators create some at the start)
    initial_len = len(df)
    df = df.dropna()
    print(f"Removed {initial_len - len(df)} null rows.")

    # Split 80% train / 20% test
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    # Save to CSV
    train_df.to_csv("../data/train.csv", index=False)
    test_df.to_csv("../data/test.csv", index=False)
    
    print(f"Data pipeline complete.")
    print(f"Training set: {len(train_df)} rows")
    print(f"Testing set: {len(test_df)} rows")

if __name__ == "__main__":
    prepare_data()
