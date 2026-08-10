from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.schemas.holding import HoldingResponse  # Wait, let's make sure holding schema is defined or handle import properly.

class PortfolioBase(BaseModel):
    name: str

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioResponse(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PortfolioDetail(PortfolioResponse):
    holdings: List[HoldingResponse] = []

    class Config:
        from_attributes = True
