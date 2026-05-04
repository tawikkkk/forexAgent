import pandas as pd
from stable_baselines3 import PPO
from environment import XAUUSDEnv
import os

def train_model():
    print("Loading training data...")
    train_df = pd.read_csv("../../data/train.csv")
    
    print("Initializing environment...")
    env = XAUUSDEnv(train_df)
    
    print("Setting up PPO model...")
    # Using MlpPolicy for simple feature vector observations
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1, 
        learning_rate=0.0003,
        n_steps=1024,
        batch_size=64,
        ent_coef=0.02 # Encourage exploration
    )
    
    print("Starting training for 500,000 timesteps...")
    # This might take a few minutes
    model.learn(total_timesteps=500000)
    
    print("Saving model...")
    model.save("xauusd_agent")
    print("Model saved as backend/agent/xauusd_agent.zip")

if __name__ == "__main__":
    train_model()
