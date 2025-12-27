# QUAD Analytics: Implementation & Fix Plan

**Created:** 2025-12-28 00:42 IST  
**Based On:** Feature Availability Audit (1.8% functional)  
**Target:** Achieve 80%+ feature completion in 90 days

---

## Executive Summary

This plan addresses the **three critical failure points** identified in the audit:
1. **Data Pipeline** - Empty tables, no data collection running
2. **API Layer** - 500 errors, broken endpoints
3. **Frontend Integration** - CORS issues, static data

**Approach:** Fix foundation first (data + APIs), then build features incrementally.

---

## Phase 0: Critical Fixes (Days 1-7) 🔴 URGENT

### Priority 1: Fix Data Pipeline

**Problem:** 0 records in technical_indicators, insider_trading, option_chain, quad_predictions, quad_signal_accuracy

**Tasks:**
- [ ] **Day 1:** Verify scheduler is running
  - Check `app/core/scheduler_config.py`
  - Verify cron jobs in Docker logs: `docker logs quad_backend | grep scheduler`
  - Enable debug logging for scheduler

- [ ] **Day 2:** Fix technical indicators collection
  - File: `backend/app/services/technical_analysis.py`
  - Verify NSE API connectivity
  - Test indicator calculation: RSI, MACD, Bollinger Bands, ATR
  - Create manual trigger: `POST /api/v1/data/collect-technicals`

- [ ] **Day 3:** Fix insider trading data
  - File: `backend/app/api/v1/endpoints/insider.py`
  - Verify NSE insider trading API
  - Populate `insider_trading` table with last 30 days data
  - Create scheduled job (daily 6 PM IST)

- [ ] **Day 4:** Fix options data collection
  - File: `backend/app/api/v1/endpoints/derivatives.py`
  - Test NSE option chain API for NIFTY, BANKNIFTY
  - Populate `option_chain` table
  - Create scheduled job (every 5 minutes during market hours)

- [ ] **Day 5:** Populate QUAD decisions
  - Run analysis for top 50 NIFTY stocks
  - Target: 50 stocks × 30 days = 1500 decisions minimum
  - Verify `quad_decisions` table growth

**Validation:**
```bash
# Run this after Day 5
python3 -c "
import sqlite3
conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM technical_indicators')
print(f'technical_indicators: {cursor.fetchone()[0]} (target: >1000)')
cursor.execute('SELECT COUNT(*) FROM insider_trading')
print(f'insider_trading: {cursor.fetchone()[0]} (target: >100)')
cursor.execute('SELECT COUNT(*) FROM option_chain')
print(f'option_chain: {cursor.fetchone()[0]} (target: >500)')
cursor.execute('SELECT COUNT(*) FROM quad_decisions')
print(f'quad_decisions: {cursor.fetchone()[0]} (target: >1500)')
conn.close()
"
```

---

### Priority 2: Fix API Endpoints

**Problem:** `/quad/{symbol}/history`, `/quad/{symbol}/timeline`, `/quad/{symbol}/accuracy` returning 500 errors

**Tasks:**
- [ ] **Day 6:** Debug quad analytics endpoints
  - File: `backend/app/services/quad_analytics_service.py`
  - Add try-catch with detailed logging
  - Test each endpoint individually:
    ```bash
    curl -v http://localhost:8000/api/v1/quad/RELIANCE/history?limit=5
    curl -v http://localhost:8000/api/v1/quad/RELIANCE/timeline?days=30
    curl -v http://localhost:8000/api/v1/quad/RELIANCE/accuracy?days=90
    ```
  - Fix database query issues (likely async/await problems)

- [ ] **Day 7:** Fix CORS issue
  - Verify Docker network configuration
  - Test: `curl -H "Origin: http://localhost:3010" -v http://localhost:8000/api/v1/health`
  - If needed, add explicit CORS headers to responses
  - Clear browser cache and test frontend

**Validation:**
```bash
# All should return 200 OK
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/quad/RELIANCE/history
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/quad/RELIANCE/timeline
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/quad/RELIANCE/accuracy
```

---

## Phase 1: Core Features (Days 8-30) 🟠 HIGH PRIORITY

### Week 2: Risk Management Basics

**Goal:** Implement VaR, Beta, Sharpe Ratio

**Tasks:**
- [ ] **Day 8-10:** Value at Risk (VaR)
  - Create: `backend/app/services/risk_metrics.py`
  - Implement historical VaR (95%, 99% confidence)
  - Add endpoint: `GET /api/v1/risk/{symbol}/var?days=30&confidence=95`
  - Add to database: `risk_metrics` table

- [ ] **Day 11-12:** Beta Calculation
  - Calculate beta vs NIFTY 50 (252-day rolling)
  - Add to `risk_metrics` table
  - Display on QUAD page: "Market Beta: 1.23"

- [ ] **Day 13-14:** Sharpe Ratio
  - Calculate risk-adjusted returns
  - Use risk-free rate: 6.5% (current India 10Y bond)
  - Display: "Sharpe Ratio: 1.8 (Good)"

**Frontend Integration:**
- Create: `frontend-new/src/components/quad/RiskMetrics.tsx`
- Display VaR, Beta, Sharpe in a card below Pillar Contribution

---

### Week 3: Actionable Trade Parameters

**Goal:** Entry/Exit zones, Stop-Loss, Position Sizing

**Tasks:**
- [ ] **Day 15-17:** Entry/Exit Zones
  - Create: `backend/app/services/trade_signals.py`
  - Calculate support/resistance using:
    - Fibonacci retracements
    - Pivot points
    - Volume-weighted levels
  - Return: `{ entry: [2850, 2870], exit: [2950, 2980], stop_loss: 2820 }`

- [ ] **Day 18-19:** Position Sizing
  - Implement Kelly Criterion
  - Risk-based sizing (1% account risk per trade)
  - Return: `{ shares: 50, capital: 142500, risk_amount: 1500 }`

- [ ] **Day 20-21:** Frontend Integration
  - Create: `frontend-new/src/components/quad/TradeSetup.tsx`
  - Display entry zones as horizontal lines on chart
  - Show position size calculator

**Validation:**
```bash
curl http://localhost:8000/api/v1/trade-signals/RELIANCE?conviction=76
# Expected: { entry: [...], exit: [...], stop_loss: ..., position_size: {...} }
```

---

### Week 4: Charting & Visualization

**Goal:** Candlestick charts, Volume overlay, Working timeline

**Tasks:**
- [ ] **Day 22-24:** Candlestick Chart
  - Use existing `price_history` data (289 records)
  - Library: Recharts (already in project)
  - Create: `frontend-new/src/components/charts/CandlestickChart.tsx`
  - Integrate into QUAD page

- [ ] **Day 25-26:** Fix Conviction Timeline
  - Debug chart sizing issue (`width(-1) height(-1)`)
  - Ensure parent container has explicit dimensions
  - Add volume bars below timeline

- [ ] **Day 27-28:** Volume Profile
  - Calculate volume by price level
  - Display as horizontal histogram
  - Highlight high-volume nodes (HVN) and low-volume nodes (LVN)

**Frontend Files:**
```
frontend-new/src/components/charts/
├── CandlestickChart.tsx (NEW)
├── ConvictionTimeline.tsx (FIX)
└── VolumeProfile.tsx (NEW)
```

---

## Phase 2: Advanced Analytics (Days 31-60) 🟡 MEDIUM PRIORITY

### Week 5-6: Backtesting & Validation

**Tasks:**
- [ ] **Day 29-35:** Signal Accuracy Tracking
  - Populate `quad_signal_accuracy` table
  - Track: Win rate, avg return, max drawdown per signal
  - Calculate: "BUY signals: 68% win rate, +4.2% avg return"

- [ ] **Day 36-42:** Equity Curve
  - Simulate following all QUAD signals
  - Calculate cumulative P&L
  - Display as line chart: "Following QUAD: +23% vs NIFTY: +12%"

**Endpoint:**
```
GET /api/v1/quad/{symbol}/backtest?start_date=2024-01-01&end_date=2024-12-31
Response: {
  win_rate: 0.68,
  total_trades: 45,
  avg_return: 0.042,
  max_drawdown: -0.08,
  equity_curve: [{date, value}, ...]
}
```

---

### Week 7-8: Comparative Analysis

**Tasks:**
- [ ] **Day 43-49:** Peer Comparison
  - Use existing `peers` table
  - Compare QUAD scores across sector
  - Display: "RELIANCE: 76% (Rank 3/15 in Energy)"

- [ ] **Day 50-56:** Sector Heatmap
  - Calculate avg conviction by sector
  - Create heatmap: Energy (72%), IT (65%), Banking (58%)
  - Use: `frontend-new/src/components/charts/SectorHeatmap.tsx`

**Frontend Component:**
```tsx
<PeerComparison 
  symbol="RELIANCE"
  peers={[
    {symbol: "ONGC", conviction: 82, rank: 1},
    {symbol: "BPCL", conviction: 78, rank: 2},
    {symbol: "RELIANCE", conviction: 76, rank: 3},
    ...
  ]}
/>
```

---

### Week 9: ML Predictions

**Tasks:**
- [ ] **Day 57-60:** Activate ML Service
  - File: `backend/app/services/quad_ml_service.py` (already exists!)
  - Train model on existing `quad_decisions` data
  - Populate `quad_predictions` table
  - Display: "Predicted Conviction (7d): 78% ±3%"

---

## Phase 3: Interactivity & UX (Days 61-90) 🟢 NICE TO HAVE

### Week 10-11: Custom Configuration

**Tasks:**
- [ ] **Day 61-70:** Weight Adjustment UI
  - Allow users to modify pillar weights
  - Recalculate conviction in real-time
  - Show: "Original: 76% → Custom: 82%"

- [ ] **Day 71-77:** Alert System
  - Activate existing `quad_alerts` API
  - Create frontend: `frontend-new/src/components/quad/AlertConfig.tsx`
  - Types: Conviction threshold, Signal change, Pillar drift

---

### Week 12-13: Reporting & Export

**Tasks:**
- [ ] **Day 78-84:** PDF Export
  - Library: `pdfkit` or `reportlab`
  - Generate: QUAD Analysis Report with charts
  - Endpoint: `GET /api/v1/quad/{symbol}/report.pdf`

- [ ] **Day 85-90:** CSV Export
  - Export decision history, pillar scores, predictions
  - Endpoint: `GET /api/v1/quad/{symbol}/export.csv`

---

## Implementation Checklist

### Backend Services to Create
```
backend/app/services/
├── risk_metrics.py (NEW) - VaR, Beta, Sharpe
├── trade_signals.py (NEW) - Entry/Exit, Position Sizing
├── backtest_service.py (NEW) - Signal accuracy, Equity curve
└── peer_analysis.py (NEW) - Sector comparison
```

### Frontend Components to Create
```
frontend-new/src/components/
├── charts/
│   ├── CandlestickChart.tsx (NEW)
│   ├── VolumeProfile.tsx (NEW)
│   └── SectorHeatmap.tsx (NEW)
├── quad/
│   ├── RiskMetrics.tsx (NEW)
│   ├── TradeSetup.tsx (NEW)
│   ├── PeerComparison.tsx (NEW)
│   ├── AlertConfig.tsx (NEW)
│   └── BacktestResults.tsx (NEW)
```

### Database Tables to Populate
```sql
-- Priority 1 (Week 1)
technical_indicators (target: 1000+ records)
insider_trading (target: 100+ records)
option_chain (target: 500+ records)
quad_decisions (target: 1500+ records)

-- Priority 2 (Week 2-4)
risk_metrics (NEW table)
trade_signals (NEW table)
quad_signal_accuracy (populate existing)

-- Priority 3 (Week 5-8)
quad_predictions (populate existing)
peer_rankings (NEW table)
```

---

## Success Metrics

### End of Phase 0 (Day 7)
- ✅ All data tables have >100 records
- ✅ All API endpoints return 200 OK
- ✅ Frontend displays live data (not hardcoded)

### End of Phase 1 (Day 30)
- ✅ VaR, Beta, Sharpe Ratio displayed
- ✅ Entry/Exit zones calculated
- ✅ Candlestick chart integrated
- ✅ Feature completion: 25%

### End of Phase 2 (Day 60)
- ✅ Signal accuracy tracked
- ✅ Peer comparison working
- ✅ ML predictions active
- ✅ Feature completion: 60%

### End of Phase 3 (Day 90)
- ✅ Custom weight adjustment
- ✅ Alert system functional
- ✅ PDF/CSV export working
- ✅ Feature completion: 80%+

---

## Risk Mitigation

### Technical Risks
1. **NSE API Rate Limits** → Implement caching, use multiple data sources
2. **Database Performance** → Add indexes, optimize queries
3. **ML Model Accuracy** → Start with simple models, iterate

### Resource Risks
1. **Development Time** → Prioritize ruthlessly, cut scope if needed
2. **Data Quality** → Validate all data sources, handle missing data gracefully

---

## Daily Workflow

```bash
# Morning (9 AM)
1. Pull latest code
2. Review previous day's progress
3. Run tests: pytest backend/tests/

# Development (10 AM - 6 PM)
4. Implement tasks for the day
5. Write unit tests
6. Update documentation

# Evening (6 PM - 7 PM)
7. Deploy to Docker: docker-compose up -d --build
8. Run validation scripts
9. Update task.md checklist
10. Commit code with clear message
```

---

## Next Steps

1. **Review this plan** - Adjust timelines based on team size
2. **Create task.md** - Break down into daily tasks
3. **Start Phase 0** - Fix critical issues first
4. **Daily standups** - Track progress, unblock issues

**Estimated Effort:** 
- 1 developer: 90 days
- 2 developers: 45 days
- 3 developers: 30 days

Let's build this! 🚀
