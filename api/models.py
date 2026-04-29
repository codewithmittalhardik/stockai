from django.db import models

class WatchlistItem(models.Model):
    symbol = models.CharField(max_length=20)
    exchange = models.CharField(max_length=10, default='NSE')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.exchange}:{self.symbol}"

class Portfolio(models.Model):
    symbol = models.CharField(max_length=20)
    exchange = models.CharField(max_length=10, default='NSE')
    quantity = models.IntegerField()
    buy_price = models.FloatField()
    investment_type = models.CharField(max_length=20, choices=[('intraday', 'Intraday'), ('longterm', 'Long Term')])
    bought_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} x{self.quantity}"

class PredictionLog(models.Model):
    symbol = models.CharField(max_length=20)
    prediction_type = models.CharField(max_length=20)
    signal = models.CharField(max_length=10)  # BUY / SELL / HOLD
    confidence = models.FloatField()
    predicted_price = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} → {self.signal} ({self.confidence:.0%})"
