from rest_framework.decorators import api_view
from rest_framework.response import Response
from .market_service import (
    get_quote, get_historical, get_market_indices,
    get_top_movers, search_stocks, NIFTY50_STOCKS, get_all_quotes
)
from .predictor import analyse, bulk_scan
from .models import WatchlistItem, Portfolio, PredictionLog


@api_view(["GET"])
def market_overview(request):
    indices = get_market_indices()
    movers  = get_top_movers()
    return Response({"indices": indices, "gainers": movers["gainers"], "losers": movers["losers"]})


@api_view(["GET"])
def all_stocks(request):
    quotes = get_all_quotes()
    return Response(quotes)


@api_view(["GET"])
def stock_quote(request, symbol):
    return Response(get_quote(symbol.upper(), request.GET.get("exchange", "NSE")))


@api_view(["GET"])
def stock_history(request, symbol):
    candles = get_historical(
        symbol.upper(),
        request.GET.get("exchange", "NSE"),
        request.GET.get("interval", "day"),
        int(request.GET.get("days", 60)),
    )
    return Response({"symbol": symbol.upper(), "candles": candles})


@api_view(["GET"])
def predict(request, symbol):
    trade_type = request.GET.get("type", "intraday")
    days       = 60 if trade_type == "longterm" else 30
    candles    = get_historical(symbol.upper(), "NSE", "day", days)
    result     = analyse(candles, symbol.upper(), trade_type)

    PredictionLog.objects.create(
        symbol=symbol.upper(), prediction_type=trade_type,
        signal=result["signal"], confidence=result["confidence"],
        predicted_price=result.get("target1"),
    )
    return Response(result)


@api_view(["GET"])
def scan_top_picks(request):
    trade_type = request.GET.get("type", "intraday")
    limit      = int(request.GET.get("limit", 8))
    days       = 60 if trade_type == "longterm" else 30

    candles_map = {s["symbol"]: get_historical(s["symbol"], "NSE", "day", days)
                   for s in NIFTY50_STOCKS}

    picks = bulk_scan(candles_map, trade_type)[:limit]
    info  = {s["symbol"]: s for s in NIFTY50_STOCKS}
    for p in picks:
        s = info.get(p["symbol"], {})
        p["name"]   = s.get("name", p["symbol"])
        p["sector"] = s.get("sector", "")
    return Response({"picks": picks, "type": trade_type})


@api_view(["GET"])
def search(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return Response([])
    results = search_stocks(q)
    # add live quotes
    for r in results:
        q_data = get_quote(r["symbol"])
        r.update({"last_price": q_data["last_price"], "change_pct": q_data["change_pct"]})
    return Response(results)


# ── Watchlist ────────────────────────────────────────────────────────────────

@api_view(["GET"])
def watchlist(request):
    items = WatchlistItem.objects.all()
    data  = []
    for item in items:
        q = get_quote(item.symbol, item.exchange)
        pred = analyse(get_historical(item.symbol, "NSE", "day", 20), item.symbol, "intraday")
        data.append({
            "id": item.id, "symbol": item.symbol, "exchange": item.exchange,
            **q, "signal": pred["signal"], "confidence": pred["confidence"],
        })
    return Response(data)


@api_view(["POST"])
def add_watchlist(request):
    symbol   = request.data.get("symbol", "").upper()
    exchange = request.data.get("exchange", "NSE")
    if not symbol:
        return Response({"error": "symbol required"}, status=400)
    obj, created = WatchlistItem.objects.get_or_create(symbol=symbol, exchange=exchange)
    return Response({"id": obj.id, "symbol": obj.symbol, "created": created})


@api_view(["DELETE"])
def remove_watchlist(request, pk):
    WatchlistItem.objects.filter(pk=pk).delete()
    return Response({"deleted": True})


# ── Portfolio ─────────────────────────────────────────────────────────────────

@api_view(["GET"])
def portfolio(request):
    items = Portfolio.objects.all()
    total_invested = total_current = 0
    holdings = []
    for item in items:
        q = get_quote(item.symbol)
        invested      = item.buy_price * item.quantity
        current_val   = q["last_price"] * item.quantity
        pnl           = current_val - invested
        total_invested += invested
        total_current  += current_val
        holdings.append({
            "id": item.id, "symbol": item.symbol, "quantity": item.quantity,
            "buy_price": item.buy_price, "current_price": q["last_price"],
            "investment_type": item.investment_type,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl / invested * 100, 2) if invested else 0,
            "current_value": round(current_val, 2),
        })
    total_pnl = total_current - total_invested
    return Response({
        "holdings": holdings,
        "total_invested":  round(total_invested, 2),
        "total_current":   round(total_current, 2),
        "total_pnl":       round(total_pnl, 2),
        "total_pnl_pct":   round(total_pnl / total_invested * 100, 2) if total_invested else 0,
    })


@api_view(["POST"])
def add_portfolio(request):
    symbol   = request.data.get("symbol", "").upper()
    qty      = int(request.data.get("quantity", 0))
    price    = float(request.data.get("buy_price", 0))
    inv_type = request.data.get("investment_type", "longterm")
    if not symbol or not qty or not price:
        return Response({"error": "symbol, quantity and buy_price required"}, status=400)
    obj = Portfolio.objects.create(symbol=symbol, quantity=qty,
                                   buy_price=price, investment_type=inv_type)
    return Response({"id": obj.id, "symbol": obj.symbol})


@api_view(["DELETE"])
def remove_portfolio(request, pk):
    Portfolio.objects.filter(pk=pk).delete()
    return Response({"deleted": True})


@api_view(["GET"])
def nifty50(request):
    return Response(NIFTY50_STOCKS)
