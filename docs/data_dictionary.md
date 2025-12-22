# 📊 Exhaustive Data Dictionary (Fortune Trading QUAD)

This document is the "Master Registry" of all data points available in the system, audited from `NSEComplete`, `ScreenerEnhanced`, and specialized NSE utility scrapers.

---

## 1. Price & Delivery Data (`price_data`)
| Field Name | Type | Source | Description |
| :--- | :--- | :--- | :--- |
| `symbol` | `str` | Internal | Canonical identifier (e.g., `RELIANCE`) |
| `last_price` | `float` | `NseUtils` | Current Market Price (LTP) |
| `open` / `high` / `low`| `float` | `NSEMaster` | Day's session values |
| `previous_close` | `float` | `NseUtils` | Yesterday's adjusted close |
| `vwap` | `float` | `NseUtils` | Volume Weighted Average Price |
| `total_traded_volume`| `int` | `NseUtils` | Cumulative shares traded today |
| `deliverable_qty` | `int` | `BhavCopy` | Quantity of shares intended for delivery |
| `delivery_percent` | `float` | `BhavCopy` | % of volume that is delivery-based |
| `upper_circuit` | `float` | `NseUtils` | Maximum allowed price for the day |
| `lower_circuit` | `float` | `NseUtils` | Minimum allowed price for the day |
| `high_52w` / `low_52w`| `float` | `NseUtils` | 52-week price extremes (adjusted) |

---

## 2. Institutional Activity & Corporate Filings (`institutional`)
| Category | Source | Fields / Details |
| :--- | :--- | :--- |
| **FII/DII Activity** | `NseUtils` | Cash market buy/sell value for FIIs and DIIs |
| **Bulk Deals** | `NseUtils` | Symbol, Client Name, Buy/Sell, Quantity, Price |
| **Block Deals** | `NseUtils` | Large transactions handled in specific windows |
| **Insider Trading** | `NseUtils` | Promoter/Director trades, Buy/Sell, Value, Mode |
| **Short Selling** | `NseUtils` | Daily reported short-selling positions |
| **Corporate Actions** | `NseUtils` | Dividends, Splits, Bonus, Rights issues |
| **Announcements** | `NseUtils` | Exchange filings (Board meets, AGM, material news) |
| **Results Calendar** | `NseUtils` | Date of upcoming quarterly results/earnings |

---

## 3. Derivatives & Depth (`derivatives`)
| Category | Source | Key Fields captured |
| :--- | :--- | :--- |
| **Option Chain** | `NseUtils` | OI, Chng in OI, Volume, IV, Bid/Ask Depth, Strike |
| **Option Greeks** | *Derived* | Delta, Gamma, Theta, Vega, Rho (Calc via IV) |
| **Futures Data** | `NSEMaster` | Expiry price, Premium/Discount, Roll-over cost |
| **Most Active** | `NseUtils` | Top OI gainers, Turnover leaders (Contracts/Stocks) |
| **Market Depth** | `NseUtils` | Top 5 Bid/Ask Layer (Level 2 data) |

---

## 4. Fundamental Analysis (`fundamentals`)
| Category | Source | Deep Dive Line Items |
| :--- | :--- | :--- |
| **P&L (Annual)** | `Screener` | Sales, Expenses, Operating Profit, PAT, EPS |
| **Quarterly Results**| `Screener` | Sequential (%) and YoY (%) Growth comparisons |
| **Balance Sheet** | `Screener` | Share Capital, Reserves, Borrowings, Fixed Assets |
| **Cash Flow** | `Screener` | Operating CF, Investing CF, Financing CF |
| **Shareholding** | `Screener` | Promoter %, FII %, DII %, Public %, Pledged % |
| **Valuation Ratios**| `Screener` | P/E, P/B, EV/EBITDA, Interest Coverage |
| **Efficiency** | `Screener` | ROE, ROCE, Debtor Days, Inventory Turnover |

---

## 5. Market Sentiment & Indices (`market_data`)
| Category | Source | Description |
| :--- | :--- | :--- |
| **VIX** | `NSEMaster` | India VIX (Volatility Index) current levels |
| **Advance/Decline** | `NseUtils` | Ratio of rising vs falling stocks (Breath) |
| **Index P/E & Yield**| `NseUtils` | P/E, P/B and Dividend Yield for major indices |
| **Pre-Market** | `NseUtils` | Discovery prices from 9:00 AM - 9:08 AM |

---

## 🛡 Normalization Mapping Roles
1. **Identities**: `RELIANCE` (Standard) ↔ `RELIANCE.NS` (Yahoo) ↔ `RELIANCE` (NSE) ↔ `RELIANCE` (Screener).
2. **Units**: All financial values from Screener are normalized to **Crores (Cr)**.
3. **Decimals**: Price data rounded to 2 decimals; Greeks to 4 decimals.
4. **Timezones**: Inbound data localized to `Asia/Kolkata` and stored as `UTC`.
5. **Fallbacks**: If `NseUtils` (Live) is blocked, system falls back to `yfinance` Snapshot.
