from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services.market_data import market_data_service
from app.services.analytics import calculate_portfolio_metrics

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/analytics", tags=["Analytics"])

@router.get("")
def get_portfolio_analytics(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
        
    holdings = portfolio.holdings
    if not holdings:
        return calculate_portfolio_metrics([], {}, {}, {}, None)
        
    holdings_list = []
    current_prices = {}
    sectors = {}
    market_histories = {}
    
    for h in holdings:
        holdings_list.append({
            "ticker": h.ticker,
            "quantity": h.quantity,
            "buy_price": h.buy_price,
            "buy_date": h.buy_date
        })
        
        try:
            ticker_data = market_data_service.get_ticker_data(h.ticker)
            current_prices[h.ticker] = ticker_data["current_price"]
            sectors[h.ticker] = ticker_data["sector"]
            market_histories[h.ticker] = ticker_data["history_series"]
        except Exception:
            # Fallback if a specific ticker fails
            current_prices[h.ticker] = h.buy_price
            sectors[h.ticker] = "Other"
            
    # Fetch Nifty 50 benchmark history for beta calculation
    benchmark_history = None
    try:
        benchmark_data = market_data_service.get_ticker_data("^NSEI")
        benchmark_history = benchmark_data["history_series"]
    except Exception:
        # Benchmark unavailable, beta calculation will fall back
        pass
        
    metrics = calculate_portfolio_metrics(
        holdings=holdings_list,
        current_prices=current_prices,
        sectors=sectors,
        market_histories=market_histories,
        benchmark_history=benchmark_history
    )
    
    return metrics
