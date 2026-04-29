"""
Market Service (yfinance)
Fetches live data and history from Yahoo Finance.
"""
import yfinance as yf
from datetime import datetime, timedelta

NIFTY50_STOCKS = [
    {"symbol": "RELIANCE",   "name": "Reliance Industries",       "sector": "Energy"},
    {"symbol": "TCS",        "name": "Tata Consultancy Services",  "sector": "IT"},
    {"symbol": "HDFCBANK",   "name": "HDFC Bank",                  "sector": "Banking"},
    {"symbol": "INFY",       "name": "Infosys",                    "sector": "IT"},
    {"symbol": "ICICIBANK",  "name": "ICICI Bank",                 "sector": "Banking"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever",         "sector": "FMCG"},
    {"symbol": "ITC",        "name": "ITC Ltd",                    "sector": "FMCG"},
    {"symbol": "SBIN",       "name": "State Bank of India",        "sector": "Banking"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance",              "sector": "Finance"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel",              "sector": "Telecom"},
    {"symbol": "WIPRO",      "name": "Wipro",                      "sector": "IT"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints",               "sector": "Paints"},
    {"symbol": "MARUTI",     "name": "Maruti Suzuki",              "sector": "Auto"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors",                "sector": "Auto"},
    {"symbol": "AXISBANK",   "name": "Axis Bank",                  "sector": "Banking"},
    {"symbol": "SUNPHARMA",  "name": "Sun Pharma",                 "sector": "Pharma"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement",           "sector": "Cement"},
    {"symbol": "TITAN",      "name": "Titan Company",              "sector": "Consumer"},
    {"symbol": "NESTLEIND",  "name": "Nestle India",               "sector": "FMCG"},
    {"symbol": "POWERGRID",  "name": "Power Grid Corp",            "sector": "Power"},
]

def _yf_symbol(symbol):
    return f"{symbol.upper()}.NS"

def get_quote(symbol, exchange="NSE"):
    try:
        t = yf.Ticker(_yf_symbol(symbol))
        fast = t.fast_info
        last_price = float(fast.last_price)
        prev_close = float(fast.previous_close)
        change = round(last_price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0
        
        open_price = float(fast.open) if hasattr(fast, 'open') and fast.open else last_price
        high = float(fast.day_high) if hasattr(fast, 'day_high') and fast.day_high else last_price
        low = float(fast.day_low) if hasattr(fast, 'day_low') and fast.day_low else last_price
        volume = int(fast.last_volume) if hasattr(fast, 'last_volume') and fast.last_volume else 0
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            "last_price": round(last_price, 2),
            "change": change,
            "change_pct": change_pct,
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(prev_close, 2),
            "volume": volume,
        }
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")
        return {
            "symbol": symbol, "exchange": exchange,
            "last_price": 0, "change": 0, "change_pct": 0,
            "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0
        }

def get_historical(symbol, exchange="NSE", interval="1d", days=60):
    try:
        yf_interval = '1d' if interval == 'day' else interval
        t = yf.Ticker(_yf_symbol(symbol))
        df = t.history(period=f"{days}d", interval=yf_interval)
        
        candles = []
        for index, row in df.iterrows():
            candles.append({
                "date": str(index.date()),
                "open": round(float(row.get('Open', 0)), 2),
                "high": round(float(row.get('High', 0)), 2),
                "low": round(float(row.get('Low', 0)), 2),
                "close": round(float(row.get('Close', 0)), 2),
                "volume": int(row.get('Volume', 0))
            })
        return candles
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return []

def get_market_indices():
    indices_map = {
        "NIFTY 50":   "^NSEI",
        "SENSEX":     "^BSESN",
        "NIFTY BANK": "^NSEBANK",
        "NIFTY IT":   "^CNXIT",
    }
    result = {}
    for name, sym in indices_map.items():
        try:
            t = yf.Ticker(sym).fast_info
            last_price = float(t.last_price)
            prev_close = float(t.previous_close)
            change = round(last_price - prev_close, 2)
            change_pct = round((change / prev_close) * 100, 2) if prev_close else 0
            result[name] = {
                "value": round(last_price, 2),
                "change": change,
                "change_pct": change_pct,
            }
        except Exception as e:
            print(f"Index error {sym}: {e}")
            result[name] = {"value": 0, "change": 0, "change_pct": 0}
    return result

def get_top_movers():
    quotes = get_all_quotes()
    if not quotes:
        return {"gainers": [], "losers": []}
    
    gainers = sorted([q for q in quotes if q["change_pct"] > 0],
                     key=lambda x: x["change_pct"], reverse=True)[:5]
    losers  = sorted([q for q in quotes if q["change_pct"] < 0],
                     key=lambda x: x["change_pct"])[:5]
    return {"gainers": gainers, "losers": losers}

def search_stocks(query):
    q = query.upper()
    return [s for s in NIFTY50_STOCKS
            if q in s["symbol"] or q in s["name"].upper()][:8]

def get_all_quotes():
    tickers = " ".join([f"{s['symbol']}.NS" for s in NIFTY50_STOCKS])
    quotes = []
    try:
        data = yf.download(tickers, period="2d", progress=False)
        for s in NIFTY50_STOCKS:
            sym = s['symbol']
            sym_ns = f"{sym}.NS"
            try:
                if 'Close' in data.columns and sym_ns in data['Close']:
                    closes = data['Close'][sym_ns].dropna()
                    if len(closes) < 1:
                        continue
                    last_price = float(closes.iloc[-1])
                    prev_close = float(closes.iloc[-2]) if len(closes) > 1 else last_price
                else:
                    continue
                    
                change = last_price - prev_close
                change_pct = (change / prev_close) * 100 if prev_close else 0
                quotes.append({
                    "symbol": sym, "name": s["name"], "sector": s["sector"],
                    "last_price": round(last_price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2)
                })
            except Exception as e:
                print(f"Error fetching mass quote {sym}: {e}")
    except Exception as e:
        print(f"Download API error: {e}")
    return quotes

