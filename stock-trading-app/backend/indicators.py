"""
Technical Indicators Calculator
Supports: SMA, EMA, RSI, MACD, Bollinger Bands, Stochastic, ATR, VWAP
"""

import numpy as np
import pandas as pd


class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.close = df["close"].astype(float)
        self.high = df["high"].astype(float)
        self.low = df["low"].astype(float)
        self.volume = df["volume"].astype(float) if "volume" in df.columns else None

    def calculate(self, indicators: list) -> pd.DataFrame:
        result = self.df.copy()

        for ind in indicators:
            ind = ind.lower().strip()

            if ind.startswith("sma"):
                period = int(ind.replace("sma", "")) if len(ind) > 3 else 20
                result[ind] = self._sma(period)

            elif ind.startswith("ema"):
                period = int(ind.replace("ema", "")) if len(ind) > 3 else 9
                result[ind] = self._ema(period)

            elif ind == "rsi":
                result["rsi"] = self._rsi(14)

            elif ind == "macd":
                macd, signal, hist = self._macd()
                result["macd"] = macd
                result["macd_signal"] = signal
                result["macd_hist"] = hist

            elif ind == "bb":
                upper, mid, lower = self._bollinger_bands(20, 2)
                result["bb_upper"] = upper
                result["bb_mid"] = mid
                result["bb_lower"] = lower
                result["bb_width"] = ((upper - lower) / mid * 100).round(4)
                result["bb_pct"] = ((self.close - lower) / (upper - lower) * 100).round(4)

            elif ind == "stoch":
                k, d = self._stochastic(14, 3)
                result["stoch_k"] = k
                result["stoch_d"] = d

            elif ind == "atr":
                result["atr"] = self._atr(14)

            elif ind == "vwap" and self.volume is not None:
                result["vwap"] = self._vwap()

            elif ind == "obv" and self.volume is not None:
                result["obv"] = self._obv()

        return result

    def _sma(self, period: int) -> pd.Series:
        return self.close.rolling(window=period).mean().round(4)

    def _ema(self, period: int) -> pd.Series:
        return self.close.ewm(span=period, adjust=False).mean().round(4)

    def _rsi(self, period: int = 14) -> pd.Series:
        delta = self.close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.round(2)

    def _macd(self, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = self.close.ewm(span=fast, adjust=False).mean()
        ema_slow = self.close.ewm(span=slow, adjust=False).mean()
        macd_line = (ema_fast - ema_slow).round(4)
        signal_line = macd_line.ewm(span=signal, adjust=False).mean().round(4)
        histogram = (macd_line - signal_line).round(4)
        return macd_line, signal_line, histogram

    def _bollinger_bands(self, period: int = 20, std_dev: float = 2.0):
        sma = self.close.rolling(window=period).mean()
        std = self.close.rolling(window=period).std()
        upper = (sma + std_dev * std).round(4)
        lower = (sma - std_dev * std).round(4)
        return upper, sma.round(4), lower

    def _stochastic(self, k_period: int = 14, d_period: int = 3):
        lowest_low = self.low.rolling(window=k_period).min()
        highest_high = self.high.rolling(window=k_period).max()
        k = ((self.close - lowest_low) / (highest_high - lowest_low) * 100).round(2)
        d = k.rolling(window=d_period).mean().round(2)
        return k, d

    def _atr(self, period: int = 14) -> pd.Series:
        prev_close = self.close.shift(1)
        tr = pd.concat([
            self.high - self.low,
            (self.high - prev_close).abs(),
            (self.low - prev_close).abs()
        ], axis=1).max(axis=1)
        return tr.ewm(com=period - 1, min_periods=period).mean().round(4)

    def _vwap(self) -> pd.Series:
        typical_price = (self.high + self.low + self.close) / 3
        vwap = (typical_price * self.volume).cumsum() / self.volume.cumsum()
        return vwap.round(4)

    def _obv(self) -> pd.Series:
        obv = np.where(
            self.close > self.close.shift(1),
            self.volume,
            np.where(self.close < self.close.shift(1), -self.volume, 0)
        )
        return pd.Series(obv, index=self.close.index).cumsum()
