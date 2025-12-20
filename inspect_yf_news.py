import yfinance as yf
import json

ticker = yf.Ticker("NVDA")
print(f"News type: {type(ticker.news)}")
if ticker.news:
    print(f"First item keys: {ticker.news[0].keys()}")
    print(json.dumps(ticker.news[0], indent=2))
