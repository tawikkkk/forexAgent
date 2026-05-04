import unittest

import pandas as pd

try:
    from environment import XAUUSDEnv
except ModuleNotFoundError:
    from backend.agent.environment import XAUUSDEnv


class XAUUSDEnvTests(unittest.TestCase):
    def test_hold_penalty_applies_every_five_inactive_steps(self):
        df = pd.DataFrame(
            {
                "open": [100.0] * 8,
                "high": [101.0] * 8,
                "low": [99.0] * 8,
                "close": [100.0] * 8,
                "volume": [1000.0] * 8,
                "rsi": [50.0] * 8,
                "macd": [0.0] * 8,
                "macd_signal": [0.0] * 8,
                "macd_diff": [0.0] * 8,
                "ema_20": [100.0] * 8,
                "atr": [1.0] * 8,
            }
        )
        env = XAUUSDEnv(df)
        env.reset()

        rewards = []
        for _ in range(5):
            _, reward, _, _, _ = env.step(0)
            rewards.append(reward)

        self.assertEqual(rewards[:4], [0, 0, 0, 0])
        self.assertAlmostEqual(rewards[4], -0.1)


if __name__ == "__main__":
    unittest.main()
