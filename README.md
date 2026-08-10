# 🚀 AI Portfolio Analyzer

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-336791.svg)](https://www.postgresql.org/)
[![Mistral AI](https://img.shields.io/badge/Mistral%20AI-Large%20%2F%20Ministral-ff7000.svg)](https://mistral.ai/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-minded, full-stack investment portfolio analytics application that tracks Indian equity positions (NSE/BSE), calculates advanced performance and quantitative risk metrics (volatility, Sharpe ratio, beta, drawdowns, and Herfindahl-Hirschman concentration index), and generates plain-English diagnostic commentary using **Mistral AI** & **LangChain**.

---

## ✨ Key Features

- 📊 **Real-time NSE/BSE Market Data:** Integrates with `yfinance` to fetch live prices and historical series with an in-memory TTL cache to minimize API latency.
- 📐 **Quantitative Financial Analytics Engine:** Computes fundamental risk & return metrics:
  - **Sharpe Ratio** (Risk-adjusted returns relative to risk-free rate)
  - **Beta coefficient** (Market benchmark sensitivity vs Nifty 50)
  - **Annualized Volatility** & **Maximum Drawdown**
  - **Herfindahl-Hirschman Index (HHI)** for sector concentration analysis
- 🤖 **AI Portfolio Diagnostics & Conversational Advisor:** Powered by **Mistral AI** (`mistral-large-latest`, `ministral-8b-latest`) via **LangChain** with Pydantic structured outputs and intelligent offline fallback engine.
- 🎨 **Glassmorphic SPA Frontend:** Modern responsive dark-theme dashboard powered by HTML5, Vanilla CSS, and **Chart.js** interactive visual graphs.
- 🔒 **Secure Cookie-Based Auth:** Cookie-based HttpOnly JWT authentication flow with direct `bcrypt` password hashing.
- 🧪 **Offline Automated Testing:** Complete test suite written with `pytest` using SQLite in-memory overrides for zero-dependency local testing.

---

## 🛠️ Tech Stack

* **Frontend**: HTML5, Vanilla CSS (Glassmorphism design system), JavaScript (ES6+ SPA), Chart.js.
* **Backend**: FastAPI (Python), Uvicorn ASGI server.
* **Database**: PostgreSQL + SQLAlchemy ORM.
* **Market Data**: `yfinance` integration (with TTL caching).
* **AI Layer**: Mistral AI API (`mistral-large-latest` / `ministral-8b-latest`) & LangChain (`ChatMistralAI`).
* **Authentication**: Cookie-based HttpOnly JWT tokens + `bcrypt` password security.

---

## 📁 Directory Structure

```
├── app/
│   ├── core/
│   │   ├── config.py           # Config loader (.env using pydantic-settings)
│   │   ├── database.py         # SQLAlchemy engine & session dependency
│   │   └── security.py         # Password hashing & JWT security helpers
│   ├── models/
│   │   ├── base.py             # Declarative Base
│   │   ├── user.py             # User ORM model
│   │   ├── portfolio.py        # Portfolio ORM model
│   │   ├── holding.py          # Stock Holding ORM model
│   │   └── insight.py          # Cached AI Commentary ORM model
│   ├── schemas/
│   │   ├── user.py             # User registration & auth schemas
│   │   ├── portfolio.py        # Portfolio CRUD schemas
│   │   ├── holding.py          # Holding CRUD validation schemas
│   │   └── insight.py          # Mistral AI structured output schemas
│   ├── services/
│   │   ├── market_data.py      # yfinance scraper with TTL caching
│   │   ├── analytics.py        # Standalone financial math engine
│   │   ├── mistral_insights.py # Mistral AI structured outputs & insights
│   │   └── ai_agent.py         # LangChain conversational AI advisor & fallback
│   ├── routers/
│   │   ├── auth.py             # User authentication endpoints
│   │   ├── portfolios.py       # Portfolio management routes
│   │   ├── holdings.py         # Holding addition & removal routes
│   │   ├── analytics.py        # Portfolio metrics calculation endpoint
│   │   └── insights.py         # AI diagnostic commentary routes
│   └── main.py                 # FastAPI application entrypoint & static mounts
├── frontend/
│   ├── css/
│   │   └── style.css           # Premium glassmorphic dark theme stylesheet
│   ├── js/
│   │   └── app.js              # SPA controller & Chart.js renderer
│   └── index.html              # Main HTML document
├── tests/
│   ├── test_analytics.py       # Standalone analytics math unit tests
│   └── test_endpoints.py       # End-to-end endpoint integration tests
├── .env.example                # Environment configuration template
├── .gitignore                  # Git exclusion rules
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
* **Python 3.10+**
* **PostgreSQL** running locally or cloud-hosted (Supabase, Neon, render)
* **Mistral AI API Key**

### 2. Installation & Setup

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/Tushar-ksheerasagar/AI_PORTFOLIO-ANALYZER.git
cd AI_PORTFOLIO-ANALYZER

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your parameters in `.env`:
* `DATABASE_URL`: PostgreSQL connection string (e.g. `postgresql://postgres:password@localhost:5432/portfolio_db`).
* `MISTRAL_API_KEY`: Your Mistral AI API key.
* `JWT_SECRET_KEY`: Secure random string for JWT signing.

### 4. Running the Backend Server

Launch Uvicorn server:

```bash
uvicorn app.main:app --reload
```

Navigate to **`http://localhost:8000`** in your browser. The backend automatically creates PostgreSQL tables on startup and serves the SPA frontend.

### 5. Interactive API Documentation

FastAPI auto-generates Swagger & ReDoc API specs:
* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

---

## 🧪 Running Automated Tests

Run the full automated test suite using `pytest`:

```bash
python -m pytest tests/
```

*The test suite overrides PostgreSQL sessions with in-memory SQLite, allowing offline execution without live database overhead.*

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
