# RecoScoreApp — Stock Recommendation Analyzer

> ⚠️ **Disclaimer:** This application is for **educational analytics purposes only**. It does not constitute investment advice. Past recommendation performance does not guarantee future results.

---

## Screenshots

### Dashboard — with 20 sample recommendations loaded

![Dashboard with data](docs/screenshots/dashboard_full.png)

### Dashboard — 30-day evaluation window

![Dashboard 30d window](docs/screenshots/dashboard_30d.png)

### Recommendations List

![Recommendations list](docs/screenshots/recommendations_list.png)

### Pipeline Ingestion Result

![Pipeline result](docs/screenshots/pipeline_result.png)

### Test Suite — 51/51 Passing

![Test results](docs/screenshots/test_results.png)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         RecoScoreApp                            │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │   React      │◄──►│  FastAPI Backend │◄──►│  PostgreSQL  │  │
│  │  Dashboard   │    │  (Port 8000)     │    │  Database    │  │
│  │  (Port 3000) │    │                  │    │              │  │
│  └──────────────┘    └────────┬─────────┘    └──────────────┘  │
│                               │                                 │
│                    ┌──────────▼──────────┐                      │
│                    │    Agent Pipeline   │                      │
│                    ├─────────────────────┤                      │
│                    │ 1. Ingestion Agent  │◄── Mock / Facebook   │
│                    │ 2. Extraction Agent │◄── Rule / LLM        │
│                    │ 3. Entity Agent     │◄── Alias Table       │
│                    │ 4. Market Data      │◄── yfinance / Mock   │
│                    │ 5. Scoring Agent    │                      │
│                    │ 6. Report Agent     │                      │
│                    └─────────────────────┘                      │
│                    APScheduler: periodic re-evaluation          │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
RecoScoreApp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── source_post.py
│   │   │   ├── recommendation.py
│   │   │   ├── price_snapshot.py
│   │   │   ├── recommendation_score.py
│   │   │   ├── ticker_alias.py
│   │   │   └── extraction_audit.py
│   │   ├── agents/              # Core agent logic
│   │   │   ├── ingestion_agent.py
│   │   │   ├── extraction_agent.py
│   │   │   ├── entity_resolution_agent.py
│   │   │   ├── market_data_agent.py
│   │   │   ├── scoring_agent.py
│   │   │   └── report_agent.py
│   │   ├── adapters/            # Pluggable ingestion adapters
│   │   │   ├── base_adapter.py  # Abstract interface
│   │   │   ├── mock_adapter.py  # Sample data (default)
│   │   │   └── facebook_adapter.py  # Facebook Graph API
│   │   ├── routers/             # FastAPI route handlers
│   │   │   ├── ingestion.py
│   │   │   ├── recommendations.py
│   │   │   ├── scores.py
│   │   │   └── reports.py
│   │   └── schemas/             # Pydantic request/response models
│   │       └── schemas.py
│   ├── seed_data/
│   │   └── sample_posts.json    # 20 synthetic sample posts
│   ├── tests/
│   │   ├── test_extraction.py   # Unit tests for parser
│   │   ├── test_scoring.py      # Unit tests for scoring formulas
│   │   └── test_api.py          # Integration tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main dashboard app
│   │   ├── api.js               # Axios API client
│   │   └── components/
│   │       ├── SummaryCards.jsx
│   │       ├── HitRateChart.jsx
│   │       ├── TopWorstTables.jsx
│   │       ├── RecommendationsList.jsx
│   │       └── IngestionPanel.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Data Models

| Model | Description |
|-------|-------------|
| `SourcePost` | Raw ingested posts from Facebook/mock |
| `Recommendation` | Extracted recommendations (ticker, action, prices, horizon) |
| `PriceSnapshot` | Price data at entry/30d/90d/180d/365d |
| `RecommendationScore` | Computed return and classification per window |
| `TickerAlias` | Maps names/aliases to canonical NSE/BSE tickers |
| `ExtractionAudit` | Audit trail of LLM/rule extraction |

## Scoring Formulas

**Buy/Hold:**
```
R = (P_now - P_entry) / P_entry
```

**Sell/Avoid:**
```
R = (P_entry - P_now) / P_entry
```

**Classification:**
- Good: R > +5%
- Bad: R < -5%
- Neutral: -5% ≤ R ≤ +5%

Evaluated at windows: 30d, 90d, 180d, 365d.
Horizon-aware: if post mentions "3 months", the 90d window is marked as primary.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingestion/trigger` | Run full pipeline (ingest → extract → resolve → price → score) |
| POST | `/ingestion/reprocess` | Re-fetch market data and recompute scores |
| POST | `/scores/recompute` | Recompute all scores |
| GET | `/recommendations` | List with filters (ticker, action, horizon, dates, classification) |
| GET | `/recommendations/{id}` | Recommendation detail with scores timeline |
| GET | `/reports/summary` | Overall metrics |
| GET | `/reports/hit-rate-by-month` | Monthly hit rates |
| GET | `/reports/top` | Top performing calls |
| GET | `/reports/worst` | Worst performing calls |
| GET | `/reports/full` | Full consolidated report |
| GET | `/health` | Health check |
| GET | `/docs` | Auto-generated Swagger UI |

## Local Setup (Quick Start)

### Option A: Docker Compose (recommended)

```bash
# Clone and navigate
cd RecoScoreApp

# Start all services
docker-compose up --build

# Access:
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

### Option B: Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Optional: copy .env.example to .env and configure

# Start server (uses SQLite by default)
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Access: http://localhost:5173
```

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing
```

Expected: **51 tests** (42 unit + 9 integration) all passing.

## Configuration (`.env`)

```env
# Database (default: SQLite)
DATABASE_URL=sqlite:///./recoscore.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost:5432/recoscore

# Ingestion adapter: mock | facebook
INGESTION_ADAPTER=mock

# Market data: mock | yfinance
MARKET_DATA_PROVIDER=mock

# Facebook Graph API (optional - requires app permissions)
FACEBOOK_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=stock.swami.859262

# LLM extraction (optional - requires OpenAI API key)
USE_LLM_EXTRACTION=false
OPENAI_API_KEY=

# Scoring thresholds
GOOD_THRESHOLD=0.05
BAD_THRESHOLD=-0.05

# Periodic recompute interval
SCORE_RECOMPUTE_INTERVAL_HOURS=24
```

## Agents

### 1. Ingestion Agent
- Pluggable adapter interface (`BaseIngestionAdapter`)
- **MockAdapter**: Loads 20 sample posts from `seed_data/sample_posts.json`
- **FacebookAdapter**: Uses official Graph API v19.0 (`pages_read_engagement` scope)
- Idempotent: skips duplicate `external_id`

### 2. Recommendation Extraction Agent
- **Rule-based** (primary): regex patterns for tickers, prices, actions, horizons
- Supports English and Hinglish (entry lo, kharid, becho, mahine, etc.)
- **LLM-based** (optional): GPT-4o-mini with structured JSON prompt
- Extraction audit trail stored in `ExtractionAudit`

### 3. Entity Resolution Agent
- 60+ built-in NSE aliases (RELIANCE, TCS, RIL→RELIANCE, HUL→HINDUNILVR, etc.)
- Fuzzy partial matching fallback
- Stores yfinance symbol for market data lookup

### 4. Market Data Agent
- **yfinance** provider (live data, NSE via `.NS` suffix)
- **Mock** provider (deterministic prices for testing)
- Fetches snapshots at entry, 30d, 90d, 180d, 365d

### 5. Scoring Agent
- Computes returns per window (buy/hold vs sell/avoid formulas)
- Classifies as good/bad/neutral/pending
- Horizon-aware: marks closest window as primary

### 6. Report Agent
- Summary metrics (total, good/bad/neutral, hit rate, avg return)
- Hit rate by month
- Top/worst 5 recommendations

## Dashboard Features

- 📊 **Summary Cards**: Total recs, Good/Bad/Neutral/Pending counts, Hit Rate, Avg Return
- 📈 **Hit Rate Chart**: Stacked bar chart by month with hit rate line
- 🏆 **Top/Worst Tables**: Best and worst performing calls
- 📋 **Recommendations List**: Filterable by ticker, action, horizon, date range
- ⚡ **Pipeline Controls**: Trigger ingestion, recompute scores

## Known Limitations & Next Steps

1. **Facebook API**: Requires page token with `pages_read_engagement` permission. Not publicly available for this specific page without authorization from the page owner.
2. **Ticker Extraction**: Rule-based approach may miss complex post formats. Increase LLM extraction for better coverage.
3. **Market Data**: yfinance may have rate limits for bulk operations. Consider a caching layer.
4. **Historical Data**: yfinance doesn't guarantee complete historical coverage for all NSE stocks.
5. **Hindi/Hinglish**: Current regex covers common patterns. NLP models would improve coverage.

**Phase 2 ideas:**
- Model confidence calibration
- Weekly automated report generation
- Slack/email notifications
- Redis caching for price snapshots
- Celery for distributed task processing
