# Frontend Component Architecture

Structure:
- `components/`: Reusable UI elements (charts, tables, badges, modals)
- `pages/`: Dashboard views (Overview, Audit Browser, Policy Config, Linkage Graph)
- `services/`: API client adapters (Axios/fetch callers for `/api/v1/...`)
- `hooks/`: Custom React hooks for data fetching and state
- `types/`: TypeScript interface definitions
- `utils/`: Formatting and helper utilities
