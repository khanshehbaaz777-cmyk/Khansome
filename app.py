from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Starter NSE watchlist. Edit this list or enter your own Yahoo Finance symbols
# in the web UI (for example, AAPL or RELIANCE.NS).
DEFAULT_SYMBOLS = [
    "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "INFY.NS",
    "TCS.NS", "ITC.NS", "LT.NS", "AXISBANK.NS", "BHARTIARTL.NS",
    "KOTAKBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TATAMOTORS.NS", "TATASTEEL.NS", "NTPC.NS", "POWERGRID.NS",
    "ADANIENT.NS", "ONGC.NS",
]
SYMBOL_RE = re.compile(r"^[A-Za-z0-9.^=_-]{1,24}$")
CACHE_SECONDS = 45
_cache: dict[tuple[Any, ...], tuple[float, dict[str, Any]]] = {}
_cache_lock = threading.Lock()


def _wilder(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def weekly_adx(symbol: str, di_length: int = 14, adx_smoothing: int = 14) -> dict[str, Any]:
    frame = yf.download(
        symbol,
        period="2y",
        interval="1wk",
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    if frame.empty:
        raise ValueError("No weekly price data returned for this symbol")

    # yfinance may return MultiIndex columns even for a single symbol.
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame = frame.rename(columns=str.title)
    required = {"High", "Low", "Close"}
    if not required.issubset(frame.columns):
        raise ValueError("Price provider returned incomplete OHLC data")

    high, low, close = frame["High"], frame["Low"], frame["Close"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    previous_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)

    smoothed_tr = _wilder(true_range, di_length)
    plus_di = 100 * _wilder(plus_dm, di_length) / smoothed_tr
    minus_di = 100 * _wilder(minus_dm, di_length) / smoothed_tr
    denominator = (plus_di + minus_di).replace(0, float("nan"))
    dx = 100 * (plus_di - minus_di).abs() / denominator
    adx = _wilder(dx, adx_smoothing)

    valid = pd.concat([plus_di, minus_di, adx, close], axis=1).dropna()
    if valid.empty:
        raise ValueError("Not enough weekly history to calculate ADX")
    row = valid.iloc[-1]
    plus_value, minus_value, adx_value, close_value = map(float, row)
    return {
        "symbol": symbol,
        "plus_di": round(plus_value, 2),
        "minus_di": round(minus_value, 2),
        "adx": round(adx_value, 2),
        "close": round(close_value, 2),
        "match": plus_value > minus_value and adx_value > 25 and minus_value < 20,
        "week_ending": valid.index[-1].strftime("%Y-%m-%d"),
        "error": None,
    }


@app.get("/
def index():
    return render_template("index.html", default_symbols=",".join(DEFAULT_SYMBOLS))


@app.get("/api/scan")
def scan():
    raw_symbols = request.args.get("symbols", ",".join(DEFAULT_SYMBOLS))
    requested = [part.strip().upper() for part in re.split(r"[,\s]+", raw_symbols) if part.strip()]
    symbols = list(dict.fromkeys(requested))
    if not symbols:
        return jsonify({"error": "Enter at least one ticker symbol."}), 400
    if len(symbols) > 100:
        return jsonify({"error": "Scan up to 100 symbols at a time."}), 400
    invalid = [symbol for symbol in symbols if not SYMBOL_RE.fullmatch(symbol)]
    if invalid:
        return jsonify({"error": f"Invalid ticker symbol(s): {', '.join(invalid)}"}), 400

    key = tuple(symbols)
    now = time.time()
    with _cache_lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < CACHE_SECONDS:
            return jsonify(cached[1])

    results = []
    for symbol in symbols:
        try:
            results.append(weekly_adx(symbol))
        except Exception as exc:  # Return a per-symbol error without aborting the scan.
            results.append({"symbol": symbol, "match": False, "error": str(exc)[:180]})

    payload = {
        "results": results,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "rules": {"plus_di_above_minus_di": True, "adx_above": 25, "minus_di_below": 20},
        "provider": "Yahoo Finance via yfinance",
        "cache_seconds": CACHE_SECONDS,
    }
    with _cache_lock:
        _cache[key] = (time.time(), payload)
    return jsonify(payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
