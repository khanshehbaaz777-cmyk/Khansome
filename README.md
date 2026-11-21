# Weekly ADX Market Screener

A small web application that scans a watchlist of stock symbols using weekly Directional Movement Index (DMI) and ADX. It preserves the original TradingView Pine indicator and adds a browser-based screener.

## Screening rules

A symbol matches when all conditions are true on weekly candles:

- **+DI > -DI** (bullish directional movement; interpreting “positive ADX > ADX” as +DI > -DI).
- **ADX > 25**.
- **-DI < 20**.

The server calculates DMI/ADX with Wilder smoothing over 14 periods, matching the common default settings. The current, still-forming weekly candle is included, so a signal can change until the week closes.

## Run locally

Requires Python 3.10 or later.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. Edit the symbol list in the page using Yahoo Finance ticker format. The starter list is a set of NSE symbols (`.NS`); examples for other markets include `AAPL`, `MSFT`, and `TSLA`. Up to 100 symbols can be scanned per request.

## Deploy

This is a Flask web service. A host that supports Python web apps can deploy the repository using the included `Procfile` (`gunicorn app:app`) and install dependencies from `requirements.txt`. Keep the app's public URL private if you do not want others to access it; the app currently has no user authentication.

## Data and limitations

The app retrieves weekly OHLC data from Yahoo Finance using the community `yfinance` package. This is a convenient prototype data source, not a guaranteed or exchange-grade real-time feed. Market data may be delayed, rate-limited, or unavailable, and Yahoo Finance terms/provider behavior may change. The backend caches scans for 45 seconds; the browser auto-refreshes every 60 seconds. Use a licensed market-data provider for reliable real-time trading workflows. This app only screens the symbols entered; it does not place trades and is not investment advice.

## Files

- `app.py` — Flask API, weekly ADX calculation, and scan endpoint.
- `templates/index.html` — responsive screener page.
- `weekly_futures_screener.pine` — original TradingView indicator.
