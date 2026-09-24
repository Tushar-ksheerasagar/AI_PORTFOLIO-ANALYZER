<div align="center">

# AI Portfolio Analyzer

### Read the market. Understand the risk. Invest with context.

A full-stack portfolio intelligence dashboard for Indian equities, combining live NSE/BSE data, quantitative analytics, and Mistral AI commentary in one focused workspace.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-Insights-FF7000?style=for-the-badge)](https://mistral.ai/)

[Run locally](#-run-locally) | [Configure](#-configure) | [API map](#-api-map) | [Test](#-test)

</div>

---

## The product

AI Portfolio Analyzer turns a collection of holdings into a readable decision surface. Create portfolios, add Indian equity positions, inspect performance and risk, then ask the AI layer to explain what the numbers suggest.

| Track | Understand | Act |
| --- | --- | --- |
| NSE/BSE prices and history | Returns, volatility, beta, Sharpe ratio, drawdown, and concentration | Review AI summaries, risk notes, diversification, and watch lists |

## What is inside

### Portfolio workspace

- Secure registration, login, logout, and HttpOnly JWT cookies
- Multiple portfolios with create, select, and delete workflows
- Holdings captured with ticker, quantity, purchase price, and purchase date

### Market intelligence

- `yfinance` market data for NSE/BSE symbols
- Cached ticker history to reduce repeated upstream requests
- Nifty 50 and S&P BSE Sensex cards
- Business headlines with a fallback response when the feed is unavailable

### Decision support

- Return and risk analytics for each portfolio
- Mistral AI summaries, risk commentary, diversification analysis, and watch lists
- FastAPI Swagger UI and ReDoc for API exploration

## Architecture

```text
Browser (HTML + CSS + JavaScript + Chart.js)
                |
                v
       FastAPI application
        /       |        \
       v        v         v
 PostgreSQL  yfinance  Mistral AI
(SQLAlchemy) (market)  (insights)
```

| Layer | Tools |
| --- | --- |
| Interface | HTML, vanilla JavaScript, CSS, Chart.js |
| API | FastAPI, Uvicorn, Pydantic |
| Data | PostgreSQL, SQLAlchemy |
| Intelligence | yfinance, Mistral AI, LangChain |
| Quality | pytest, in-memory SQLite test database |

## Project map

```text
app/
  core/       Configuration, database, and security helpers
  models/     SQLAlchemy ORM models
  routers/    Authentication, portfolio, holding, analytics, and insight APIs
  schemas/    Pydantic request and response schemas
  services/   Market data, analytics, and AI services
  main.py     FastAPI app and frontend static-file mount
frontend/     SPA HTML, CSS, and JavaScript
tests/        Analytics and endpoint tests
.env.example  Environment variable template
```

## Run locally

### 1. Requirements

- Python 3.10 or newer
- PostgreSQL running locally or remotely
- A Mistral AI API key for AI insights

### 2. Install

```bash
git clone https://github.com/Tushar-ksheerasagar/AI_PORTFOLIO-ANALYZER.git
cd AI_PORTFOLIO-ANALYZER
python -m venv venv
```

Activate the environment:

```powershell
# Windows PowerShell
venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configure

Create a local environment file from the template:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# Linux/macOS
cp .env.example .env
```

Set the required values in `.env`:

```dotenv
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/portfolio_db
MISTRAL_API_KEY=your_mistral_api_key_here
JWT_SECRET_KEY=change_this_to_a_long_random_secret
```

Use a long, unique `JWT_SECRET_KEY` outside local development. The `.env` file is excluded by `.gitignore` and should never be committed.

## Start the dashboard

```bash
uvicorn app.main:app --reload
```

Open the application at **http://127.0.0.1:8000**. Missing database tables are created when the app starts.

| Resource | URL |
| --- | --- |
| Dashboard | http://127.0.0.1:8000 |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

## API map

| Area | Endpoint | Purpose |
| --- | --- | --- |
| Auth | `/api/auth` | Registration, login, logout, and current user |
| Portfolios | `/api/portfolios` | Create and manage portfolios |
| Holdings | `/api/holdings` | Add and manage positions |
| Analytics | `/api/analytics` | Calculate portfolio metrics |
| Insights | `/api/insights` | Generate AI portfolio commentary |
| Market | `/api/market/indices` | Read Nifty 50 and Sensex data |
| News | `/api/market/news` | Read business headlines |

## Test

```bash
python -m pytest -q
```

The suite uses an in-memory SQLite database, so PostgreSQL is not required to run the tests.

---

<div align="center">

Built with FastAPI, PostgreSQL, yfinance, and Mistral AI.

</div>
