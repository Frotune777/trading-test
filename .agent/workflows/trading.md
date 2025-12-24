---
description: End-to-End Trading Platform Development Workflow
---

You are an expert systems engineer and quantitative platform architect.

Your task is to iteratively design, implement, and validate a
production-grade algorithmic trading platform.

You must follow the workflow phases strictly in order.
Each phase has entry criteria, exit criteria, and validation rules.

Do NOT skip phases.
Do NOT introduce ML or automation before market correctness and execution safety.

========================================================
GLOBAL RULES (APPLY TO ALL PHASES)
========================================================

1. Safety > Performance > Features
2. Determinism > Heuristics
3. Explainability > Black-box behavior
4. Real-time correctness before backtesting sophistication
5. Every automated action must be observable and reversible

========================================================
PHASE 1: REAL-TIME & EXECUTION (FOUNDATION)
========================================================

GOAL:
Establish a correct, low-latency, safe real-time trading foundation.

--------------------------------
1.1 OpenAlgo Socket Bridge ✅
--------------------------------
Status: COMPLETED

Responsibilities:
- Stream real-time ticks (LTP/Quotes)
- Enforce feed health states
- Redis hybrid cache
- Candle boundary awareness
- Execution safety gates

Validation:
- Feed health observable
- Execution blocked when unsafe
- Dry-run fully functional

--------------------------------
1.2 Interactive Dashboard ⏳
--------------------------------
Objective:
Build a WebSocket-driven UI that reflects real-time system truth.

Tasks:
- WebSocket gateway from backend → frontend
- Push live:
  - LTP updates
  - Feed health (HEALTHY / DEGRADED / DOWN)
  - Execution readiness
  - Alerts & candle closes

Constraints:
- UI must never poll for real-time data
- UI must show WHY actions are blocked

Exit Criteria:
- UI mirrors backend state in <500ms
- No phantom prices or stale data

--------------------------------
1.3 OpenAlgo Order Placement ✅
--------------------------------
Status: COMPLETED

Responsibilities:
- Decision → Execution pipeline
- Dry-run vs Live enforcement
- Kill switch
- Audit persistence

Validation:
- No live order possible without explicit enablement
- Every attempt explainable

========================================================
PHASE 2: INTELLIGENCE & STRATEGY
========================================================

GOAL:
Create deterministic, testable, strategy intelligence.

--------------------------------
2.1 Strategy Manager (DSL)
--------------------------------
Objective:
Design a Python-based strategy DSL.

Tasks:
- Define strategy schema
- Save/load strategies from DB
- Version strategies immutably
- Parameterize indicators

Constraints:
- Strategies must be stateless per tick
- All parameters must be serializable

Exit Criteria:
- Strategy can be replayed historically
- Strategy changes are versioned

--------------------------------
2.2 Backtest Engine 2.0
--------------------------------
Objective:
High-fidelity simulation engine.

Tasks:
- Event-driven backtesting
- Candle + tick compatibility
- Simulated execution with slippage
- Use same ExecutionGate logic

Constraints:
- No duplicated logic between live & backtest
- Backtest must reuse strategy DSL

Exit Criteria:
- Backtest == Live logic equivalence

--------------------------------
2.3 Effective TA Aggregator
--------------------------------
Objective:
Combine indicators intelligently.

Tasks:
- Regime detection (trend / range / volatility)
- Dynamic indicator weighting
- Confidence scoring

Constraints:
- Indicators must be explainable
- Aggregation must output confidence, not just signal

========================================================
PHASE 3: ML EVOLUTION & AUTO-TUNING
========================================================

GOAL:
Improve performance without breaking determinism.

--------------------------------
3.1 ML Auto-Tuner
--------------------------------
Objective:
Automated hyperparameter optimization.

Tasks:
- Grid / Bayesian optimization
- Backtest-driven evaluation
- Prevent overfitting

Constraints:
- ML cannot bypass strategy DSL
- Must log all experiments

--------------------------------
3.2 Model Promotion Pipeline
--------------------------------
Objective:
Safely deploy best-performing models.

Tasks:
- Champion/challenger evaluation
- Auto-promotion with thresholds
- Rollback capability

Constraints:
- No silent model replacement
- Human override always available

--------------------------------
3.3 Feature Engineering 2.0
--------------------------------
Objective:
Integrate alternative data.

Tasks:
- News sentiment
- Social signals
- Market breadth

Constraints:
- Features must be time-aligned
- No future leakage

========================================================
PHASE 4: AUTOMATION & ALERTS
========================================================

GOAL:
Move from assisted trading to controlled autonomy.

--------------------------------
4.1 Trading Bot Service
--------------------------------
Objective:
Autonomous execution with risk control.

Tasks:
- Strategy scheduling
- Position management
- Risk enforcement

Constraints:
- Must obey ExecutionGate
- Must emit alerts for every action

--------------------------------
4.2 Job Scheduler (Cron)
--------------------------------
Objective:
Operational reliability.

Tasks:
- Daily data refresh
- ML retraining
- Health checks

Constraints:
- Use APScheduler (IST only)
- Jobs must be observable

--------------------------------
4.3 Alert Engine ✅
--------------------------------
Status: COMPLETED

Responsibilities:
- Multi-channel alerts
- Feed, execution, risk notifications

========================================================
PHASE 5: QA & PRODUCTION
========================================================

GOAL:
Production-readiness at scale.

--------------------------------
5.1 End-to-End Testing
--------------------------------
Objective:
Confidence in full trade lifecycle.

Tasks:
- Playwright tests
- Mock OpenAlgo
- Failure injection

--------------------------------
5.2 Performance Audit
--------------------------------
Objective:
Latency & throughput optimization.

Tasks:
- Tick handling benchmarks
- Redis pressure testing
- WebSocket fan-out tuning

--------------------------------
5.3 Deployment Strategy
--------------------------------
Objective:
Resilient production deployment.

Tasks:
- Docker hardening
- Kubernetes / Swarm
- Zero-downtime deploys

========================================================
FINAL SUCCESS CRITERIA
========================================================

The system is considered COMPLETE when:
- Live trading is safe, explainable, and reversible
- Strategy logic is replayable
- ML improves performance without hiding logic
- UI reflects true system state
- Failures degrade safely, not catastrophically
