from django.urls import path
from . import views

urlpatterns = [
    path("market/",                views.market_overview),
    path("stocks/",                views.all_stocks),
    path("quote/<str:symbol>/",    views.stock_quote),
    path("history/<str:symbol>/",  views.stock_history),
    path("predict/<str:symbol>/",  views.predict),
    path("scan/",                  views.scan_top_picks),
    path("search/",                views.search),
    path("watchlist/",             views.watchlist),
    path("watchlist/add/",         views.add_watchlist),
    path("watchlist/<int:pk>/remove/", views.remove_watchlist),
    path("portfolio/",             views.portfolio),
    path("portfolio/add/",         views.add_portfolio),
    path("portfolio/<int:pk>/remove/", views.remove_portfolio),
    path("nifty50/",               views.nifty50),
]
