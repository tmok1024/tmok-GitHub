"""
Signal Engine - Buy/Sell signal generation
Combines multiple technical indicators for comprehensive signals
"""

import pandas as pd
import numpy as np
from indicators import TechnicalIndicators


class SignalEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.close = df["close"].astype(float)

    def generate_signals(self, indicators: list) -> dict:
        """Generate buy/sell signals from all enabled indicators"""
        ind_engine = TechnicalIndicators(self.df)
        result_df = ind_engine.calculate(indicators)
        current = result_df.iloc[-1]
        prev = result_df.iloc[-2] if len(result_df) > 1 else current

        signals = {}
        bullish_count = 0
        bearish_count = 0
        total_weight = 0

        # RSI Signal (weight: 25)
        if "rsi" in result_df.columns:
            rsi = current.get("rsi")
            if pd.notna(rsi):
                rsi = float(rsi)
                if rsi <= 30:
                    action, strength = "BUY", min(100, int((30 - rsi) / 30 * 100 + 60))
                    color = "#00E676"
                    desc = f"RSI {rsi:.1f} - 売られ過ぎ (買い)"
                    bullish_count += 25
                elif rsi >= 70:
                    action, strength = "SELL", min(100, int((rsi - 70) / 30 * 100 + 60))
                    color = "#FF1744"
                    desc = f"RSI {rsi:.1f} - 買われ過ぎ (売り)"
                    bearish_count += 25
                elif rsi < 45:
                    action, strength = "BUY", 30
                    color = "#69F0AE"
                    desc = f"RSI {rsi:.1f} - やや売られ過ぎ"
                    bullish_count += 10
                elif rsi > 55:
                    action, strength = "SELL", 30
                    color = "#FF5252"
                    desc = f"RSI {rsi:.1f} - やや買われ過ぎ"
                    bearish_count += 10
                else:
                    action, strength = "HOLD", 50
                    color = "#FFD740"
                    desc = f"RSI {rsi:.1f} - 中立"

                signals["rsi"] = {
                    "action": action, "strength": strength,
                    "value": round(rsi, 2), "color": color, "desc": desc
                }
                total_weight += 25

        # MACD Signal (weight: 30)
        if "macd" in result_df.columns and "macd_signal" in result_df.columns:
            macd = current.get("macd")
            macd_sig = current.get("macd_signal")
            macd_hist = current.get("macd_hist")
            prev_hist = prev.get("macd_hist")

            if pd.notna(macd) and pd.notna(macd_sig):
                macd, macd_sig = float(macd), float(macd_sig)
                macd_hist = float(macd_hist) if pd.notna(macd_hist) else 0
                prev_hist = float(prev_hist) if pd.notna(prev_hist) else 0

                # Golden/Death cross detection
                if macd > macd_sig and prev_hist <= 0:
                    action, strength, color = "BUY", 85, "#00E676"
                    desc = "MACD ゴールデンクロス (強買い)"
                    bullish_count += 30
                elif macd < macd_sig and prev_hist >= 0:
                    action, strength, color = "SELL", 85, "#FF1744"
                    desc = "MACD デッドクロス (強売り)"
                    bearish_count += 30
                elif macd > macd_sig and macd_hist > prev_hist:
                    action, strength, color = "BUY", 60, "#69F0AE"
                    desc = "MACD 上昇中 (買い)"
                    bullish_count += 20
                elif macd < macd_sig and macd_hist < prev_hist:
                    action, strength, color = "SELL", 60, "#FF5252"
                    desc = "MACD 下落中 (売り)"
                    bearish_count += 20
                else:
                    action, strength, color = "HOLD", 50, "#FFD740"
                    desc = "MACD 中立"

                signals["macd"] = {
                    "action": action, "strength": strength,
                    "value": round(macd, 4), "signal_value": round(macd_sig, 4),
                    "histogram": round(macd_hist, 4),
                    "color": color, "desc": desc
                }
                total_weight += 30

        # Bollinger Bands Signal (weight: 20)
        if "bb_upper" in result_df.columns:
            price = float(current["close"])
            bb_upper = current.get("bb_upper")
            bb_lower = current.get("bb_lower")
            bb_pct = current.get("bb_pct")

            if pd.notna(bb_upper) and pd.notna(bb_lower):
                bb_upper, bb_lower = float(bb_upper), float(bb_lower)
                bb_pct = float(bb_pct) if pd.notna(bb_pct) else 50

                if price <= bb_lower:
                    action, strength, color = "BUY", 80, "#00E676"
                    desc = f"BB下限タッチ (強買い) %B:{bb_pct:.1f}%"
                    bullish_count += 20
                elif price >= bb_upper:
                    action, strength, color = "SELL", 80, "#FF1744"
                    desc = f"BB上限タッチ (強売り) %B:{bb_pct:.1f}%"
                    bearish_count += 20
                elif bb_pct < 20:
                    action, strength, color = "BUY", 50, "#69F0AE"
                    desc = f"BB下部 (買い) %B:{bb_pct:.1f}%"
                    bullish_count += 10
                elif bb_pct > 80:
                    action, strength, color = "SELL", 50, "#FF5252"
                    desc = f"BB上部 (売り) %B:{bb_pct:.1f}%"
                    bearish_count += 10
                else:
                    action, strength, color = "HOLD", 50, "#FFD740"
                    desc = f"BB中央 %B:{bb_pct:.1f}%"

                signals["bb"] = {
                    "action": action, "strength": strength,
                    "bb_upper": round(bb_upper, 2),
                    "bb_lower": round(bb_lower, 2),
                    "bb_pct": round(bb_pct, 2),
                    "color": color, "desc": desc
                }
                total_weight += 20

        # Moving Average Cross Signal (weight: 25)
        sma20 = current.get("sma20")
        sma50 = current.get("sma50")
        prev_sma20 = prev.get("sma20")
        prev_sma50 = prev.get("sma50")

        if pd.notna(sma20) and pd.notna(sma50):
            price = float(current["close"])
            sma20, sma50 = float(sma20), float(sma50)

            price_vs_sma20_pct = ((price - sma20) / sma20) * 100
            price_vs_sma50_pct = ((price - sma50) / sma50) * 100

            # Golden/Death cross
            if pd.notna(prev_sma20) and pd.notna(prev_sma50):
                prev_sma20, prev_sma50 = float(prev_sma20), float(prev_sma50)
                if sma20 > sma50 and prev_sma20 <= prev_sma50:
                    action, strength, color = "BUY", 90, "#00E676"
                    desc = f"MA ゴールデンクロス (強買い)"
                    bullish_count += 25
                elif sma20 < sma50 and prev_sma20 >= prev_sma50:
                    action, strength, color = "SELL", 90, "#FF1744"
                    desc = f"MA デッドクロス (強売り)"
                    bearish_count += 25
                elif price > sma20 > sma50:
                    action, strength, color = "BUY", 65, "#69F0AE"
                    desc = f"価格>SMA20>SMA50 上昇トレンド (+{price_vs_sma20_pct:.2f}%)"
                    bullish_count += 15
                elif price < sma20 < sma50:
                    action, strength, color = "SELL", 65, "#FF5252"
                    desc = f"価格<SMA20<SMA50 下落トレンド ({price_vs_sma20_pct:.2f}%)"
                    bearish_count += 15
                else:
                    action, strength, color = "HOLD", 50, "#FFD740"
                    desc = f"SMA20 vs 価格: {price_vs_sma20_pct:+.2f}%"
            else:
                action, strength, color = "HOLD", 50, "#FFD740"
                desc = f"SMA20: {price_vs_sma20_pct:+.2f}%"

            signals["ma"] = {
                "action": action, "strength": strength,
                "sma20": round(sma20, 2), "sma50": round(sma50, 2),
                "price_vs_sma20_pct": round(price_vs_sma20_pct, 2),
                "price_vs_sma50_pct": round(price_vs_sma50_pct, 2),
                "color": color, "desc": desc
            }
            total_weight += 25

        # EMA Signal (weight: 20)
        ema9 = current.get("ema9")
        if pd.notna(ema9):
            price = float(current["close"])
            ema9 = float(ema9)
            price_vs_ema_pct = ((price - ema9) / ema9) * 100

            if price > ema9 * 1.005:
                action, strength, color = "BUY", 55, "#69F0AE"
                desc = f"EMA9上 (買い) +{price_vs_ema_pct:.2f}%"
                bullish_count += 10
            elif price < ema9 * 0.995:
                action, strength, color = "SELL", 55, "#FF5252"
                desc = f"EMA9下 (売り) {price_vs_ema_pct:.2f}%"
                bearish_count += 10
            else:
                action, strength, color = "HOLD", 50, "#FFD740"
                desc = f"EMA9付近 {price_vs_ema_pct:+.2f}%"

            signals["ema"] = {
                "action": action, "strength": strength,
                "ema9": round(ema9, 2),
                "price_vs_ema_pct": round(price_vs_ema_pct, 2),
                "color": color, "desc": desc
            }
            total_weight += 20

        # Overall Signal
        if total_weight > 0:
            score = ((bullish_count - bearish_count) / total_weight) * 100
            if score >= 30:
                overall_action = "BUY"
                overall_color = "#00E676"
                overall_strength = min(100, int(score + 50))
                overall_desc = f"総合買いシグナル ({score:+.0f})"
            elif score <= -30:
                overall_action = "SELL"
                overall_color = "#FF1744"
                overall_strength = min(100, int(-score + 50))
                overall_desc = f"総合売りシグナル ({score:+.0f})"
            else:
                overall_action = "HOLD"
                overall_color = "#FFD740"
                overall_strength = 50
                overall_desc = f"様子見 ({score:+.0f})"

            signals["overall"] = {
                "action": overall_action,
                "strength": overall_strength,
                "score": round(score, 1),
                "color": overall_color,
                "desc": overall_desc,
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
            }

        return signals
