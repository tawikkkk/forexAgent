import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

class TradingAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def analyze_market(self, pair, price_history):
        if not self.model:
            return {
                "signal": "NEUTRAL",
                "confidence": 0.5,
                "reasoning": "AI Model not configured. Please add GEMINI_API_KEY to .env"
            }

        prompt = f"""
        You are a professional Forex Trading AI Agent.
        Analyze the following price data for {pair} and provide a trading signal.
        
        Recent Price History:
        {json.dumps(price_history, indent=2)}
        
        Provide your response in JSON format:
        {{
            "signal": "BUY" | "SELL" | "NEUTRAL",
            "confidence": float (0.0 to 1.0),
            "reasoning": "short explanation of technical/sentiment analysis",
            "target_price": float,
            "stop_loss": float
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Basic JSON extraction (assuming the model returns clean JSON)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            return {
                "signal": "ERROR",
                "reasoning": f"AI Error: {str(e)}"
            }

trading_agent = TradingAgent()
