import random
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class ForexService:
    def __init__(self):
        self.api_key = os.getenv("FMP_API_KEY")
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.mock_prices = {
            "EUR/USD": 1.0850,
            "GBP/USD": 1.2640,
            "USD/JPY": 151.20,
            "AUD/USD": 0.6530,
            "USD/CAD": 1.3580,
        }

    def get_latest_prices(self):
        if not self.api_key:
            # Generate mock movement
            for pair in self.mock_prices:
                change = random.uniform(-0.0005, 0.0005)
                self.mock_prices[pair] += change
            return self.mock_prices

        try:
            # Real API call if key exists
            pairs = ",".join(self.mock_prices.keys()).replace("/", "")
            response = requests.get(f"{self.base_url}/quote/{pairs}?apikey={self.api_key}")
            data = response.json()
            prices = {item['symbol']: item['price'] for item in data}
            return prices
        except Exception as e:
            print(f"Error fetching real prices: {e}")
            return self.mock_prices

forex_service = ForexService()
