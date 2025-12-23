# Development Rules and Conventions

To maintain high architectural standards, all developers must adhere to the following rules.

## 1. No Hallucinations
As an AI-first project, absolute precision in code and API usage is mandatory.
- **Rule**: Never assume an API field exists. Verify the Pydantic schema in the backend or the TypeScript interface in the frontend.
- **Rule**: Use the `view_file` tool to inspect signatures before writing integration code.

## 2. Step-by-Step Execution
Avoid "all-at-once" implementation. Follow this loop:
1. **Research**: Confirm signatures and data availability.
2. **Plan**: Write an implementation plan.
3. **Draft**: Create the code.
4. **Verify**: Run tests and check the UI.

## 3. Directory Structure Enforcement

- `backend/app/api/v1/endpoints/`: Routing entry points.
- `backend/app/services/`: Core logic and domain services.
- `frontend-new/src/app/`: Next.js pages and layouts.
- `frontend-new/src/components/`: Reusable UI components.
- `frontend-new/src/hooks/`: Data fetching and state management hooks.

## 4. Coding Conventions

### Backend (Python/FastAPI)
- **Typing**: Use Type Hints for all function arguments and return types.
- **Validation**: Use Pydantic models for all Request/Response bodies.
- **Error Handling**: Raise `HTTPException` with clear status codes and details.

### Frontend (TypeScript/React)
- **Strict Typing**: No `any`. Use interfaces for all API payloads.
- **Querying**: Use `@tanstack/react-query` for all data fetching.
- **Async/Await**: Preferred over `.then()`.

## 5. Deployment & Configuration
- **CORS**: Always ensure `BACKEND_CORS_ORIGINS` in `.env` includes the frontend URL.
- **Environment**: Use `.env` for secrets; never hardcode API keys or DB URLs.
