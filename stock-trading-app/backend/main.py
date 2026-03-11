"""
Stock Trading Signals API
Real-time chart data with buy/sell signals for scalping
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from signals import SignalEngine
from indicators import TechnicalIndicators

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Trading Signals", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

# Active WebSocket connections per symbol
connections: dict[str, list[WebSocket]] = {}
# Auto trading state per symbol
auto_trade_state: dict[str, dict] = {}


@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")


@app.get("/api/symbols/search")
async def search_symbols(q: str):
    """Search for stock symbols"""
    # Common Japanese and US stocks
    common_symbols = [
        {"symbol": "7203.T", "name": "トヨタ自動車", "exchange": "TSE"},
        {"symbol": "6758.T", "name": "ソニーグループ", "exchange": "TSE"},
        {"symbol": "9984.T", "name": "ソフトバンクグループ", "exchange": "TSE"},
        {"symbol": "6861.T", "name": "キーエンス", "exchange": "TSE"},
        {"symbol": "8306.T", "name": "三菱UFJフィナンシャル", "exchange": "TSE"},
        {"symbol": "9432.T", "name": "NTT", "exchange": "TSE"},
        {"symbol": "4063.T", "name": "信越化学工業", "exchange": "TSE"},
        {"symbol": "6954.T", "name": "ファナック", "exchange": "TSE"},
        {"symbol": "7974.T", "name": "任天堂", "exchange": "TSE"},
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ"},
        {"symbol": "NVDA", "name": "NVIDIA Corp.", "exchange": "NASDAQ"},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "exchange": "NASDAQ"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
        {"symbol": "META", "name": "Meta Platforms", "exchange": "NASDAQ"},
        {"symbol": "SPY", "name": "S&P 500 ETF", "exchange": "NYSE"},
        {"symbol": "QQQ", "name": "Nasdaq 100 ETF", "exchange": "NASDAQ"},
    ]
    q_upper = q.upper()
    results = [
        s for s in common_symbols
        if q_upper in s["symbol"].upper() or q.lower() in s["name"].lower()
    ]
    return results[:10]


@app.get("/api/chart/{symbol}")
async def get_chart_data(
    symbol: str,
    interval: str = "1m",
    period: str = "1d",
    indicators: str = "sma20,sma50,ema9,rsi,macd,bb"
):
    """Get OHLCV chart data with technical indicators and signals"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, period=period)

        if df.empty:
            return {"error": f"No data found for {symbol}"}

        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        if "datetime" in df.columns:
            df = df.rename(columns={"datetime": "date"})
        df["date"] = df["date"].astype(str)

        indicator_list = [i.strip() for i in indicators.split(",")]
        ind_engine = TechnicalIndicators(df)
        signal_engine = SignalEngine(df)

        result_df = ind_engine.calculate(indicator_list)
        signals = signal_engine.generate_signals(indicator_list)

        # Build candlestick data
        candles = []
        for _, row in result_df.iterrows():
            candle = {
                "time": row["date"],
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row["volume"]) if not pd.isna(row["volume"]) else 0,
            }
            # Add indicator values
            for col in result_df.columns:
                if col not in ["date", "open", "high", "low", "close", "volume",
                               "dividends", "stock splits"]:
                    val = row.get(col)
                    if val is not None and not pd.isna(val):
                        candle[col] = round(float(val), 4)
            candles.append(candle)

        # Get current price info
        current = result_df.iloc[-1]
        prev_close = result_df.iloc[-2]["close"] if len(result_df) > 1 else current["close"]
        price_change = float(current["close"]) - float(prev_close)
        price_change_pct = (price_change / float(prev_close)) * 100

        return {
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "current_price": round(float(current["close"]), 2),
            "price_change": round(price_change, 2),
            "price_change_pct": round(price_change_pct, 2),
            "candles": candles,
            "signals": signals,
            "last_updated": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching chart data for {symbol}: {e}")
        return {"error": str(e)}


@app.get("/api/signal/{symbol}")
async def get_current_signal(symbol: str, interval: str = "1m"):
    """Get current buy/sell signal for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, period="1d")

        if df.empty:
            return {"error": "No data"}

        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]

        signal_engine = SignalEngine(df)
        signals = signal_engine.generate_signals(["sma20", "sma50", "ema9", "rsi", "macd", "bb"])

        current_price = float(df.iloc[-1]["close"])
        prev_price = float(df.iloc[-2]["close"]) if len(df) > 1 else current_price
        change_pct = ((current_price - prev_price) / prev_price) * 100

        return {
            "symbol": symbol,
            "price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "signal": signals.get("overall", {}).get("action", "HOLD"),
            "signal_strength": signals.get("overall", {}).get("strength", 0),
            "signals": signals,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ws/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str, interval: str = "1m"):
    """WebSocket endpoint for real-time price updates"""
    await websocket.accept()

    if symbol not in connections:
        connections[symbol] = []
    connections[symbol].append(websocket)

    logger.info(f"WebSocket connected: {symbol}, total: {len(connections[symbol])}")

    try:
        while True:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(interval=interval, period="1d")

                if not df.empty:
                    df = df.reset_index()
                    df.columns = [c.lower() for c in df.columns]

                    ind_engine = TechnicalIndicators(df)
                    signal_engine = SignalEngine(df)
                    result_df = ind_engine.calculate(["sma20", "sma50", "ema9", "rsi", "macd", "bb"])
                    signals = signal_engine.generate_signals(["sma20", "sma50", "ema9", "rsi", "macd", "bb"])

                    current = result_df.iloc[-1]
                    prev = result_df.iloc[-2] if len(result_df) > 1 else current

                    change_pct = ((float(current["close"]) - float(prev["close"])) / float(prev["close"])) * 100

                    # Get latest candle
                    latest_candle = {
                        "time": str(current.get("datetime", current.get("date", ""))),
                        "open": round(float(current["open"]), 2),
                        "high": round(float(current["high"]), 2),
                        "low": round(float(current["low"]), 2),
                        "close": round(float(current["close"]), 2),
                        "volume": int(current["volume"]) if not pd.isna(current["volume"]) else 0,
                    }

                    for col in result_df.columns:
                        if col not in ["datetime", "date", "open", "high", "low", "close",
                                       "volume", "dividends", "stock splits"]:
                            val = current.get(col)
                            if val is not None and not pd.isna(val):
                                latest_candle[col] = round(float(val), 4)

                    message = {
                        "type": "update",
                        "symbol": symbol,
                        "price": round(float(current["close"]), 2),
                        "change_pct": round(change_pct, 2),
                        "candle": latest_candle,
                        "signals": signals,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Check auto trade
                    if symbol in auto_trade_state and auto_trade_state[symbol].get("enabled"):
                        trade_action = check_auto_trade(symbol, signals, float(current["close"]))
                        if trade_action:
                            message["auto_trade"] = trade_action

                    await websocket.send_json(message)

            except Exception as e:
                logger.error(f"Error in WebSocket update for {symbol}: {e}")

            # Update interval based on chart interval
            sleep_time = 5 if interval in ["1m", "2m", "5m"] else 15
            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        connections[symbol].remove(websocket)
        logger.info(f"WebSocket disconnected: {symbol}")


@app.post("/api/auto-trade/{symbol}")
async def configure_auto_trade(symbol: str, config: dict):
    """Configure auto trading settings for a symbol"""
    auto_trade_state[symbol] = {
        "enabled": config.get("enabled", False),
        "strategy": config.get("strategy", "signal_based"),
        "buy_threshold": config.get("buy_threshold", 70),   # Signal strength threshold
        "sell_threshold": config.get("sell_threshold", 70),
        "max_position": config.get("max_position", 100),    # Max shares
        "stop_loss_pct": config.get("stop_loss_pct", 2.0),  # 2% stop loss
        "take_profit_pct": config.get("take_profit_pct", 3.0),  # 3% take profit
        "current_position": 0,
        "entry_price": None,
        "trades": [],
    }
    return {"status": "configured", "symbol": symbol, "config": auto_trade_state[symbol]}


@app.get("/api/auto-trade/{symbol}/status")
async def get_auto_trade_status(symbol: str):
    """Get current auto trading status"""
    if symbol not in auto_trade_state:
        return {"symbol": symbol, "enabled": False}
    return {"symbol": symbol, **auto_trade_state[symbol]}


def check_auto_trade(symbol: str, signals: dict, current_price: float) -> Optional[dict]:
    """Check if auto trade conditions are met"""
    state = auto_trade_state.get(symbol)
    if not state or not state.get("enabled"):
        return None

    overall = signals.get("overall", {})
    action = overall.get("action", "HOLD")
    strength = overall.get("strength", 0)

    trade = None

    if action == "BUY" and strength >= state["buy_threshold"] and state["current_position"] == 0:
        # Execute simulated buy
        state["current_position"] = state["max_position"]
        state["entry_price"] = current_price
        trade = {
            "action": "BUY",
            "price": current_price,
            "quantity": state["max_position"],
            "strength": strength,
            "timestamp": datetime.now().isoformat(),
        }
        state["trades"].append(trade)

    elif state["current_position"] > 0 and state["entry_price"]:
        entry = state["entry_price"]
        pnl_pct = ((current_price - entry) / entry) * 100

        # Check stop loss / take profit / sell signal
        should_sell = (
            pnl_pct <= -state["stop_loss_pct"] or
            pnl_pct >= state["take_profit_pct"] or
            (action == "SELL" and strength >= state["sell_threshold"])
        )

        if should_sell:
            pnl = (current_price - entry) * state["current_position"]
            reason = "STOP_LOSS" if pnl_pct <= -state["stop_loss_pct"] else \
                     "TAKE_PROFIT" if pnl_pct >= state["take_profit_pct"] else "SIGNAL"

            trade = {
                "action": "SELL",
                "price": current_price,
                "quantity": state["current_position"],
                "entry_price": entry,
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            }
            state["trades"].append(trade)
            state["current_position"] = 0
            state["entry_price"] = None

    return trade


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
