import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from app.services.analytics import (
    calculate_portfolio_history,
    compute_risk_metrics,
    calculate_portfolio_metrics
)

def test_calculate_portfolio_history_empty():
    assert calculate_portfolio_history([], {}).empty

def test_calculate_portfolio_history():
    holdings = [
        {"ticker": "AAPL", "quantity": 10},
        {"ticker": "MSFT", "quantity": 5}
    ]
    dates = pd.date_range(start="2026-01-01", periods=5)
    histories = {
        "AAPL": pd.Series([100.0, 102.0, 101.0, 105.0, 110.0], index=dates),
        "MSFT": pd.Series([200.0, 198.0, 202.0, 205.0, 210.0], index=dates)
    }
    
    port_history = calculate_portfolio_history(holdings, histories)
    assert len(port_history) == 5
    # Day 1: 10*100 + 5*200 = 2000
    assert port_history.iloc[0] == 2000.0
    # Day 5: 10*110 + 5*210 = 2150
    assert port_history.iloc[4] == 2150.0

def test_compute_risk_metrics_no_volatility():
    # Constant value portfolio
    dates = pd.date_range(start="2026-01-01", periods=10)
    portfolio_value = pd.Series([1000.0] * 10, index=dates)
    benchmark_value = pd.Series([100.0] * 10, index=dates)
    
    metrics = compute_risk_metrics(portfolio_value, benchmark_value)
    assert metrics["volatility"] == 0.0
    assert metrics["sharpe_ratio"] == 0.0
    assert metrics["max_drawdown"] == 0.0

def test_compute_risk_metrics_drawdown():
    dates = pd.date_range(start="2026-01-01", periods=3)
    # Peak at 1000, drops to 800, rises to 900
    portfolio_value = pd.Series([1000.0, 800.0, 900.0], index=dates)
    # Peak-to-trough drop is (1000-800)/1000 = 20%
    metrics = compute_risk_metrics(portfolio_value, pd.Series(dtype=float))
    assert abs(metrics["max_drawdown"] - 0.20) < 1e-4

def test_calculate_portfolio_metrics():
    holdings = [
        {"ticker": "AAPL", "quantity": 10, "buy_price": 100.0, "buy_date": date(2026, 1, 1)},
        {"ticker": "MSFT", "quantity": 5, "buy_price": 200.0, "buy_date": date(2026, 1, 1)}
    ]
    current_prices = {"AAPL": 120.0, "MSFT": 220.0}
    sectors = {"AAPL": "Tech", "MSFT": "Tech"}
    
    dates = pd.date_range(start="2026-01-01", periods=5)
    market_histories = {
        "AAPL": pd.Series([100.0, 105.0, 110.0, 115.0, 120.0], index=dates),
        "MSFT": pd.Series([200.0, 205.0, 210.0, 215.0, 220.0], index=dates)
    }
    
    metrics = calculate_portfolio_metrics(
        holdings=holdings,
        current_prices=current_prices,
        sectors=sectors,
        market_histories=market_histories,
        benchmark_history=None
    )
    
    # Cost basis = 10*100 + 5*200 = 2000
    assert metrics["summary"]["total_cost_basis"] == 2000.0
    # Current value = 10*120 + 5*220 = 2300
    assert metrics["summary"]["total_current_value"] == 2300.0
    # Absolute return = 2300 - 2000 = 300
    assert metrics["summary"]["absolute_return"] == 300.0
    # Percentage return = 300 / 2000 * 100 = 15%
    assert metrics["summary"]["percentage_return"] == 15.0
    
    # Check sector allocation (both Tech -> Tech = 100%)
    assert metrics["sector_allocations"]["Tech"] == 100.0
    
    # Check individual holding return (AAPL: cost = 1000, value = 1200, return = 200, pct = 20%)
    aapl_hd = next(h for h in metrics["holdings"] if h["ticker"] == "AAPL")
    assert aapl_hd["absolute_return"] == 200.0
    assert aapl_hd["percentage_return"] == 20.0
