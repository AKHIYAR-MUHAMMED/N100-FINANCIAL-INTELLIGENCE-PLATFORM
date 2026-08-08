# Dashboard & Analytics REST API Specification

This document provides a comprehensive overview of the REST API endpoints exposed by `src/api_server.py` for the Nifty 100 Financial Analytics Dashboard.

## Base URL
```http
http://localhost:8000
```

---

## Endpoints Summary

| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/summary` | Get system status, DB row counts, DQ metrics, and sector distribution | None |
| `GET` | `/api/companies` | List all Nifty 100 constituent companies | `sector` (optional) |
| `GET` | `/api/health` | Service health check and database connection status | None |
| `GET` | `/api/analytics/risk` | Monte Carlo simulations and risk metrics for a ticker | `ticker` |
| `GET` | `/api/analytics/dupont` | 3-step and 5-step DuPont decomposition history | `company_id` |
| `GET` | `/api/screener/rank` | Multi-factor quantitative scoring and ranking | None |
| `GET` | `/api/failures` | Retrieve recent data quality (DQ) validation failures | None |
| `GET` | `/` | Serve interactive dashboard HTML frontend | None |

---

## Detailed Endpoint Specifications

### 1. Get System Summary
**Endpoint:** `GET /api/summary`

**Description:**
Returns high-level health metrics including total record count across database tables, data quality failure counts by severity (CRITICAL vs WARNING), sector distribution, and foreign key integrity status.

**Example Request:**
```bash
curl -X GET http://localhost:8000/api/summary
```

**Example Response (200 OK):**
```json
{
  "table_counts": {
    "companies": 92,
    "financial_ratios": 460,
    "profitandloss": 460,
    "balancesheet": 460,
    "cashflow": 460,
    "sectors": 11
  },
  "dq_summary": {
    "total": 14,
    "critical": 2,
    "warning": 12
  },
  "sector_distribution": {
    "Financial Services": 22,
    "IT Services": 14,
    "Automobile": 10
  },
  "fk_violations": 0,
  "status": "Healthy"
}
```

---

### 2. Get Companies List
**Endpoint:** `GET /api/companies`

**Description:**
Fetches master metadata for Nifty 100 companies. Optionally filter companies by sector name.

**Query Parameters:**
- `sector` *(string, optional)*: Filter by exact sector name (e.g., `Financial Services`, `IT Services`).

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/companies?sector=IT%20Services"
```

**Example Response (200 OK):**
```json
[
  {
    "ticker": "COMP01",
    "name": "Tata Consultancy Services",
    "sector_name": "IT Services",
    "industry": "IT Consulting & Software",
    "website": "https://www.tcs.com"
  }
]
```

---

### 3. Get Validation Failures
**Endpoint:** `GET /api/failures`

**Description:**
Returns up to the 100 most recent Data Quality (DQ) validation failures detected during ETL processing.

**Example Request:**
```bash
curl -X GET http://localhost:8000/api/failures
```

**Example Response (200 OK):**
```json
[
  {
    "failure_id": 104,
    "rule_id": "VAL_002",
    "ticker": "COMP45",
    "table_name": "financial_ratios",
    "column_name": "pe_ratio",
    "severity": "WARNING",
    "failure_reason": "PE ratio exceeds 3.0x sector median threshold"
  }
]
```

---

## Static Assets & Web Dashboard

The API server also acts as a static file server serving the single-page application (SPA) dashboard from `src/dashboard/`:
- `GET /` -> `index.html`
- `GET /styles.css` -> CSS styles
- `GET /app.js` -> JavaScript client logic
