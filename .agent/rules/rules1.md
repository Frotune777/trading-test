---
trigger: always_on
---

1. The Agent must NEVER place, trigger, or simulate a LIVE trade.
2. The Agent must NEVER bypass the ExecutionGate.
3. The Agent must NEVER modify or suggest modifying:
   - EXECUTION_ENABLED
   - EXECUTION_MODE
4. The Agent must NEVER assume execution readiness.
5. The Agent must NEVER fabricate:
   - Prices
   - LTPs
   - Ticks
   - Candle closes
   - Broker responses
6. If required data is missing or stale, the Agent must fail closed.
7. OpenAlgo is the single source of market truth.
8. Redis real-time LTP is authoritative ONLY if freshness < 5s.
9. If data freshness is unknown, treat it as STALE.
10. The Agent must never infer market state.
11. If feed health is not explicitly HEALTHY, assume UNSAFE.
12. Historical data must never be mixed with real-time data silently.
13. The Agent may generate TradeDecisions, not TradeExecutions.
14. Every TradeDecision must include:
    - decision_id
    - strategy_name
    - symbol
    - signal (BUY/SELL/HOLD)
    - confidence score
    - decision_time
    - validity window
15. The Agent must clearly separate:
    - Analysis
    - Signal
    - Execution Readiness
16. The Agent must never merge multiple symbols into one decision.
17. The Agent must never output ambiguous or implicit signals.
18. The Agent must follow the project phases strictly.
19. The Agent must NOT introduce ML before:
    - Strategy Manager is complete
    - Backtest Engine 2.0 is validated
20. The Agent must NOT introduce automation without:
    - Alerting
    - Observability
    - Kill switches
21. The Agent must NOT skip validation or testing steps.
22. All code suggestions must be deterministic.
23. No hidden state or magic behavior.
24. No duplication of execution logic.
25. Shared logic must be reused across live and backtest.
26. Configuration must be explicit and version-controlled.
27. Time handling must be timezone-aware (IST).
28. Every critical component must have tests.
29. Failure scenarios must be explicitly tested.
30. Mock OpenAlgo for tests.
31. No feature is “done” without validation criteria.
32. Tests must verify block reasons explicitly.
33. Every decision must be traceable.
34. Every execution attempt must be logged.
35. Every block must include a reason.
36. Agent assumptions must be explicitly stated.
37. Silent failures are not allowed.
38. UI must reflect backend truth, not inferred state.
39. UI must display execution block reasons.
40. UI must show feed health clearly.
41. UI must never show stale prices as live.
42. The Agent must never self-authorize autonomy.
43. The Agent must never remove human override paths.
44. The Agent must not schedule itself to trade.
45. Any future autonomy must be opt-in and reversible.
