import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class XAUUSDEnv(gym.Env):
    """Custom Gymnasium environment for XAUUSD Trading"""
    metadata = {"render_modes": ["human"]}

    def __init__(self, df, initial_balance=10000):
        super(XAUUSDEnv, self).__init__()
        
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        
        # Actions: 0=Hold, 1=Buy, 2=Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation: Price + Indicators
        # Columns: open, high, low, close, volume, rsi, macd, macd_signal, macd_diff, ema_20, atr
        self.features = ['open', 'high', 'low', 'close', 'volume', 'rsi', 'macd', 'macd_signal', 'macd_diff', 'ema_20', 'atr']
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(len(self.features),), dtype=np.float32
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0 # 0=None, 1=Long, -1=Short
        self.entry_price = 0
        self.total_reward = 0
        self.done = False
        self.steps_held = 0
        self.steps_inactive = 0
        
        observation = self._get_observation()
        info = {}
        
        return observation, info

    def _get_observation(self):
        obs = self.df.loc[self.current_step, self.features].values.astype(np.float32)
        return obs

    def step(self, action):
        self.current_step += 1
        
        if self.current_step >= len(self.df) - 1:
            self.done = True
            
        current_price = self.df.loc[self.current_step, 'close']
        reward = 0
        
        # Logic for actions
        if action == 1: # BUY
            if self.position <= 0:
                # If short, close it first
                if self.position == -1:
                    trade_pnl = (self.entry_price - current_price)
                    reward += trade_pnl
                    reward += 0.5 # Reward for completing a trade
                    self.steps_held = 0
                self.position = 1
                self.entry_price = current_price
                self.steps_inactive = 0
        elif action == 2: # SELL
            if self.position >= 0:
                # If long, close it first
                if self.position == 1:
                    trade_pnl = (current_price - self.entry_price)
                    reward += trade_pnl
                    reward += 0.5 # Reward for completing a trade
                    self.steps_held = 0
                self.position = -1
                self.entry_price = current_price
                self.steps_inactive = 0
        elif action == 0: # HOLD
            self.steps_inactive += 1
            if self.position != 0:
                self.steps_held += 1
            
            # Penalty for inaction (every 5 steps)
            if self.steps_inactive % 5 == 0:
                reward -= 0.1
                
            # Penalty for holding a losing position too long (> 20 steps)
            if self.steps_held > 20:
                current_pnl = 0
                if self.position == 1:
                    current_pnl = current_price - self.entry_price
                elif self.position == -1:
                    current_pnl = self.entry_price - current_price
                
                if current_pnl < 0:
                    reward -= 0.5

        # Adjust balance by reward (only actual trade pnl for balance)
        # Note: reward variable here includes penalties/incentives for RL
        # Real balance only reflects trade outcomes
        
        observation = self._get_observation()
        terminated = self.done
        truncated = False
        
        info = {
            'balance': self.balance,
            'position': self.position,
            'step': self.current_step
        }
        
        return observation, reward, terminated, truncated, info

    def render(self):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Position: {self.position}")
