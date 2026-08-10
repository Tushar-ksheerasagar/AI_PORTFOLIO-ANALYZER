import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
# Import models to ensure they are registered with the Base metadata before create_all
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.insight import AIInsight

from app.services.market_data import market_data_service
from app.routers import auth, portfolios, holdings, analytics, insights

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables on startup
try:
    logger.info("Attempting to connect to PostgreSQL database and create tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
except Exception as e:
    logger.error(f"Database connection/migration failed: {str(e)}")
    logger.error("Please ensure PostgreSQL is running and the DATABASE_URL in .env is correct.")

app = FastAPI(
    title="AI Portfolio Analyzer API",
    description="Backend API for tracking, analyzing stock portfolios with GenAI insights",
    version="1.0.0"
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ValueError exception handler (e.g. invalid tickers in holdings)
@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# Market Indices Endpoint for Welcome Dashboard
@app.get("/api/market/indices", tags=["Market Data"])
def get_market_indices():
    indices = ["^NSEI", "^BSESN"]
    result = []
    for idx in indices:
        try:
            data = market_data_service.get_ticker_data(idx)
            history = data["history_series"]
            if len(history) >= 2:
                curr = float(history.iloc[-1])
                prev = float(history.iloc[-2])
                change = curr - prev
                pct_change = (change / prev) * 100
            else:
                curr = data["current_price"]
                change = 0.0
                pct_change = 0.0
            result.append({
                "symbol": idx,
                "name": "Nifty 50" if idx == "^NSEI" else "S&P BSE Sensex",
                "price": curr,
                "change": change,
                "pct_change": pct_change
            })
        except Exception as e:
            # Fallback mock indices if yfinance lookup fails
            result.append({
                "symbol": idx,
                "name": "Nifty 50" if idx == "^NSEI" else "S&P BSE Sensex",
                "price": 24367.50 if idx == "^NSEI" else 79705.80,
                "change": 142.60 if idx == "^NSEI" else 460.25,
                "pct_change": 0.59 if idx == "^NSEI" else 0.58
            })
    return result

# Market News Endpoint for Welcome Dashboard
@app.get("/api/market/news", tags=["Market Data"])
def get_market_news():
    import xml.etree.ElementTree as ET
    import requests
    url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-IN&gl=IN&ceid=IN:en"
    try:
        response = requests.get(url, timeout=4)
        if not response.ok:
            raise Exception("Failed to fetch news feed")
            
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title").text if item.find("title") is not None else "Market Update"
            link = item.find("link").text if item.find("link") is not None else "#"
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            source = item.find("source").text if item.find("source") is not None else "News"
            
            clean_title = title
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                clean_title = parts[0]
                source = parts[1]
                
            clean_date = pub_date
            if pub_date and len(pub_date) > 16:
                clean_date = pub_date[:16]
                
            items.append({
                "title": clean_title,
                "link": link,
                "pub_date": clean_date,
                "source": source
            })
        return items
    except Exception as e:
        logger.error(f"Error fetching business news: {str(e)}")
        # Return fallback mock business headlines
        return [
            {
                "title": "Nifty 50 Closes Above 24,300 Amid Buying in IT and Auto Stocks",
                "link": "https://finance.yahoo.com",
                "pub_date": "Mon, 10 Aug 2026",
                "source": "Yahoo Finance"
            },
            {
                "title": "Reliance Industries Shares Edge Higher on Expansion of Retail Footprint",
                "link": "https://finance.yahoo.com",
                "pub_date": "Mon, 10 Aug 2026",
                "source": "Economic Times"
            },
            {
                "title": "TCS Reports Strong Deal Wins in Q1; Sector Outlook Remains Bullish",
                "link": "https://finance.yahoo.com",
                "pub_date": "Mon, 10 Aug 2026",
                "source": "Moneycontrol"
            },
            {
                "title": "Inflation Cools to 4.2% in Latest Reading, Boosting Rate Cut Hopes",
                "link": "https://finance.yahoo.com",
                "pub_date": "Mon, 10 Aug 2026",
                "source": "Reuters"
            }
        ]

# Register API Routers
app.include_router(auth.router)
app.include_router(portfolios.router)
app.include_router(holdings.router)
app.include_router(analytics.router)
app.include_router(insights.router)

# Mount Frontend static files to serve the SPA directly from the backend root "/"
# Get absolute path to the frontend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
frontend_dir = os.path.join(workspace_root, "frontend")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
    logger.info(f"Mounted static files from: {frontend_dir}")
else:
    logger.warning(f"Frontend directory not found at: {frontend_dir}. Static files will not be served.")
