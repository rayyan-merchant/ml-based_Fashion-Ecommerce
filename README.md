# Fashion E-Commerce Intelligence System

An integrated ML-DB project for a fashion storefront and admin intelligence dashboard. The app combines customer shopping flows, admin commerce operations, and ML-backed insights for recommendations, sentiment analysis, forecasting, segmentation, and funnel analytics.

## Current Stack

- Frontend: React 18, CRA, JavaScript, React Router, Tailwind CSS, Axios, Recharts/Chart.js
- Backend: FastAPI, PostgreSQL, JWT authentication
- ML: hybrid recommender, review similarity, sentiment, forecasting, segmentation, analytics endpoints
- Database: PostgreSQL schema under `niche_data`

The frontend prompt describes the target Vite + TypeScript + Zustand + TanStack Query architecture. This repo currently preserves the working CRA frontend while adding compatible service contracts under `frontend/src/services/` so a future Vite/TypeScript migration can happen incrementally.

## Quick Start

1. Copy env files:

   ```powershell
   Copy-Item .env.example .env
   Copy-Item frontend\.env.example frontend\.env
   ```

2. Start the backend:

   ```powershell
   cd backend
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. Start the frontend:

   ```powershell
   cd frontend
   npm.cmd start
   ```

4. Open `http://127.0.0.1:3000`.

## Mock vs Real API

By default the frontend calls the real FastAPI backend:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_USE_MOCK_API=false
```

Set `REACT_APP_USE_MOCK_API=true` to use realistic fixtures from `frontend/src/api/mockData.js`. The mock layer includes 60 products, 24 customers, 36 orders, paginated reviews, segments, forecasts, analytics, wordcloud placeholders, and recommendation-ready product fields.

The service layer also reads `VITE_API_BASE_URL` and `VITE_USE_MOCK_API` so the same contracts survive a future Vite migration.

## Important Frontend Paths

- Storefront: `/`, `/products`, `/collections/:category`, `/sale`, `/new-arrivals`, `/trending`, `/lookbook`, `/brands`
- Product detail: `/products/:id`
- Customer flows: `/login`, `/register`, `/cart`, `/wishlist`, `/checkout`, `/orders`, `/profile`, `/account/*`
- Admin: `/admin/login`, `/admin`, `/admin/products`, `/admin/orders`, `/admin/customers`, `/admin/reviews`, `/admin/intelligence/*`, `/admin/settings`

## Project Structure

- `frontend/src/api/`: backend-specific Axios clients and mock fixtures
- `frontend/src/services/`: prompt-aligned service contracts for products, orders, customers, reviews, recommendations, ML, auth, cart, and admin
- `frontend/src/pages/`: customer and admin pages
- `frontend/src/components/`: reusable UI, product, chart, ML, and admin widgets
- `backend/app/routers/`: FastAPI route modules for commerce, auth, ML, and analytics
- `database/`: SQL schema, procedures, and DB setup assets
- `ml/`: model training and artifact workspace

## Verification

Useful checks:

```powershell
cd backend
python -m compileall app

cd ..\frontend
npm.cmd run build
```

The latest integration pass verified real backend auth, cart, wishlist, checkout, admin CRUD, review paging/similarity, recommendations, sentiment, forecasting, segmentation, and analytics endpoints.
