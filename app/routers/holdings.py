from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.schemas.holding import HoldingCreate, HoldingResponse, HoldingUpdate
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.market_data import market_data_service

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/holdings", tags=["Holdings"])

def verify_portfolio_ownership(portfolio_id: int, user_id: int, db: Session) -> Portfolio:
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    return portfolio

@router.post("", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def add_holding(
    portfolio_id: int,
    holding_in: HoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_portfolio_ownership(portfolio_id, current_user.id, db)
    
    # Validate ticker with market data service
    try:
        market_data_service.get_ticker_data(holding_in.ticker)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ticker symbol '{holding_in.ticker}': {str(e)}"
        )
        
    new_holding = Holding(
        portfolio_id=portfolio_id,
        ticker=holding_in.ticker.strip().upper(),
        quantity=holding_in.quantity,
        buy_price=holding_in.buy_price,
        buy_date=holding_in.buy_date
    )
    db.add(new_holding)
    db.commit()
    db.refresh(new_holding)
    return new_holding

@router.put("/{holding_id}", response_model=HoldingResponse)
def update_holding(
    portfolio_id: int,
    holding_id: int,
    holding_in: HoldingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_portfolio_ownership(portfolio_id, current_user.id, db)
    
    holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.portfolio_id == portfolio_id
    ).first()
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found in this portfolio"
        )
        
    update_data = holding_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "ticker":
            continue  # Ticker is not allowed to change on update, just delete and re-add
        setattr(holding, field, value)
        
    db.commit()
    db.refresh(holding)
    return holding

@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(
    portfolio_id: int,
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_portfolio_ownership(portfolio_id, current_user.id, db)
    
    holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.portfolio_id == portfolio_id
    ).first()
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found in this portfolio"
        )
        
    db.delete(holding)
    db.commit()
    return
