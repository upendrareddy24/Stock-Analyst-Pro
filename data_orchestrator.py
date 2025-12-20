import pandas as pd
import datetime
import requests
import os
import json
from typing import Optional, List, Dict, Any

# Try to import keys from local config if available, otherwise use environment variables
try:
    from config import FMP_API_KEY, TWELVE_DATA_API_KEY, ALPHA_VANTAGE_API_KEY
except ImportError:
    FMP_API_KEY = os.getenv("FMP_API_KEY")
    TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

class DataOrchestrator:
    """
    Handles multi-tier stock data fetching with automatic fallbacks and caching.
    Tiers: FMP -> Twelve Data -> Alpha Vantage -> Yahoo Finance
    """
    
    def __init__(self, cache_dir: str = "cache"):
        self.fmp_key = FMP_API_KEY
        self.td_key = TWELVE_DATA_API_KEY
        self.av_key = ALPHA_VANTAGE_API_KEY
        self.cache_dir = cache_dir
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_path(self, ticker: str, type: str) -> str:
        return os.path.join(self.cache_dir, f"{ticker}_{type}.json")

    def _is_cache_valid(self, cache_path: str, expiry_minutes: int) -> bool:
        if not os.path.exists(cache_path):
            return False
        mtime = os.path.getmtime(cache_path)
        return (datetime.datetime.now().timestamp() - mtime) < (expiry_minutes * 60)

    def get_stock_data(self, ticker: str, period: str = "1y", interval: str = "1d", force_refresh: bool = False) -> pd.DataFrame:
        """
        Public method to get stock data with all fallbacks and 1-hour caching.
        """
        cache_path = self._get_cache_path(ticker, "price")
        
        if not force_refresh and self._is_cache_valid(cache_path, 60):
            try:
                df = pd.read_json(cache_path)
                if not df.empty:
                    print(f"Loading {ticker} price from cache...")
                    return df
            except:
                pass

        # Tier 1: Financial Modeling Prep
        df = self._fetch_fmp(ticker, period, interval)
        if df is None or df.empty:
            # Tier 2: Twelve Data
            df = self._fetch_twelve_data(ticker, period, interval)
        if df is None or df.empty:
            # Tier 3: Alpha Vantage
            df = self._fetch_alpha_vantage(ticker, period, interval)
        if df is None or df.empty:
            # Tier 4: Yahoo Finance (Final Fallback)
            df = self._fetch_yahoo_finance(ticker, period, interval)

        if df is not None and not df.empty:
            df.to_json(cache_path)
            
        return df if df is not None else pd.DataFrame()

    def _fetch_fmp(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        if not self.fmp_key:
            return None
        
        print(f"Fetching {ticker} from FMP...")
        try:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={self.fmp_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if "historical" not in data:
                return None
                
            df = pd.DataFrame(data["historical"])
            df = df.iloc[::-1].reset_index(drop=True)
            df = df.rename(columns={
                "date": "Date", "open": "Open", "high": "High", 
                "low": "Low", "close": "Close", "volume": "Volume"
            })
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
            if period == "1y":
                start_date = datetime.datetime.now() - datetime.timedelta(days=365)
                df = df[df.index >= start_date]
                
            return df
        except Exception as e:
            print(f"FMP failed: {e}")
            return None

    def _fetch_twelve_data(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        if not self.td_key:
            return None
            
        print(f"Falling back to Twelve Data for {ticker}...")
        try:
            td_interval = "1day" if interval == "1d" else interval
            url = f"https://api.twelvedata.com/time_series?symbol={ticker}&interval={td_interval}&outputsize=5000&apikey={self.td_key}&order=ASC"
            
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            if "values" in data:
                df = pd.DataFrame(data["values"])
                df = df.rename(columns={
                    "datetime": "Date", "open": "Open", "high": "High", 
                    "low": "Low", "close": "Close", "volume": "Volume"
                })
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col])
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                return df
            return None
        except Exception as e:
            print(f"Twelve Data failed: {e}")
            return None

    def _fetch_alpha_vantage(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        if not self.av_key:
            return None
            
        print(f"Falling back to Alpha Vantage for {ticker}...")
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={self.av_key}"
            resp = requests.get(url, timeout=15)
            data = resp.json()
            
            if "Time Series (Daily)" in data:
                df = pd.DataFrame(data["Time Series (Daily)"]).T
                df = df.rename(columns={
                    "1. open": "Open", "2. high": "High", "3. low": "Low", 
                    "4. close": "Close", "5. volume": "Volume"
                })
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col])
                df.index = pd.to_datetime(df.index)
                df.index.name = 'Date'
                df.sort_index(inplace=True)
                return df
            return None
        except Exception as e:
            print(f"Alpha Vantage failed: {e}")
            return None

    def _fetch_yahoo_finance(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        print(f"Final fallback to Yahoo Finance for {ticker}...")
        try:
            import yfinance as yf
            yf_interval = "1d" if interval == "1d" else interval
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period=period, interval=yf_interval)
            
            if df.empty:
                return None
            
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df.index.name = 'Date'
            return df
        except Exception as e:
            print(f"Yahoo Finance failed: {e}")
            return None

    def get_ticker_news(self, ticker: str, limit: int = 5, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetches latest news for a specific ticker with 15-minute caching.
        """
        cache_path = self._get_cache_path(ticker, "news")
        
        if not force_refresh and self._is_cache_valid(cache_path, 15):
            try:
                with open(cache_path, 'r') as f:
                    print(f"Loading {ticker} news from cache...")
                    return json.load(f)
            except:
                pass

        news = []
        # Try FMP first
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={ticker}&limit={limit}&apikey={self.fmp_key}"
                resp = requests.get(url, timeout=10)
                data = resp.json()
                if isinstance(data, list):
                    for item in data:
                        news.append({
                            "title": item.get("title"),
                            "summary": item.get("text"),
                            "url": item.get("url"),
                            "date": item.get("publishedDate"),
                            "source": item.get("site")
                        })
                    return news
            except Exception as e:
                print(f"FMP News failed: {e}")

        # Fallback to Yahoo Finance (via yfinance)
        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(ticker)
            yf_news = ticker_obj.news
            if yf_news:
                for item in yf_news[:limit]:
                    # Support new yfinance schema
                    content = item.get("content", {})
                    if content:
                        news.append({
                            "title": content.get("title", "No Title"),
                            "summary": content.get("summary", "Yahoo Finance"),
                            "url": content.get("clickThroughUrl", {}).get("url", "#"),
                            "date": content.get("pubDate", "Recent"),
                            "source": "Yahoo Finance"
                        })
                        continue

                    # Fallback to old schema
                    pub_time = item.get("providerPublishTime")
                    formatted_date = "Recent"
                    if pub_time:
                        try:
                            formatted_date = datetime.datetime.fromtimestamp(int(pub_time)).strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            pass
                            
                    news.append({
                        "title": item.get("title", "No Title"),
                        "summary": item.get("publisher", "Yahoo Finance"),
                        "url": item.get("link", "#"),
                        "date": formatted_date,
                        "source": "Yahoo Finance"
                    })
                if news:
                    with open(cache_path, 'w') as f:
                        json.dump(news, f)
                return news
        except Exception as e:
            print(f"Yahoo News failed: {e}")
            
        if news:
            with open(cache_path, 'w') as f:
                json.dump(news, f)
        return news

if __name__ == "__main__":
    orchestrator = DataOrchestrator()
    sample_data = orchestrator.get_stock_data("AAPL")
    print(sample_data.tail())
