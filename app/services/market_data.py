import time
import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional

class MarketDataService:
    def __init__(self, cache_ttl_seconds: int = 15):
        self.cache_ttl = cache_ttl_seconds
        # In-memory cache structure: { ticker: { "timestamp": float, "data": dict } }
        self.cache: Dict[str, Dict[str, Any]] = {}
        
    def get_ticker_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches current price, sector, and 1-year historical data for a ticker.
        Applies a simple in-memory caching layer with TTL.
        """
        now = time.time()
        ticker = ticker.strip().upper()
        
        # Check cache
        if ticker in self.cache:
            cached = self.cache[ticker]
            if now - cached["timestamp"] < self.cache_ttl:
                return cached["data"]
                
        # Cache miss: fetch from yfinance
        try:
            yt = yf.Ticker(ticker)
            
            # Fetch current price from historical daily close (most reliable)
            history_1d = yt.history(period="1d")
            if not history_1d.empty:
                current_price = float(history_1d["Close"].iloc[-1])
            else:
                info = yt.info
                current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
                if current_price is None:
                    raise ValueError(f"Could not fetch current price for {ticker}")
            
            # Fetch sector
            info = yt.info
            sector = info.get("sector", "Other")
            if not sector:
                sector = "Other"
                
            # Fetch 1 year of daily historical closing prices (for volatility, beta, drawdown)
            history_1y = yt.history(period="1y")
            if history_1y.empty:
                raise ValueError(f"No historical price data available for {ticker}")
                
            close_prices = history_1y["Close"]
            
            data = {
                "ticker": ticker,
                "current_price": current_price,
                "sector": sector,
                "history": {str(k.date()): float(v) for k, v in close_prices.items()},
                "history_series": close_prices
            }
            
            # Save to cache
            self.cache[ticker] = {
                "timestamp": now,
                "data": data
            }
            
            return data
            
        except Exception as e:
            raise ValueError(f"Error fetching market data for '{ticker}': {str(e)}")

market_data_service = MarketDataService()
