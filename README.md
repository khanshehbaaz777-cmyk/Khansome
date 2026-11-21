# Weekly Futures Stock Screener (ADX)

A TradingView Pine Script indicator to screen symbols using weekly directional movement and ADX. It evaluates weekly data even when applied to a chart on another timeframe.

## Screening rules

A symbol matches when all three conditions are true:

- Weekly **+DI > -DI** (interpreting “positive ADX > ADX” as positive directional indicator above negative directional indicator).
- Weekly **ADX > 25**.
- Weekly **-DI < 20**.

DI length and ADX smoothing default to 14 and can be changed in the indicator settings. The threshold values are configurable too.

## Use in TradingView

1. Open `weekly_futures_screener.pine` and copy it into the Pine Editor in TradingView.
2. Add the indicator to a chart and save it.
3. Open **Pine Screener**, select a watchlist containing the stocks or futures-related symbols you want to scan, and select this indicator.
4. Filter the **Weekly ADX Match** plot to `1` to see matches. The diagnostic +DI, ADX, and -DI values are available in the Data Window.
5. Optionally create an alert using **Weekly ADX Screener Match**.

The script evaluates whichever symbols you include in your TradingView watchlist; it does not fetch or maintain a market-wide ticker universe. Weekly signals can change while the current weekly candle is still forming. This is a technical screening aid, not investment advice.
