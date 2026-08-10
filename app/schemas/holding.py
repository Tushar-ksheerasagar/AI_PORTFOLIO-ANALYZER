from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

class HoldingBase(BaseModel):
    ticker: str = Field(..., description="Stock ticker (e.g. RELIANCE.NS, TCS.NS)")
    quantity: float = Field(..., gt=0, description="Quantity of shares purchased")
    buy_price: float = Field(..., gt=0, description="Price per share at purchase")
    buy_date: date = Field(..., description="Purchase date")

class HoldingCreate(HoldingBase):
    pass

class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    buy_price: Optional[float] = Field(None, gt=0)
    buy_date: Optional[date] = None

class HoldingResponse(HoldingBase):
    id: int
    portfolio_id: int
    created_at: datetime

    class Config:
        from_attributes = True
