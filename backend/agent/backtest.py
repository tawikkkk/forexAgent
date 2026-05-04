import pandas as pd
import numpy as np
import vectorbt as vbt
from stable_baselines3 import PPO
from environment import XAUUSDEnv
import matplotlib.pyplot as plt
import os
import json

def run_backtest():
    print("Loading test data...")
    test_df = pd.read_csv("../../data/test.csv")
    
    print("Loading trained model...")
    model = PPO.load("xauusd_agent")
    
    print("Running model on test data...")
    env = XAUUSDEnv(test_df)
    obs, info = env.reset()
    
    actions = []
    done = False
    while not done:
        action, _states = model.predict(obs, deterministic=True)
        actions.append(action)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated

    # Align actions with test data
    test_df_subset = test_df.iloc[:len(actions)]
    
    # Map actions to vectorbt signals
    entries = pd.Series([a == 1 for a in actions])
    exits = pd.Series([a == 2 for a in actions])
    
    print("Generating vectorbt portfolio...")
    portfolio = vbt.Portfolio.from_signals(
        test_df_subset['close'],
        entries,
        exits,
        init_cash=10000,
        fees=0.001,
        freq='1D'
    )
    
    # Calculate Metrics
    stats = portfolio.stats()
    print("\n--- Backtest Results ---")
    print(stats)
    
    # Calculate custom win rate if stats is buggy or for verification
    total_trades = int(stats['Total Trades'])
    win_rate = 0
    if total_trades > 0:
        # vectorbt 'Win Rate [%]' can sometimes be NaN if only open trades exist
        # or if it's calculated differently. Let's use a robust approach.
        win_rate = float(stats['Win Rate [%]'])
        if np.isnan(win_rate) and stats['Total Return [%]'] > 0 and total_trades == 1:
            win_rate = 100.0
        elif np.isnan(win_rate):
            win_rate = 0.0

    # Save metrics to JSON for the dashboard
    results = {
        "total_return": float(stats['Total Return [%]']),
        "win_rate": win_rate,
        "max_drawdown": float(stats['Max Drawdown [%]']),
        "sharpe_ratio": float(stats['Sharpe Ratio']) if not np.isnan(stats['Sharpe Ratio']) else 0.0,
        "total_trades": total_trades
    }
    
    os.makedirs("../../data", exist_ok=True)
    with open("../../data/backtest_metrics.json", "w") as f:
        json.dump(results, f)
    
    print("Saving equity curve chart using matplotlib...")
    plt.figure(figsize=(12, 6))
    plt.plot(portfolio.value().values, color='#00d2ff', linewidth=2)
    plt.title("XAUUSD AI Agent Equity Curve", color='white', fontsize=14)
    plt.xlabel("Days", color='white')
    plt.ylabel("Balance ($)", color='white')
    plt.grid(True, alpha=0.2)
    
    # Dark theme styling
    plt.gcf().set_facecolor('#0a0b10')
    plt.gca().set_facecolor('#0a0b10')
    plt.gca().spines['bottom'].set_color('white')
    plt.gca().spines['top'].set_color('white')
    plt.gca().spines['right'].set_color('white')
    plt.gca().spines['left'].set_color('white')
    plt.gca().tick_params(colors='white')
    
    plt.savefig("../../data/backtest_chart.png", facecolor='#0a0b10')
    plt.close()

    print(f"Backtest complete. Metrics and Chart saved.")
    return results

if __name__ == "__main__":
    run_backtest()
