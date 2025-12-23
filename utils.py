import yfinance as yf
import pandas as pd
import re
import os

def fetch_current_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        if hist.empty:
            return None
            
        current_price = float(hist['Close'].iloc[-1])
        
        # Calculate daily change
        daily_change = 0.0
        if len(hist) >= 2:
            prev_close = float(hist['Close'].iloc[-2])
            daily_change = float(((current_price - prev_close) / prev_close) * 100)
            
        return {
            'price': current_price,
            'daily_change': daily_change
        }
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None

def process_excel(file_path):
    """Smart ticker extraction with multi-stage fallback."""
    ignore_list = ['SYMBOL', 'TICKER', 'PRICE', 'CHANGE', 'VOL', 'VOLUME', 'TOTAL', 'DATE', 'STRATEGY']
    extracted_tickers = set()

    # Stage 1: Pandas with robust delimiter detection & jagged line skipping
    try:
        # For CSVs, let pandas detect the separator (comma, tab, semicolon)
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
        else:
            df = pd.read_excel(file_path)

        # Smart Ticker Search: Scan all columns for ticker-like strings
        # Look for columns where at least 30% of rows look like tickers
        ticker_regex = r'^[A-Z0-9.]{1,8}$'
        
        for col in df.columns:
            # Skip if header is in ignore list
            col_str = str(col).upper().strip()
            if col_str in ignore_list:
                continue
                
            col_data = df[col].dropna().astype(str).str.strip().unique()
            matches = [t for t in col_data if re.match(ticker_regex, t) and t.upper() not in ignore_list]
            
            # If we found a significant number of matches, this is likely a ticker column
            if len(matches) > 0:
                for t in matches:
                    extracted_tickers.add(t.upper())

    except Exception as e:
        print(f"Pandas parsing failed: {e}. Falling back to raw text extraction.")

    # Stage 2: Raw Text Extraction Fallback (Foolproof)
    try:
        if not extracted_tickers:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
                # Find uppercase blocks 1-8 chars long bounded by whitespace, quotes, or commas
                raw_matches = re.findall(r'(?:^|[,\s"\'])([A-Z0-9.]{1,8})(?=[,\s"\']|$)', content)
                for t in raw_matches:
                    if t.upper() not in ignore_list and not t.isdigit():
                        extracted_tickers.add(t.upper())
    except Exception as e:
        print(f"Raw text extraction failed: {e}")

    return list(extracted_tickers)
