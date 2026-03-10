# MeshMind v2 Web App

React + TypeScript admin UI for MeshMind v2.

## Run against local services

1. **Start infrastructure:**
   ```bash
   docker compose -f infrastructure/docker-compose.yml up -d postgres redis qdrant
   ```

2. **Start control-api:**
   ```bash
   cd apps/control-api
   DATABASE_URL=postgres://meshmind:meshmind@localhost:5432/meshmind \
   JWT_SECRET=dev-secret \
   MESHMIND_SEED_DEV_ADMIN=true \
   cargo run
   ```

3. **Start query-api** (for Search and Ask):
   ```bash
   cd apps/query-api
   pip install -e .
   DATABASE_URL=postgres://meshmind:meshmind@localhost:5432/meshmind \
   QDRANT_URL=http://localhost:6333 \
   QUERY_API_PORT=3001 \
   python -m meshmind_query_api.main
   ```
   And set `QUERY_API_URL=http://localhost:3001` when running control-api.

4. **Run the web app:**
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
   Open http://localhost:5173. Vite proxies `/api` to control-api (port 3000).

5. **Login:** Use `admin` / `admin` if `MESHMIND_SEED_DEV_ADMIN=true`.

## Scripts

- `npm run dev` — dev server
- `npm run build` — production build
- `npm run test` — unit tests (Vitest)
- `npm run test:e2e` — Playwright e2e tests
- `npm run test:e2e:ui` — Playwright UI mode
