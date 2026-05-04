import unittest

import pandas as pd
from fastapi.testclient import TestClient

from backend import config
from backend.main import app, create_signal_from_candles


class FakeModel:
    def predict(self, observation, deterministic=True):
        return 1, None


class FastAPISignalTests(unittest.TestCase):
    def test_config_paths_match_project_layout(self):
        self.assertEqual(config.MODEL_PATH, "backend/agent/xauusd_agent.zip")
        self.assertEqual(config.DATA_PATH, "data/backtest_metrics.json")

    def test_health_endpoint_reports_model_key(self):
        client = TestClient(app)

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())
        self.assertIn("model", response.json())

    def test_create_signal_from_candles_returns_expected_shape(self):
        candles = []
        for index in range(60):
            price = 2300 + index
            candles.append(
                {
                    "date": f"2026-05-02 {index % 24:02d}:00:00",
                    "open": price,
                    "high": price + 2,
                    "low": price - 2,
                    "close": price + 1,
                    "volume": 1000 + index,
                }
            )

        signal = create_signal_from_candles(candles, FakeModel())

        self.assertEqual(signal["action"], "BUY")
        self.assertEqual(signal["action_code"], 1)
        self.assertIn("confidence", signal)
        self.assertIsInstance(signal["price"], float)
        self.assertIn("timestamp", signal)
        self.assertEqual(signal["mode"], "live")

    def test_create_signal_from_twelve_data_values(self):
        candles = []
        for index in range(60):
            price = 2300 + index
            candles.append(
                {
                    "datetime": f"2026-05-02 {index % 24:02d}:00:00",
                    "open": str(price),
                    "high": str(price + 2),
                    "low": str(price - 2),
                    "close": str(price + 1),
                    "volume": str(1000 + index),
                }
            )

        signal = create_signal_from_candles(candles, FakeModel())

        self.assertEqual(signal["action"], "BUY")
        self.assertEqual(signal["action_code"], 1)
        self.assertEqual(signal["mode"], "live")
        self.assertIsInstance(signal["price"], float)

    def test_twelve_data_values_can_omit_forex_volume(self):
        candles = []
        for index in range(60):
            price = 2300 + index
            candles.append(
                {
                    "datetime": f"2026-05-02 {index % 24:02d}:00:00",
                    "open": str(price),
                    "high": str(price + 2),
                    "low": str(price - 2),
                    "close": str(price + 1),
                }
            )

        signal = create_signal_from_candles(candles, FakeModel())

        self.assertEqual(signal["action"], "BUY")
        self.assertEqual(signal["mode"], "live")


if __name__ == "__main__":
    unittest.main()
