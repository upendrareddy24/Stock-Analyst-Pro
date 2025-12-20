import yfinance as yf
ticker = yf.Ticker("NVDA")
if ticker.news:
    item = ticker.news[0]
    content = item.get('content', {})
    print(f"Title: {content.get('title')}")
    print(f"Link: {content.get('clickThroughUrl', {}).get('url')}")
    print(f"PubDate: {content.get('pubDate')}")
