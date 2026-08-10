from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import Base

class AIInsight(Base):
    __tablename__ = "ai_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    content = Column(JSON, nullable=False)
    portfolio_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    portfolio = relationship("Portfolio", back_populates="insights")
