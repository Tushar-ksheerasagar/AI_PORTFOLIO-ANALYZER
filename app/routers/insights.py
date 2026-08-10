import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.insight import AIInsight
from app.schemas.insight import AIInsightResponse
from app.services.market_data import market_data_service
from app.services.analytics import calculate_portfolio_metrics
from app.services.mistral_insights import generate_portfolio_hash, generate_ai_insights

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/insights", tags=["AI Insights"])

def compute_latest_metrics(portfolio: Portfolio, db: Session):
    holdings = portfolio.holdings
    if not holdings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate insights for a portfolio with no holdings."
        )
        
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
            current_prices[h.ticker] = h.buy_price
            sectors[h.ticker] = "Other"
            
    benchmark_history = None
    try:
        benchmark_data = market_data_service.get_ticker_data("^NSEI")
        benchmark_history = benchmark_data["history_series"]
    except Exception:
        pass
        
    return calculate_portfolio_metrics(
        holdings=holdings_list,
        current_prices=current_prices,
        sectors=sectors,
        market_histories=market_histories,
        benchmark_history=benchmark_history
    )

@router.get("", response_model=AIInsightResponse)
def get_insights(
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio has no holdings. Add some stock holdings first."
        )
        
    holdings_dict_list = [
        {
            "ticker": h.ticker,
            "quantity": h.quantity,
            "buy_price": h.buy_price,
            "buy_date": h.buy_date
        }
        for h in holdings
    ]
    
    current_hash = generate_portfolio_hash(holdings_dict_list)
    
    # Check cache in DB
    cached_insight = db.query(AIInsight).filter(AIInsight.portfolio_id == portfolio_id).first()
    if cached_insight and cached_insight.portfolio_hash == current_hash:
        return cached_insight
        
    # Cache miss: compute and fetch from AI service
    metrics = compute_latest_metrics(portfolio, db)
    insight_content = generate_ai_insights(metrics)
    
    if cached_insight:
        cached_insight.content = insight_content.model_dump()
        cached_insight.portfolio_hash = current_hash
        cached_insight.created_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(cached_insight)
        return cached_insight
    else:
        new_insight = AIInsight(
            portfolio_id=portfolio_id,
            content=insight_content.model_dump(),
            portfolio_hash=current_hash
        )
        db.add(new_insight)
        db.commit()
        db.refresh(new_insight)
        return new_insight

@router.post("/regenerate", response_model=AIInsightResponse)
def force_regenerate_insights(
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio has no holdings. Add some stock holdings first."
        )
        
    holdings_dict_list = [
        {
            "ticker": h.ticker,
            "quantity": h.quantity,
            "buy_price": h.buy_price,
            "buy_date": h.buy_date
        }
        for h in holdings
    ]
    current_hash = generate_portfolio_hash(holdings_dict_list)
    
    metrics = compute_latest_metrics(portfolio, db)
    insight_content = generate_ai_insights(metrics)
    
    cached_insight = db.query(AIInsight).filter(AIInsight.portfolio_id == portfolio_id).first()
    if cached_insight:
        cached_insight.content = insight_content.model_dump()
        cached_insight.portfolio_hash = current_hash
        cached_insight.created_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(cached_insight)
        return cached_insight
    else:
        new_insight = AIInsight(
            portfolio_id=portfolio_id,
            content=insight_content.model_dump(),
            portfolio_hash=current_hash
        )
        db.add(new_insight)
        db.commit()
        db.refresh(new_insight)
        return new_insight

from app.core.config import settings
from app.schemas.insight import ChatMessage, ChatRequest

@router.post("/chat")
def chat_with_advisor(
    portfolio_id: int,
    request: ChatRequest,
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
        metrics = {
            "summary": {
                "total_current_value": 0.0,
                "total_cost_basis": 0.0,
                "absolute_return": 0.0,
                "percentage_return": 0.0
            },
            "risk_metrics": {
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "beta": 0.0,
                "max_drawdown": 0.0
            },
            "sector_allocations": {},
            "holdings": []
        }
        sector_str = "None (Portfolio is empty)"
        holdings_str = "None (Portfolio is empty)"
    else:
        # 1. Compute metrics for context
        metrics = compute_latest_metrics(portfolio, db)
        
        # 2. Compile token-efficient summary lists
        sector_str = ", ".join([f"{k}: {v*100:.1f}%" for k, v in metrics["sector_allocations"].items()])
        holdings_str = "; ".join([
            f"{h['ticker']} ({h['sector']}): weight={h['weight']*100:.1f}%, overall return={h['percentage_return']:.1f}%"
            for h in metrics["holdings"]
        ])
    
    # 3. Delegate to LangChain Chat Agent with built-in Guardrails
    from app.services.ai_agent import run_chat_agent
    
    # Format message history to standard List[Dict]
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    response_text = run_chat_agent(
        message=request.message,
        history=history_dicts,
        metrics=metrics,
        holdings_str=holdings_str,
        sector_str=sector_str
    )
    
    return {"response": response_text}

from app.schemas.insight import RebalanceResponse

@router.post("/rebalance", response_model=RebalanceResponse)
def get_rebalance_recommendations(
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio has no holdings. Add some stock holdings first."
        )
        
    # 1. Compute metrics to get absolute/percentage returns
    metrics = compute_latest_metrics(portfolio, db)
    
    holdings_metrics = metrics.get("holdings", [])
    if not holdings_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No holdings metrics calculated. Make sure stock ticker data is available."
        )
        
    # 2. Find the weakest performing holding based on percentage return
    weakest_holding = min(holdings_metrics, key=lambda x: x["percentage_return"])
    
    # 3. Request recommendations from AI agent
    from app.services.ai_agent import recommend_stock_replacements
    recommendations = recommend_stock_replacements(
        weakest_ticker=weakest_holding["ticker"],
        weakest_sector=weakest_holding["sector"],
        weakest_return=weakest_holding["percentage_return"],
        weakest_buy_price=weakest_holding["buy_price"]
    )
    
    return recommendations
