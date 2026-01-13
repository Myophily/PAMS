# PAMS Backend (FastAPI)

Backend API for the Personal Asset Management System application.

## Setup

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # OR: venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize database:
   ```bash
   python -c "from app.database import init_db; init_db()"
   ```

4. Start server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Access API docs:
   ```
   http://localhost:8000/docs
   ```

## Project Structure

- `app/main.py` - FastAPI application entry point
- `app/database.py` - SQLAlchemy configuration
- `app/models/` - Database models (5 tables)
  - `account.py` - Financial accounts
  - `holding.py` - Current asset positions
  - `transaction.py` - Immutable transaction log
  - `market_data.py` - Cached price/rate data
  - `asset_snapshot.py` - Daily asset totals
- `app/schemas/` - Pydantic request/response schemas
- `app/routers/` - API endpoint definitions
- `app/services/` - Business logic (Phase 2+)
- `app/utils/` - Helper functions

## Database

- **Engine:** SQLite (asset_data.db)
- **ORM:** SQLAlchemy 2.0+
- **Foreign Keys:** Enabled
- **Journal Mode:** WAL (Write-Ahead Logging)

## API Endpoints (Phase 1)

- `GET /api/health` - Health check and database status
- `GET /api/accounts/` - List all accounts (placeholder)
- `GET /api/transactions/` - List all transactions (placeholder)

Full CRUD operations will be implemented in Phase 2.

## Environment Variables (.env)

```bash
DATABASE_URL=sqlite:///./asset_data.db
CORS_ORIGINS=http://localhost:3000
```

## Important Notes

- All monetary values use `Decimal` type (NEVER float)
- Transaction dates use `Date` type (YYYY-MM-DD)
- Holdings are ALWAYS computed from Transaction history
- Transactions are immutable (soft delete only)
