# SETUP.md - Personal Asset Management System

Step-by-step setup instructions for local development.

---

## Prerequisites

**Required Software:**
- **Python:** 3.10 or higher ([Download](https://www.python.org/downloads/))
- **Node.js:** 18 or higher ([Download](https://nodejs.org/))
- **Git:** For version control ([Download](https://git-scm.com/))

**Optional:**
- **SQLite Browser:** To inspect database ([Download](https://sqlitebrowser.org/))
- **VS Code:** Recommended IDE ([Download](https://code.visualstudio.com/))

---

## Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone <repository-url>
cd PAMS

# 2. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Initialize database
python -c "from app.database import init_db; init_db()"

# 4. Start backend (Terminal 1)
uvicorn app.main:app --reload --port 8000

# 5. Frontend setup (in new terminal)
cd ../frontend
npm install

# 6. Start frontend (Terminal 2)
npm run dev

# 7. Open browser
# Navigate to http://localhost:3000
```

---

## Detailed Setup Instructions

### 1. Backend Setup (Python/FastAPI)

#### Step 1.1: Create Virtual Environment

```bash
cd backend
python3 -m venv venv
```

**Why virtual environment?**
- Isolates project dependencies
- Prevents conflicts with system Python packages
- Makes deployment reproducible

#### Step 1.2: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Verification:** Your terminal prompt should now start with `(venv)`

#### Step 1.3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected packages:**
```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
requests>=2.31.0
```

**Verify installation:**
```bash
pip list
```

#### Step 1.4: Create Environment Variables

Create `.env` file in `backend/` directory:

```bash
# backend/.env
DATABASE_URL=sqlite:///./asset_data.db
API_KEY_YAHOO_FINANCE=your_api_key_here  # Optional
API_KEY_ALPHA_VANTAGE=your_api_key_here  # Optional
CORS_ORIGINS=http://localhost:3000
```

**Note:** API keys are optional. The app can function with manual price entry.

#### Step 1.5: Initialize Database

```bash
# Run database initialization script
python -c "from app.database import init_db; init_db()"
```

**This creates:**
- `asset_data.db` file in backend directory
- All required tables (Account, Transaction, Holding, MarketData, AssetSnapshot)
- Indexes for performance

**Verify database creation:**
```bash
ls -l asset_data.db  # Should show file size > 0
```

#### Step 1.6: Start Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify backend is running:**
- Open browser to `http://localhost:8000/docs`
- You should see FastAPI auto-generated documentation (Swagger UI)

---

### 2. Frontend Setup (Next.js/React)

#### Step 2.1: Install Node Dependencies

```bash
cd frontend
npm install
```

**Expected packages:**
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "@tanstack/react-query": "^5.0.0",
    "recharts": "^2.10.0",
    "tailwindcss": "^3.4.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.0.0",
    "@types/node": "^20.0.0"
  }
}
```

**Verify installation:**
```bash
npm list --depth=0
```

#### Step 2.2: Configure Next.js Rewrites

**File: `frontend/next.config.ts`**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
```

**What this does:**
- All requests to `/api/*` are proxied to FastAPI backend
- Eliminates CORS issues
- Frontend can call `/api/accounts` instead of `http://localhost:8000/api/accounts`

#### Step 2.3: Create Environment Variables

**File: `frontend/.env.local`**
```bash
NEXT_PUBLIC_API_URL=/api
```

#### Step 2.4: Start Frontend Development Server

```bash
npm run dev
```

**Expected output:**
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully in 2.1s (123 modules)
- wait compiling...
- event compiled successfully in 345 ms (234 modules)
```

**Verify frontend is running:**
- Open browser to `http://localhost:3000`
- You should see the PAM dashboard (may be empty initially)

---

### 3. Running Both Servers

**You need TWO terminal windows running simultaneously:**

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

**Access the application:**
- **Frontend (UI):** `http://localhost:3000`
- **Backend API Docs:** `http://localhost:8000/docs`

---

## Project Structure Overview

```
PAM/
├── backend/
│   ├── venv/                    # Python virtual environment (gitignored)
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # Database models
│   │   │   ├── __init__.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── holding.py
│   │   │   └── market_data.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── account_schema.py
│   │   │   └── transaction_schema.py
│   │   ├── routers/             # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── accounts.py
│   │   │   ├── transactions.py
│   │   │   └── dashboard.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── transaction_service.py
│   │   │   ├── calculation_service.py
│   │   │   └── market_data_service.py
│   │   └── utils/               # Helper functions
│   │       └── validators.py
│   ├── .env                     # Environment variables (gitignored)
│   ├── requirements.txt         # Python dependencies
│   └── asset_data.db            # SQLite database (gitignored)
│
├── frontend/
│   ├── node_modules/            # Node dependencies (gitignored)
│   ├── app/
│   │   ├── page.tsx             # Dashboard home page
│   │   ├── layout.tsx           # Root layout
│   │   ├── accounts/
│   │   │   ├── page.tsx         # Account list
│   │   │   └── [id]/page.tsx    # Account detail
│   │   └── api/                 # API route handlers (optional)
│   ├── components/              # React components
│   │   ├── TotalAssetCard.tsx
│   │   ├── AccountCard.tsx
│   │   ├── TransactionModal.tsx
│   │   └── charts/
│   │       ├── AssetAllocationChart.tsx
│   │       └── AssetVolatilityChart.tsx
│   ├── lib/
│   │   ├── hooks/               # React Query hooks
│   │   │   ├── useAccounts.ts
│   │   │   ├── useTransactions.ts
│   │   │   └── useDashboard.ts
│   │   └── types.ts             # TypeScript types
│   ├── public/                  # Static assets
│   ├── .env.local               # Frontend env vars (gitignored)
│   ├── next.config.ts           # Next.js configuration
│   ├── package.json             # Node dependencies
│   ├── tailwind.config.js       # Tailwind CSS config
│   └── tsconfig.json            # TypeScript config
│
├── CLAUDE.md                    # AI assistant instructions
├── CONTEXT.md                   # Project overview
├── RULES.md                     # Development rules
├── TODO.md                      # Development roadmap
├── API_SPEC.md                  # API documentation
├── DATABASE.md                  # Database schema
├── TRANSACTION_PATTERNS.md      # Transaction logic
├── SETUP.md                     # This file
├── .gitignore                   # Git ignore rules
└── README.md                    # User-facing readme
```

---

## Database Setup Details

### Initial Schema Creation

**File: `backend/app/database.py`**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./asset_data.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=True  # Log SQL queries (set to False in production)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database schema."""
    # Import all models
    from app.models import account, transaction, holding, market_data, asset_snapshot

    # Create tables
    Base.metadata.create_all(bind=engine)

    print("Database initialized successfully!")
```

**Run initialization:**
```bash
python -c "from app.database import init_db; init_db()"
```

### Seed Data (Optional)

Create sample data for testing:

**File: `backend/scripts/seed_data.py`**
```python
from app.database import SessionLocal, init_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.holding import Holding
from datetime import date
from decimal import Decimal

def seed_database():
    """Create sample data for testing."""
    db = SessionLocal()

    try:
        # Create accounts
        checking = Account(
            name="Toss Checking",
            type="Deposit",
            currency="KRW"
        )
        brokerage = Account(
            name="Kiwoom Brokerage",
            type="Securities",
            currency="KRW"
        )
        db.add_all([checking, brokerage])
        db.flush()

        # Initial deposit
        tx_deposit = Transaction(
            account_id=checking.id,
            type="Deposit",
            amount=Decimal("5000000.00"),
            date=date(2024, 1, 1),
            description="Initial balance"
        )
        db.add(tx_deposit)

        # Create CASH holding
        cash_holding = Holding(
            account_id=checking.id,
            ticker="CASH",
            quantity=Decimal("5000000.00"),
            avg_price=Decimal("1.0")
        )
        db.add(cash_holding)

        db.commit()
        print("Sample data created successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed_database()
```

**Run seed script:**
```bash
python backend/scripts/seed_data.py
```

---

## Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`
**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Problem:** `sqlalchemy.exc.OperationalError: unable to open database file`
**Solution:**
```bash
# Check file permissions
chmod 644 asset_data.db

# Or reinitialize database
rm asset_data.db
python -c "from app.database import init_db; init_db()"
```

**Problem:** `Address already in use: 127.0.0.1:8000`
**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process (replace PID with actual process ID)
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Frontend Issues

**Problem:** `Error: Cannot find module 'next'`
**Solution:**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem:** `API calls return 404 or CORS errors`
**Solution:**
1. Verify backend is running on port 8000
2. Check `next.config.ts` has correct rewrites
3. Restart Next.js dev server after config changes

**Problem:** `Module not found: Can't resolve '@/components/...'`
**Solution:**
Check `tsconfig.json` has path aliases:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### Database Issues

**Problem:** Database locked errors
**Solution:**
```bash
# Enable WAL mode
sqlite3 asset_data.db "PRAGMA journal_mode=WAL;"

# Or close all connections and retry
```

**Problem:** Corrupted database
**Solution:**
```bash
# Check integrity
sqlite3 asset_data.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
cp asset_data_backup.db asset_data.db
```

---

## Development Workflow

### Daily Development Cycle

1. **Start both servers:**
   ```bash
   # Terminal 1
   cd backend && source venv/bin/activate && uvicorn app.main:app --reload

   # Terminal 2
   cd frontend && npm run dev
   ```

2. **Make changes:**
   - Backend changes auto-reload (FastAPI `--reload`)
   - Frontend changes hot-reload (Next.js HMR)

3. **Test changes:**
   - Frontend: Check browser at `http://localhost:3000`
   - Backend API: Check Swagger docs at `http://localhost:8000/docs`

4. **Inspect database:**
   ```bash
   sqlite3 asset_data.db
   .tables  # List all tables
   SELECT * FROM account;  # Query data
   .quit
   ```

### Adding New Features

**Example: Adding a new API endpoint**

1. **Define Pydantic schema (backend/app/schemas/example_schema.py):**
   ```python
   from pydantic import BaseModel
   from datetime import date

   class ExampleRequest(BaseModel):
       name: str
       value: int

   class ExampleResponse(BaseModel):
       id: int
       name: str
       value: int
       created_at: date
   ```

2. **Create API endpoint (backend/app/routers/example.py):**
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from app.database import get_db
   from app.schemas.example_schema import ExampleRequest, ExampleResponse

   router = APIRouter(prefix="/api/example", tags=["example"])

   @router.post("/", response_model=ExampleResponse)
   def create_example(request: ExampleRequest, db: Session = Depends(get_db)):
       # Business logic here
       return {"id": 1, "name": request.name, "value": request.value}
   ```

3. **Register router (backend/app/main.py):**
   ```python
   from app.routers import example

   app.include_router(example.router)
   ```

4. **Create React Query hook (frontend/lib/hooks/useExample.ts):**
   ```typescript
   import { useQuery, useMutation } from '@tanstack/react-query';

   export function useExample() {
     return useQuery({
       queryKey: ['example'],
       queryFn: async () => {
         const res = await fetch('/api/example');
         return res.json();
       }
     });
   }
   ```

5. **Use in component (frontend/components/ExampleComponent.tsx):**
   ```typescript
   import { useExample } from '@/lib/hooks/useExample';

   export default function ExampleComponent() {
     const { data, isLoading } = useExample();

     if (isLoading) return <div>Loading...</div>;

     return <div>{JSON.stringify(data)}</div>;
   }
   ```

---

## Production Deployment

**Note:** This app is designed for local use, not production deployment.

However, if you want to run it on a server:

### Backend Deployment

```bash
# Use gunicorn instead of uvicorn for production
pip install gunicorn

gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Docker (Optional)

**Dockerfile (backend):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile (frontend):**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

CMD ["npm", "start"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/asset_data.db:/app/asset_data.db
    environment:
      - DATABASE_URL=sqlite:///./asset_data.db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - NEXT_PUBLIC_API_URL=/api
```

**Run with Docker:**
```bash
docker-compose up -d
```

---

## Backup & Restore

### Manual Backup

```bash
# Backup database
cp backend/asset_data.db backups/asset_data_$(date +%Y%m%d).db

# Or compress
tar -czf backups/asset_data_$(date +%Y%m%d).tar.gz backend/asset_data.db
```

### Automated Backup (cron job)

**Create backup script (`backup.sh`):**
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

cp backend/asset_data.db "$BACKUP_DIR/asset_data_$DATE.db"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "asset_data_*.db" -mtime +7 -delete
```

**Add to crontab:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/PAM/backup.sh
```

### Cloud Sync

**Using Dropbox:**
```bash
# Move database to Dropbox
mv backend/asset_data.db ~/Dropbox/PAM/asset_data.db

# Create symlink
ln -s ~/Dropbox/PAM/asset_data.db backend/asset_data.db
```

**Using Google Drive (with rclone):**
```bash
# Install rclone
brew install rclone  # Mac
# or apt-get install rclone  # Linux

# Configure Google Drive
rclone config

# Sync database
rclone copy backend/asset_data.db gdrive:PAM/
```

---

## Next Steps

After setup is complete:

1. ✅ Verify both servers are running
2. ✅ Create your first account (Dashboard → Add Account)
3. ✅ Record your first transaction (Deposit, Transfer, etc.)
4. ✅ Check account details and transaction history
5. ✅ Explore dashboard charts and visualizations

**Read next:**
- [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md) - Understand the 4 core patterns
- [API_SPEC.md](API_SPEC.md) - Full API reference
- [DATABASE.md](DATABASE.md) - Database schema details

**Need help?**
- Check [Troubleshooting](#troubleshooting) section above
- Review TODO.md for development roadmap
- Inspect backend API docs at `http://localhost:8000/docs`
