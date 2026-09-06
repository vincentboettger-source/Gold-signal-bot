"""
Gold Trading Signal Bot
========================
Holt Goldpreis-Daten (XAU/USD via Yahoo Finance Ticker "GC=F"),
berechnet technische Indikatoren (SMA, RSI, MACD) und sendet ein
Kauf-/Verkaufs-/Halten-Signal per Telegram.

WICHTIG: Dies ist ein Analyse-Werkzeug, KEINE Anlageberatung.
Technische Signale können falsch liegen. Nutze es als einen von
mehreren Bausteinen für deine eigene Entscheidung, nicht als
alleinige Handlungsgrundlage.
"""

import os
import sys
import requests
import pandas as pd
import yfinance as yf
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# ---------------------------------------------------------------------------
# Konfiguration (kommt aus Umgebungsvariablen -> siehe README.md)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TICKER = "GC=F"          # Gold Futures (Yahoo Finance). Alternative: "XAUUSD=X"
INTERVAL = "1h"          # Kerzen-Intervall: "1h", "1d", "15m" ...
LOOKBACK = "30d"         # Wie viel Historie geladen wird

SMA_SHORT = 20
SMA_LONG = 50
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30


# ---------------------------------------------------------------------------
# Daten holen
# ---------------------------------------------------------------------------
def fetch_data() -> pd.DataFrame:
    df = yf.download(TICKER, period=LOOKBACK, interval=INTERVAL, progress=False)
    if df.empty:
        raise RuntimeError(f"Keine Daten für {TICKER} erhalten. Ticker oder Intervall prüfen.")
    df = df.dropna()
    return df


# ---------------------------------------------------------------------------
# Indikatoren berechnen
# ---------------------------------------------------------------------------
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"]

    df["sma_short"] = SMAIndicator(close, window=SMA_SHORT).sma_indicator()
    df["sma_long"] = SMAIndicator(close, window=SMA_LONG).sma_indicator()
    df["rsi"] = RSIIndicator(close, window=RSI_PERIOD).rsi()

    macd = MACD(close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    return df.dropna()


# ---------------------------------------------------------------------------
# Regelbasiertes Signal ableiten
# ---------------------------------------------------------------------------
def generate_signal(df: pd.DataFrame) -> dict:
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    reasons = []
    score = 0  # positiv = bullisch, negativ = bearisch

    # 1) SMA Crossover (Trendfolge)
    sma_bullish_cross = prev["sma_short"] <= prev["sma_long"] and latest["sma_short"] > latest["sma_long"]
    sma_bearish_cross = prev["sma_short"] >= prev["sma_long"] and latest["sma_short"] < latest["sma_long"]
    if sma_bullish_cross:
        score += 2
        reasons.append(f"SMA{SMA_SHORT} hat SMA{SMA_LONG} nach oben gekreuzt (Golden Cross)")
    elif sma_bearish_cross:
        score -= 2
        reasons.append(f"SMA{SMA_SHORT} hat SMA{SMA_LONG} nach unten gekreuzt (Death Cross)")
    elif latest["sma_short"] > latest["sma_long"]:
        score += 1
        reasons.append(f"Aufwärtstrend: SMA{SMA_SHORT} > SMA{SMA_LONG}")
    else:
        score -= 1
        reasons.append(f"Abwärtstrend: SMA{SMA_SHORT} < SMA{SMA_LONG}")

    # 2) RSI (Überkauft/Überverkauft)
    if latest["rsi"] < RSI_OVERSOLD:
        score += 1
        reasons.append(f"RSI überverkauft ({latest['rsi']:.1f})")
    elif latest["rsi"] > RSI_OVERBOUGHT:
        score -= 1
        reasons.append(f"RSI überkauft ({latest['rsi']:.1f})")

    # 3) MACD Crossover (Momentum)
    macd_bullish_cross = prev["macd"] <= prev["macd_signal"] and latest["macd"] > latest["macd_signal"]
    macd_bearish_cross = prev["macd"] >= prev["macd_signal"] and latest["macd"] < latest["macd_signal"]
    if macd_bullish_cross:
        score += 1
        reasons.append("MACD hat Signallinie nach oben gekreuzt")
    elif macd_bearish_cross:
        score -= 1
        reasons.append("MACD hat Signallinie nach unten gekreuzt")

    # Score -> Signal
    if score >= 2:
        signal = "BUY 🟢"
    elif score <= -2:
        signal = "SELL 🔴"
    else:
        signal = "HOLD 🟡"

    return {
        "signal": signal,
        "score": score,
        "price": latest["Close"],
        "rsi": latest["rsi"],
        "sma_short": latest["sma_short"],
        "sma_long": latest["sma_long"],
        "reasons": reasons,
        "timestamp": df.index[-1],
    }


# ---------------------------------------------------------------------------
# Telegram senden
# ---------------------------------------------------------------------------
def send_telegram_message(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN oder TELEGRAM_CHAT_ID fehlt. "
            "Siehe README.md für die Einrichtung."
        )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }, timeout=15)
    resp.raise_for_status()


def format_message(result: dict) -> str:
    reasons_text = "\n".join(f"• {r}" for r in result["reasons"])
    return (
        f"<b>Gold Signal: {result['signal']}</b>\n\n"
        f"Preis: {result['price']:.2f} USD\n"
        f"RSI({RSI_PERIOD}): {result['rsi']:.1f}\n"
        f"SMA{SMA_SHORT}: {result['sma_short']:.2f} | SMA{SMA_LONG}: {result['sma_long']:.2f}\n"
        f"Score: {result['score']}\n\n"
        f"<b>Begründung:</b>\n{reasons_text}\n\n"
        f"<i>Zeitpunkt: {result['timestamp']}</i>\n"
        f"<i>⚠️ Keine Anlageberatung. Automatisiertes technisches Signal.</i>"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    try:
        df = fetch_data()
        df = add_indicators(df)
        result = generate_signal(df)
        message = format_message(result)
        print(message)  # auch in Logs sichtbar (z.B. GitHub Actions)
        send_telegram_message(message)
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        # Optional: Fehler auch per Telegram melden
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            try:
                send_telegram_message(f"⚠️ Gold-Bot Fehler: {e}")
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
