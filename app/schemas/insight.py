from pydantic import BaseModel
from datetime import datetime
from typing import List

class AIInsightContent(BaseModel):
    summary: str
    risk_commentary: str
    diversification_note: str
    watch_items: List[str]
    disclaimer: str

class AIInsightResponse(BaseModel):
    id: int
    portfolio_id: int
    content: AIInsightContent
    portfolio_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class RecommendationItem(BaseModel):
    ticker: str
    name: str
    rationale: str
    risk: str

class RebalanceResponse(BaseModel):
    weak_stock: str
    reason_weak: str
    recommendations: List[RecommendationItem]
