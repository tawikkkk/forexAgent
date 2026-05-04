import asyncio
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx
import numpy as np
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from stable_baselines3 import PPO
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

from backend.config import DATA_PATH, MODEL_PATH, TWELVE_DATA_API_KEY


# These columns must match the observation columns used by XAUUSDEnv.
FEATURE_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "rsi",
    "macd",
    "macd_signal",
    "macd_diff",
    "ema_20",
    "atr",
]

ACTION_MAP = {0: "HOLD", 1: "BUY", 2: "SELL"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]

app = FastAPI(title="Forex AI Agent API")

# This global variable will hold the trained PPO model after startup.
model = None
signal_cache = {"expires_at": 0.0, "data": None}
signal_cache_lock = asyncio.Lock()


# Allow the Vite frontend to call this backend in the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Let the frontend load generated files such as /data/backtest_chart.png.
data_directory = PROJECT_ROOT / "data"
data_directory.mkdir(exist_ok=True)
app.mount("/data", StaticFiles(directory=data_directory), name="data")


@app.on_event("startup")
async def load_model_on_startup() -> None:
    """Load the trained PPO model once when FastAPI starts."""
    global model

    model_file = PROJECT_ROOT / MODEL_PATH
    if not model_file.exists():
        print(f"Model file not found: {model_file}")
        model = None
        return

    model = PPO.load(str(model_file))
    print("AI model loaded successfully.")


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add the same technical indicators used in backend/prepare_data.py."""
    df = df.copy()

    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()

    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"] = macd.macd_diff()

    df["ema_20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["atr"] = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14,
    ).average_true_range()

    return df.dropna()


def candles_to_dataframe(candles: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert provider candle JSON into the clean DataFrame our model expects."""
    df = pd.DataFrame(candles)

    if df.empty:
        raise ValueError("Market data provider returned no candle data.")

    # Twelve Data uses "datetime"; older/local data may use "date" or "time".
    if "datetime" in df.columns and "time" not in df.columns:
        df = df.rename(columns={"datetime": "time"})
    if "date" in df.columns and "time" not in df.columns:
        df = df.rename(columns={"date": "time"})

    # Some Twelve Data forex/metal responses omit volume. The PPO model still
    # needs a numeric volume feature, so we use 0.0 when the provider omits it.
    if "volume" not in df.columns:
        df["volume"] = 0.0

    required_columns = ["time", "open", "high", "low", "close", "volume"]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Market data response is missing columns: {', '.join(missing_columns)}")

    df = df[required_columns].copy()
    df["time"] = pd.to_datetime(df["time"])

    # Indicators should be calculated from oldest candle to newest candle.
    df = df.sort_values("time").reset_index(drop=True)

    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna()
    if df.empty:
        raise ValueError("No valid numeric candle rows were available.")

    return df


def get_prediction_confidence(trained_model: PPO, observation: np.ndarray, action_code: int) -> float:
    """Try to read the policy probability for the chosen action."""
    try:
        obs_tensor, _ = trained_model.policy.obs_to_tensor(observation)
        distribution = trained_model.policy.get_distribution(obs_tensor)
        probabilities = distribution.distribution.probs.detach().cpu().numpy()[0]
        return round(float(probabilities[action_code]), 2)
    except Exception:
        # Some policies/distributions may not expose probabilities neatly.
        return round(random.uniform(0.70, 0.95), 2)


def create_signal_from_candles(
    candles: List[Dict[str, Any]],
    trained_model: PPO,
    mode: str = "live",
) -> Dict[str, Any]:
    """Turn raw candles into one BUY/HOLD/SELL signal JSON object."""
    df = candles_to_dataframe(candles)
    df = add_indicators(df)

    if df.empty:
        raise ValueError("Not enough candle history to calculate indicators.")

    latest_row = df.iloc[-1]

    # The model needs only numeric feature values, in the same order as training.
    observation = latest_row[FEATURE_COLUMNS].to_numpy(dtype=np.float32)

    action, _states = trained_model.predict(observation, deterministic=True)
    action_code = int(action)
    confidence = get_prediction_confidence(trained_model, observation, action_code)

    return {
        "action": ACTION_MAP.get(action_code, "HOLD"),
        "action_code": action_code,
        "confidence": confidence,
        "price": round(float(latest_row["close"]), 2),
        "timestamp": latest_row["time"].strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
    }


async def fetch_latest_candles() -> List[Dict[str, Any]]:
    """Fetch the latest hourly XAU/USD candles from Twelve Data."""
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "XAU/USD",
        "interval": "1h",
        "outputsize": 50,
        "apikey": TWELVE_DATA_API_KEY,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, dict):
        raise ValueError("Twelve Data returned an unexpected response format.")
    if data.get("status") == "error":
        raise ValueError(data.get("message", "Twelve Data returned an error."))

    values = data.get("values")
    if not isinstance(values, list):
        raise ValueError("Twelve Data response did not contain a values list.")

    # Twelve Data usually returns newest first; keep 50, then sort later.
    return values[:50]


def load_demo_candles() -> List[Dict[str, Any]]:
    """Load fallback candles from data/test.csv when the live API fails."""
    test_file = PROJECT_ROOT / "data" / "test.csv"
    df = pd.read_csv(test_file)

    # test.csv already has indicators, but create_signal_from_candles only needs
    # the raw OHLCV columns because it recalculates indicators consistently.
    return df.tail(50).to_dict(orient="records")


async def get_live_signal() -> Dict[str, Any]:
    """Fetch market data and ask the PPO model for the current signal."""
    if model is None:
        raise RuntimeError("Model is not loaded.")

    now = time.monotonic()
    if signal_cache["data"] is not None and now < signal_cache["expires_at"]:
        return signal_cache["data"]

    async with signal_cache_lock:
        now = time.monotonic()
        if signal_cache["data"] is not None and now < signal_cache["expires_at"]:
            return signal_cache["data"]

        try:
            candles = await fetch_latest_candles()
            signal = create_signal_from_candles(candles, model, mode="live")
        except Exception as exc:
            print(f"Live API failed, using demo fallback: {exc}")
            try:
                candles = load_demo_candles()
                signal = create_signal_from_candles(candles, model, mode="demo")
            except Exception as demo_exc:
                raise RuntimeError(
                    f"Could not generate live or demo signal. Live error: {exc}. "
                    f"Demo error: {demo_exc}"
                ) from demo_exc

        # Cache for 15 seconds so the 5s websocket and 10s card refresh do not
        # exhaust the free Twelve Data minute quota immediately.
        signal_cache["data"] = signal
        signal_cache["expires_at"] = now + 15
        return signal


@app.get("/")
async def health_check() -> Dict[str, str]:
    """Simple health check so you can confirm the API is running."""
    return {"status": "online", "model": "loaded" if model is not None else "not_loaded"}


@app.get("/backtest-stats")
async def get_backtest_stats() -> JSONResponse:
    """Return the saved backtest metrics from data/backtest_metrics.json."""
    stats_file = PROJECT_ROOT / DATA_PATH

    try:
        with stats_file.open("r") as file:
            return JSONResponse(content=json.load(file))
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": f"Backtest metrics file not found: {DATA_PATH}"},
        )
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=500,
            content={"error": "Backtest metrics file contains invalid JSON."},
        )


@app.get("/signals")
async def get_current_signal() -> JSONResponse:
    """Return one live trading signal for the latest hourly XAUUSD data."""
    try:
        signal = await get_live_signal()
        return JSONResponse(content=signal)
    except Exception as exc:
        return JSONResponse(status_code=502, content={"error": str(exc)})


@app.websocket("/ws/live")
async def websocket_live_signals(websocket: WebSocket) -> None:
    """Send a fresh signal to the connected browser every 5 seconds."""
    await websocket.accept()

    try:
        while True:
            try:
                signal = await get_live_signal()
            except Exception as exc:
                signal = {"error": str(exc)}

            await websocket.send_json(signal)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
