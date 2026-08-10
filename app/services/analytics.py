import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

def calculate_portfolio_history(
    holdings: List[Dict[str, Any]], 
    market_histories: Dict[str, pd.Series]
) -> pd.Series:
    """
    Computes the 1-year historical daily value of the portfolio.
    holdings: list of dicts with keys: 'ticker', 'quantity'
    market_histories: dict of {ticker: pandas.Series (date -> close_price)}
    """
    if not holdings or not market_histories:
        return pd.Series(dtype=float)
    
    # Create a DataFrame of prices
    df_prices = pd.DataFrame()
    for holding in holdings:
        ticker = holding["ticker"]
        if ticker in market_histories:
            df_prices[ticker] = market_histories[ticker]
            
    if df_prices.empty:
        return pd.Series(dtype=float)
        
    # Forward fill/backward fill to handle slight date misalignments (e.g., trading halts)
    df_prices = df_prices.ffill().bfill()
    
    # Calculate daily portfolio value
    portfolio_value = pd.Series(0.0, index=df_prices.index)
    for holding in holdings:
        ticker = holding["ticker"]
        qty = holding["quantity"]
        if ticker in df_prices.columns:
            portfolio_value += df_prices[ticker] * qty
            
    return portfolio_value

def compute_risk_metrics(
    portfolio_value: pd.Series, 
    benchmark_value: pd.Series, 
    risk_free_rate: float = 0.06
) -> Dict[str, float]:
    """
    Computes annualized volatility, Sharpe ratio, beta, and max drawdown.
    All values returned as decimals/fractions.
    """
    metrics = {
        "volatility": 0.0,
        "sharpe_ratio": 0.0,
        "beta": 1.0,
        "max_drawdown": 0.0
    }
    
    if portfolio_value.empty or len(portfolio_value) < 3:
        return metrics
        
    # Daily returns
    port_returns = portfolio_value.pct_change().dropna()
    if port_returns.empty or port_returns.std() == 0:
        return metrics
        
    # 1. Volatility (Annualized standard deviation of daily returns)
    daily_std = port_returns.std()
    ann_volatility = daily_std * np.sqrt(252)
    metrics["volatility"] = float(ann_volatility)
    
    # 2. Annualized Return (based on daily mean return)
    ann_return = port_returns.mean() * 252
    
    # 3. Sharpe Ratio
    if ann_volatility > 0:
        metrics["sharpe_ratio"] = float((ann_return - risk_free_rate) / ann_volatility)
        
    # 4. Maximum Drawdown
    running_max = portfolio_value.cummax()
    drawdowns = (portfolio_value - running_max) / running_max
    metrics["max_drawdown"] = float(abs(drawdowns.min()))
    
    # 5. Beta against Benchmark
    if benchmark_value is not None and not benchmark_value.empty:
        benchmark_returns = benchmark_value.pct_change().dropna()
        
        # Align series by joining
        combined = pd.DataFrame({"port": port_returns, "bench": benchmark_returns}).dropna()
        if not combined.empty and len(combined) > 5:
            cov = combined["port"].cov(combined["bench"])
            var = combined["bench"].var()
            if var > 0:
                metrics["beta"] = float(cov / var)
                
    return metrics

def calculate_portfolio_metrics(
    holdings: List[Dict[str, Any]],
    current_prices: Dict[str, float],
    sectors: Dict[str, str],
    market_histories: Dict[str, pd.Series],
    benchmark_history: Optional[pd.Series] = None,
    risk_free_rate: float = 0.06
) -> Dict[str, Any]:
    """
    Computes all analytical metrics for the portfolio.
    """
    if not holdings:
        return {
            "summary": {
                "total_cost_basis": 0.0,
                "total_current_value": 0.0,
                "absolute_return": 0.0,
                "percentage_return": 0.0,
                "stock_hhi": 0.0,
                "sector_hhi": 0.0,
            },
            "holdings": [],
            "sector_allocations": {},
            "risk_metrics": {
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "beta": 1.0,
                "max_drawdown": 0.0
            },
            "historical_chart": []
        }

    total_cost_basis = 0.0
    total_current_value = 0.0
    holding_details = []
    
    for h in holdings:
        ticker = h["ticker"]
        qty = h["quantity"]
        buy_price = h["buy_price"]
        
        cost_basis = qty * buy_price
        curr_price = current_prices.get(ticker, buy_price)
        current_value = qty * curr_price
        
        abs_return = current_value - cost_basis
        pct_return = (abs_return / cost_basis * 100) if cost_basis > 0 else 0.0
        
        total_cost_basis += cost_basis
        total_current_value += current_value
        
        holding_details.append({
            "ticker": ticker,
            "quantity": qty,
            "buy_price": buy_price,
            "current_price": curr_price,
            "cost_basis": cost_basis,
            "current_value": current_value,
            "absolute_return": abs_return,
            "percentage_return": pct_return,
            "sector": sectors.get(ticker, "Other"),
            "weight": 0.0
        })
        
    # Calculate weights and sector allocation
    sector_values = {}
    for hd in holding_details:
        if total_current_value > 0:
            hd["weight"] = hd["current_value"] / total_current_value
        else:
            hd["weight"] = 0.0
            
        sector = hd["sector"]
        sector_values[sector] = sector_values.get(sector, 0.0) + hd["current_value"]
        
    sector_allocations = {}
    for sector, val in sector_values.items():
        sector_allocations[sector] = (val / total_current_value * 100) if total_current_value > 0 else 0.0
        
    # Herfindahl-Hirschman Index (HHI) for diversification
    stock_weights = [hd["weight"] for hd in holding_details]
    stock_hhi = sum(w**2 for w in stock_weights) if stock_weights else 0.0
    
    sector_weights = [val / total_current_value for val in sector_values.values()] if total_current_value > 0 else []
    sector_hhi = sum(w**2 for w in sector_weights) if sector_weights else 0.0
    
    # Portfolio returns
    total_abs_return = total_current_value - total_cost_basis
    total_pct_return = (total_abs_return / total_cost_basis * 100) if total_cost_basis > 0 else 0.0
    
    # Calculate historical series & risk metrics
    port_history = calculate_portfolio_history(holdings, market_histories)
    risk_metrics = compute_risk_metrics(port_history, benchmark_history, risk_free_rate)
    
    # Prepare historical series for chart
    chart_data = []
    if not port_history.empty:
        # Sort history by date to ensure proper ordering
        port_history = port_history.sort_index()
        for idx, val in port_history.items():
            # Convert timestamp index to string date
            date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)
            chart_data.append({
                "date": date_str,
                "value": float(val)
            })
            
    return {
        "summary": {
            "total_cost_basis": total_cost_basis,
            "total_current_value": total_current_value,
            "absolute_return": total_abs_return,
            "percentage_return": total_pct_return,
            "stock_hhi": stock_hhi,
            "sector_hhi": sector_hhi,
        },
        "holdings": holding_details,
        "sector_allocations": sector_allocations,
        "risk_metrics": risk_metrics,
        "historical_chart": chart_data
    }
