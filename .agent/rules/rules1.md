---
trigger: always_on
---

# ANTIGRAVITY_CORE_RULES.md
# (Authoritative • Execution-Safe • OpenAlgo Aligned)

---

## Authority, Safety & Execution Rules

1. The Agent must NEVER place, trigger, simulate, or schedule a LIVE trade.
2. The Agent must NEVER bypass the ExecutionGate.
3. The Agent must NEVER modify or suggest modifying:
   - EXECUTION_ENABLED
   - EXECUTION_MODE
4. The Agent must NEVER assume execution readiness under any condition.
5. The Agent must NEVER fabricate:
   - Prices
   - LTPs
   - Ticks
   - Candle closes
   - Broker responses
   - Market state
6. If required data is missing, stale, or unsafe, the Agent must FAIL CLOSED.
7. The Agent must NEVER self-authorize autonomy.
8. The Agent must NEVER remove or bypass human override paths.
9. Any future autonomy must be explicitly opt-in, human-approved, and fully reversible.
10. The Agent must NEVER schedule itself to trade.

---

## Market Data Integrity Rules

11. OpenAlgo is the single source of market truth for real-time market data.
12. Redis real-time LTP is authoritative ONLY if freshness < 5 seconds.
13. If data freshness is unknown, it must be treated as STALE.
14. If data freshness is ≥ 5 seconds, it must be treated as STALE.
15. If feed health is not explicitly marked HEALTHY, it must be treated as UNSAFE.
16. The Agent must NEVER infer market or intraday state.
17. Historical data must NEVER be mixed with real-time data silently.
18. The Agent must NEVER infer live prices or execution readiness from historical data.

---

## Data Source Classification Rules

19. All data sources must be explicitly classified:
    - Tier 1: Authoritative Real-Time (OpenAlgo)
    - Tier 2: Delayed / Historical (NSE)
    - Tier 3: Contextual / Fundamentals (Screener)
20. Tier 2 and Tier 3 data MUST be tagged as NON-REALTIME.
21. Tier 2 and Tier 3 data MUST NOT influence execution readiness.
22. Tier 2 and Tier 3 data MAY influence analysis only.
23. Every data object must carry:
    - source
    - timestamp
    - freshness
    - data_tier

---

## NSE Historical Data Rules (Tier 2)

24. NSE historical data is classified as Tier 2 (Delayed / Non-RealTime).
25. NSE historical data MAY be used for:
    - Backtesting
    - Indicator calculation
    - Historical analysis
26. NSE historical data MUST NOT be used to:
    - Infer live market state
    - Infer intraday movement
    - Determine execution readiness
27. NSE historical data MUST always be wrapped and tagged as:
    - NON-REALTIME
    - HISTORICAL
28. NSE historical data MUST NOT be directly accessed by strategy logic.
29. Strategies MUST consume NSE data only through approved data wrappers.

---

## Screener Financial Data Rules (Tier 3)

30. Screener financial data is classified as Tier 3 (Contextual).
31. Screener data MAY be used for:
    - Filtering
    - Ranking
    - Quality assessment
    - Long-term context
32. Screener data MUST NEVER influence:
    - Signal timing
    - Entry price
    - Exit price
    - Execution readiness
33. Screener data MUST NOT generate BUY, SELL, or HOLD signals.
34. Screener data MUST always be tagged as:
    - NON-REALTIME
    - FUNDAMENTAL
35. Screener data MUST be consumed as read-only context.

---

## Decision Generation Rules

36. The Agent may generate TradeDecisions, NOT TradeExecutions.
37. Every TradeDecision must be for exactly ONE symbol.
38. Every TradeDecision MUST include:
    - decision_id
    - strategy_name
    - symbol
    - signal (BUY / SELL / HOLD)
    - confidence_score
    - decision_time (IST, timezone-aware)
    - validity_window
39. Signals must be explicit, non-ambiguous, and non-implicit.
40. The Agent must NEVER merge multiple symbols into one decision.
41. The Agent must clearly separate:
    - Analysis
    - Signal
    - Execution Readiness

---

## Execution Readiness Rules

42. Execution readiness must ALWAYS be explicitly evaluated.
43. If execution is blocked, the block reason must be documented.
44. Every execution block must include:
    - Block reason
    - Data condition
    - Timestamp (IST)
45. The Agent must NEVER assume readiness based on partial or inferred signals.

---

## Project Phase Enforcement Rules

46. The Agent must follow project phases strictly.
47. The Agent must NOT introduce ML or AI models before:
    - Strategy Manager is complete
    - Backtest Engine 2.0 is validated
48. The Agent must NOT introduce automation without:
    - Alerting
    - Observability
    - Kill switches
49. The Agent must NOT skip any validation or testing step.

---

## Code & Architecture Rules

50. All code suggestions must be deterministic.
51. No hidden state or magic behavior is allowed.
52. No duplication of execution logic is allowed.
53. Shared logic must be reused across:
    - Backtest
    - Paper
    - Live (future)
54. Configuration must be explicit and version-controlled.
55. Time handling must be timezone-aware (IST).

---

## Testing & Validation Rules

56. Every critical component must have tests.
57. Failure scenarios must be explicitly tested.
58. OpenAlgo MUST be mocked in all tests.
59. NSE historical data MUST be mocked in all tests.
60. Screener financial data MUST be mocked in all tests.
61. Tests must explicitly verify:
    - Fail-closed behavior
    - Block reasons
    - Data freshness enforcement
62. No feature is considered DONE without validation criteria.
63. Test suites MUST achieve:
    - 100% total coverage
    - 100% pass rate

---

## Traceability & Audit Rules

64. Every TradeDecision must be traceable.
65. Every execution attempt (even if blocked) must be logged.
66. Every execution block must include an explicit reason.
67. Agent assumptions must be explicitly stated.
68. Silent failures are prohibited.

---

## UI Integrity Rules

69. UI must reflect backend truth only.
70. UI must NEVER infer state.
71. UI must clearly display:
    - Feed health
    - Data freshness
    - Execution block reasons
72. UI must NEVER show stale prices as live.

---

## Operational & Development Constraints

73. The current data source requires manual refresh.
74. Broker account integration for automated data fetching will be implemented in a later phase.
75. The Agent must analyze the project at code level before:
    - Creating plans
    - Adding tasks
    - Suggesting changes
76. Documentation must be updated whenever required.
77. All Python dependencies MUST be installed using uv.
78. All development MUST run inside a virtual environment.
79. No test may be declared PASS unless:
    - 100% coverage is achieved
    - 100% tests pass

---

## END OF CONTRACT
