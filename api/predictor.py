"""
Stock Prediction Engine — Technical Analysis + Signal Generation
"""
from statistics import mean, stdev

def sma(closes, period):
    if len(closes) < period: return None
    return round(mean(closes[-period:]), 2)

def ema(closes, period):
    if len(closes) < period: return None
    k = 2 / (period + 1)
    val = mean(closes[:period])
    for p in closes[period:]:
        val = p * k + val * (1 - k)
    return round(val, 2)

def rsi(closes, period=14):
    if len(closes) < period + 1: return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0)); losses.append(max(-d, 0))
    ag = mean(gains[-period:])
    al = mean(losses[-period:])
    if al == 0: return 100.0
    return round(100 - 100 / (1 + ag / al), 2)

def macd(closes):
    if len(closes) < 26: return None, None, None
    e12 = ema(closes, 12); e26 = ema(closes, 26)
    ml = round(e12 - e26, 4)
    sl = round(ml * 0.2 + ml * 0.8, 4)
    return ml, sl, round(ml - sl, 4)

def bollinger(closes, period=20):
    if len(closes) < period: return None, None, None
    sl = closes[-period:]
    mid = mean(sl)
    sd = stdev(sl) if len(sl) > 1 else 0
    return round(mid + 2*sd, 2), round(mid, 2), round(mid - 2*sd, 2)

def atr(candles, period=14):
    if len(candles) < 2: return None
    trs = []
    for i in range(1, len(candles)):
        hl  = candles[i]["high"] - candles[i]["low"]
        hpc = abs(candles[i]["high"] - candles[i-1]["close"])
        lpc = abs(candles[i]["low"]  - candles[i-1]["close"])
        trs.append(max(hl, hpc, lpc))
    n = min(period, len(trs))
    return round(mean(trs[-n:]), 2)

def score(indicators):
    s = 0.0
    r = indicators.get("rsi", 50)
    if   r < 30: s += 2.5
    elif r < 45: s += 1.0
    elif r > 70: s -= 2.5
    elif r > 55: s -= 1.0

    mh = indicators.get("macd_hist")
    if mh: s += max(-2, min(2, mh * 10))

    s20 = indicators.get("sma20"); s50 = indicators.get("sma50")
    cp  = indicators.get("price")
    if s20 and s50:
        s += 1.5 if s20 > s50 else -1.5
    if s20 and cp:
        s += 1.0 if cp > s20 else -1.0

    bu = indicators.get("bb_upper"); bl = indicators.get("bb_lower")
    if bu and bl and cp:
        if   cp < bl: s += 2.0
        elif cp > bu: s -= 2.0

    return round(max(-10, min(10, s)), 2)

def _reasons(signal, ind):
    r = []
    rv = ind.get("rsi", 50)
    if   rv < 30: r.append(f"RSI {rv} — oversold territory, potential reversal upcoming")
    elif rv > 70: r.append(f"RSI {rv} — overbought, consider booking profits")
    else:         r.append(f"RSI {rv} — momentum is neutral")

    s20 = ind.get("sma20"); s50 = ind.get("sma50")
    if s20 and s50:
        r.append("SMA20 > SMA50 — bullish golden cross pattern" if s20 > s50
                 else "SMA20 < SMA50 — bearish death cross pattern")

    mh = ind.get("macd_hist")
    if mh is not None:
        r.append("MACD histogram positive — buying momentum building" if mh > 0
                 else "MACD histogram negative — selling pressure present")

    bu = ind.get("bb_upper"); bl = ind.get("bb_lower"); cp = ind.get("price")
    if bu and bl and cp:
        if   cp < bl: r.append("Price below lower Bollinger Band — strong mean reversion buy signal")
        elif cp > bu: r.append("Price above upper Bollinger Band — overextended, take profits")
        else:         r.append("Price within Bollinger Bands — normal volatility range")
    return r

def analyse(candles, symbol, trade_type="intraday"):
    if not candles:
        return {"symbol": symbol, "type": trade_type, "signal": "HOLD",
                "score": 0, "confidence": 0.5, "current_price": 0,
                "reasoning": ["Insufficient data"]}

    closes = [c["close"] for c in candles]
    cp = closes[-1]
    rp = 9 if trade_type == "intraday" else 14
    bp = 10 if trade_type == "intraday" else 20

    ind = {
        "price":    cp,
        "rsi":      rsi(closes, rp),
        "sma20":    sma(closes, 20),
        "sma50":    sma(closes, 50) if len(closes) >= 50 else None,
        "sma200":   sma(closes, min(200, len(closes))),
        "atr":      atr(candles, 10 if trade_type == "intraday" else 14),
    }
    ml, sl_, mh = macd(closes)
    ind["macd"] = ml; ind["macd_signal"] = sl_; ind["macd_hist"] = mh
    bu, bm, bl = bollinger(closes, bp)
    ind["bb_upper"] = bu; ind["bb_mid"] = bm; ind["bb_lower"] = bl

    sc = score(ind)
    sig = "BUY" if sc >= 2.5 else "SELL" if sc <= -2.5 else "HOLD"
    conf = round(min(0.95, 0.5 + abs(sc) / 20), 2)
    atr_val = ind["atr"] or cp * 0.015

    if trade_type == "intraday":
        sl  = round(cp - atr_val * 1.5, 2)
        t1  = round(cp + atr_val * 2.0, 2)
        t2  = round(cp + atr_val * 3.5, 2)
        t3  = None
    else:
        sl  = round(cp * 0.93, 2)
        t1  = round(cp * 1.12, 2)
        t2  = round(cp * 1.25, 2)
        t3  = round(cp * 1.40, 2)

    rr = round((t1 - cp) / (cp - sl), 2) if cp != sl else 0

    return {
        "symbol": symbol, "type": trade_type,
        "signal": sig, "score": sc, "confidence": conf,
        "current_price": round(cp, 2), "entry": round(cp, 2),
        "stop_loss": sl, "target1": t1, "target2": t2, "target3": t3,
        "risk_reward": rr,
        "indicators": ind,
        "reasoning": _reasons(sig, ind),
    }

def bulk_scan(candles_map, trade_type="intraday"):
    results = [analyse(candles, sym, trade_type) for sym, candles in candles_map.items()]
    buys = [r for r in results if r["signal"] == "BUY"]
    return sorted(buys, key=lambda x: (x["confidence"], x["score"]), reverse=True)
