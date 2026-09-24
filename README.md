# AI Portfolio Analyzer

AI Portfolio Analyzer is a full-stack investment portfolio dashboard for Indian equities. It tracks NSE/BSE holdings, calculates portfolio performance and risk metrics, and generates plain-English diagnostics with Mistral AI.

## Features

- User registration, login, logout, and HttpOnly JWT cookie authentication
- Multiple portfolios with create, select, and delete workflows
- NSE/BSE market data from `yfinance`, with cached ticker history
- Portfolio analytics including returns, volatility, Sharpe ratio, beta, drawdown, and concentration
- AI portfolio summaries, risk commentary, diversification analysis, and watch lists
- Nifty 50 and S&P BSE Sensex market cards
- Business news feed with fallback data when an external feed is unavailable
- FastAPI Swagger and ReDoc documentation

## Technology

- Frontend: HTML, vanilla JavaScript, CSS, and Chart.js
- Backend: FastAPI and Uvicorn
- Database: PostgreSQL with SQLAlchemy
- Market data: `yfinance`
- AI: Mistral AI and LangChain
- Tests: pytest with an in-memory SQLite test database

## Project Structure

```text
app/
  core/       Configuration, database, and security helpers
  models/     SQLAlchemy ORM models
  routers/    Authentication, portfolio, holding, analytics, and insight APIs
  schemas/    Pydantic request and response schemas
  services/   Market data, analytics, and AI services
  main.py     FastAPI application and frontend static-file mount
frontend/     SPA HTML, CSS, and JavaScript
tests/        Analytics and endpoint tests
.env.example  Environment variable template
requirements.txt
```

## Requirements

- Python 3.10 or newer
- PostgreSQL running locally or remotely
- A Mistral AI API key for AI insights

## Installation

Clone the repository and create a virtual environment:

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

## Configuration

Copy `.env.example` to `.env` and update the values:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# Linux/macOS
cp .env.example .env
```

Required settings:

```dotenv
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/portfolio_db
MISTRAL_API_KEY=your_mistral_api_key_here
JWT_SECRET_KEY=change_this_to_a_long_random_secret
```

Use a long, unique `JWT_SECRET_KEY` outside local development. Keep `.env` private; it is excluded by `.gitignore`.

## Run the Application

Start the development server from the repository root:

```bash
uvicorn app.main:app --reload
```

Open the dashboard at <http://127.0.0.1:8000>. The application creates missing database tables on startup.

API documentation is available at:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## API Areas

- `/api/auth` - registration, login, logout, and current-user access
- `/api/portfolios` - portfolio management
- `/api/holdings` - holding management
- `/api/analytics` - portfolio metrics
- `/api/insights` - AI-generated portfolio insights
- `/api/market/indices` - Nifty 50 and Sensex data
- `/api/market/news` - business headlines

## Tests

Run the complete test suite:

```bash
python -m pytest -q
```

The tests use an in-memory SQLite database and do not require a running PostgreSQL instance.
