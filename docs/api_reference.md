# Backend API Reference (v1.0)

This document provides a detailed reference for all existing API endpoints available in the Fortune Trading Platform.

## Base URL
`http://localhost:8000/api/v1`

---

## 🟢 Market Data (`/market`)

| Endpoint | Method | Parameters | Description |
| :------- | :----- | :--------- | :---------- |
| `/market/breadth` | `GET` | None | Advance/Decline ratio for the overall market. |
| `/market/activity/volume` | `GET` | None | Top 20 stocks by traded volume. |
| `/market/activity/value` | `GET` | None | Top 20 stocks by traded value. |
| `/market/indices` | `GET` | None | Live Nifty and Sensex data. |

### Example: Get Market Breadth
**Request:** `GET /api/v1/market/breadth`

**Response:**
```json
{
  "data": [
    {
      "symbol": "NIFTY 50",
      "advances": 32,
      "declines": 18,
      "unchanged": 0
    }
  ]
}
```

---

## 🔵 Derivatives (`/derivatives`)

| Endpoint | Method | Parameters | Description |
| :------- | :----- | :--------- | :---------- |
| `/derivatives/option-chain/{symbol}` | `GET` | `symbol` (str) | Integrated CE/PE option chain data. |
| `/derivatives/futures/{symbol}` | `GET` | `symbol` (str) | Futures price and open interest. |
| `/derivatives/pcr/{symbol}` | `GET` | `symbol` (str) | Put-Call Ratio for the specific symbol. |

---

## 🟡 Technicals (`/technicals`)

| Endpoint | Method | Parameters | Description |
| :------- | :----- | :--------- | :---------- |
| `/technicals/indicators/{symbol}` | `GET` | `symbol` (str) | 50+ TA-Lib indicators. |
| `/technicals/intraday/{symbol}` | `GET` | `symbol` (str), `interval` (str) | OHLCV data for charting. |

---

## 🟠 Insider & Corporate (`/insider`)

| Endpoint | Method | Parameters | Description |
| :------- | :----- | :--------- | :---------- |
| `/insider/trades` | `GET` | `from_date`, `to_date` | Institutional and insider trades. |
| `/insider/bulk-deals` | `GET` | `from_date`, `to_date` | Large volume bulk deals. |
| `/insider/block-deals` | `GET` | `from_date`, `to_date` | Pre-negotiated block deals. |
| `/insider/short-selling` | `GET` | `from_date`, `to_date` | Reported short-selling activity. |

---

## 🟣 Reasoning & Recommendations (`/recommendations`)

| Endpoint | Method | Parameters | Description |
| :------- | :----- | :--------- | :---------- |
| `/recommendations/` | `GET` | `strategy`, `limit` | Curated trade recommendations. |
| `/recommendations/{symbol}/reasoning` | `GET` | `symbol` | Full QUAD pillar analysis. |
