# SaaS Migration Completion & Optimization Plan

This plan outlines the final steps (Phase 4) for migrating the Fortune Trading platform to a modern SaaS architecture (FastAPI + Next.js).

## User Review Required

> [!IMPORTANT]
> The `frontend/` directory will be replaced by `frontend-new/`. The legacy Streamlit files will remain in `legacy/` or be deleted if no longer needed.
> Docker configuration will be updated to point to the new frontend and optimize for production.

## Proposed Changes

### 1. Backend Verification & Testing
Create a basic test suite for the FastAPI backend to ensure all Phase 1-3 endpoints are functional.

#### [NEW] [test_api.py](file:///home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/backend/tests/test_api.py)
*   Add unit tests for `/market`, `/derivatives`, `/insider`, and `/technicals` endpoints.
*   Verify data normalization and error handling.

---

### 2. Infrastructure & Docker Optimization
Upgrade the deployment configuration to support the Next.js frontend and improve build times.

#### [MODIFY] [docker-compose.yml](file:///home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/docker-compose.yml)
*   Update `frontend` service to build from `./frontend-new`.
*   Fix port mappings if necessary (Next.js usually runs on 3000).

#### [NEW] [Dockerfile](file:///home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/frontend-new/Dockerfile)
*   Implement a multi-stage build:
    *   **Stage 1**: Build (Install dependencies, `next build`).
    *   **Stage 2**: Runner (Copy only necessary files, use `node:18-alpine`).

---

### 3. Service Level Optimizations
Address pending TODOs and improve data availability in the Recommendation Engine.

#### [MODIFY] [db_manager.py](file:///home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/backend/app/database/db_manager.py)
*   Implement `get_latest_option_chain(symbol)` helper to support derivatives scoring.

#### [MODIFY] [recommendation_service.py](file:///home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/backend/app/services/recommendation_service.py)
*   Wire up `_calculate_derivatives_score` to use the new `db_manager` helper.
*   Enable derivatives sentiment in the final Smart Score.

#### [MODIFY] [nse_derivatives.py](file:///home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/backend/app/data_sources/nse_derivatives.py)
*   Replace placeholder `get_option_chain` with a call to `NseUtils` or provide a fallback.

---

### 4. Integration & Polish
#### [MODIFY] [app/stock/[symbol]/page.tsx](file:///home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/frontend-new/src/app/stock/[symbol]/page.tsx)
*   Ensure all tabs (Overview, Technical, Derivatives, Insider) are fetching data from the correct backend endpoints.

## Verification Plan

### Automated Tests
*   Run FastAPI tests: `pytest backend/tests`
*   Verify frontend build: `cd frontend-new && npm run build`

### Manual Verification
*   Launch system: `docker-compose up --build`
*   Verify Dashboard Widgets (Market Pulse, Gainers/Losers).
*   Verify Stock Analysis page:
    *   [ ] Intraday Chart loading.
    *   [ ] Option Chain heatmap display.
    *   [ ] Insider Trading table data.
