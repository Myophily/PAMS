# Personal Asset Manager (PAM)

> A local-first financial dashboard application - a professional Asset Management System (PMS) beyond a simple household ledger

PAM is a reality-mirroring financial tracking system that reconstructs your complete financial state from transaction logs, enabling "time travel" to see how past transactions affect current asset valuation across multiple account types.

## Key Features

### Local-First Architecture
- **Complete data ownership** - All data stored locally in SQLite
- **No cloud dependencies** - Runs entirely on your machine
- **Privacy-focused** - Your financial data never leaves your computer

### Multi-Account Support
- **Deposit/Withdrawal accounts (입출금통장)** - Daily spending and cash management
- **Securities accounts (증권계좌)** - Stocks, ETFs, gold, and other securities
- **Foreign Currency accounts (외화통장)** - Multi-currency holdings with exchange tracking
- **Money Market accounts (MMF)** - Money market funds with interest tracking
- **Savings accounts** - Interest-earning accounts in any currency

### Reality-Mirroring Transaction System
Four core transaction patterns that model real-world financial activities:

1. **Income/Expense** - Salary, dividends, expenses (total assets change)
2. **Transfer** - Move money between accounts (total assets unchanged)
3. **Buy/Sell** - Convert cash to securities and vice versa
4. **Exchange** - Currency conversion with automatic rate tracking

### Advanced Features
- **Time-travel recalculation** - Add past transactions and automatically recalculate all holdings from that date forward
- **Hourly asset snapshots** - Automated tracking of total portfolio value over time
- **Recurring transfers** - Schedule automated transfers (salary, rent, bills)
- **Market data integration** - Real-time price tracking for securities and currencies
- **Comprehensive analytics** - Volatility graphs, allocation charts, P/L tracking

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Embedded database
- **APScheduler** - Background job scheduling
- **Pydantic** - Data validation and serialization

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **React Query** - Data fetching and state management
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Data visualization
- **Lucide React** - Icon library

## Project Structure

```
PAM/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic layer
│   │   ├── routers/         # API endpoint definitions
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # Backend test suite
│   ├── scripts/             # Database utilities and migrations
│   └── asset_data.db        # SQLite database file
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # Reusable React components
│   ├── lib/
│   │   ├── hooks/           # React Query custom hooks
│   │   └── types.ts         # TypeScript type definitions
│   └── public/              # Static assets
└── docs/                    # Project documentation
```

## Quick Start

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Git** for cloning the repository

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PAM
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Configure environment variables**

   Backend (create `backend/.env`):
   ```env
   CORS_ORIGINS=http://localhost:3000
   ```

   Frontend (create `frontend/.env.local`):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:3000/api
   ```

### Running the Application

Open **two terminal windows**:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the application:**
- Frontend: [http://localhost:3000](http://localhost:3000)
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

## Documentation

Comprehensive documentation is available in the repository:

### Essential Reading
- **[CONTEXT.md](CONTEXT.md)** - Project philosophy, core concepts, and architecture
- **[RULES.md](RULES.md)** - Development constraints and transaction patterns
- **[TODO.md](TODO.md)** - Current development priorities and roadmap

### Technical Documentation
- **[API_SPEC.md](API_SPEC.md)** - Complete API endpoint documentation
- **[DATABASE.md](DATABASE.md)** - Database schema and relationships
- **[TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md)** - Detailed transaction logic
- **[FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md)** - UI component specifications
- **[SETUP.md](SETUP.md)** - Detailed setup instructions and troubleshooting

### For Developers
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines and AI assistant instructions

## Architecture Highlights

### Log-Based State Architecture

```
Transaction Logs (Source of Truth)
         ↓
   Calculation Engine
         ↓
  Current State (Holdings)
         ↓
     Dashboard UI
```

**Key principle:** The `Holding` table (current balances) is a **computed view** derived from `Transaction` history. Transactions are immutable. If you add a transaction from 6 months ago, the system recalculates everything from that point forward.

### Data Integrity Rules

1. **Holdings are computed, never manual** - Always derived from transaction history
2. **Transactions are immutable** - Use soft delete, never hard delete
3. **Linked transactions are bidirectional** - References must be mutual
4. **Past transactions trigger recalculation** - Holdings and snapshots updated automatically
5. **Use Decimal for money** - Never use float for monetary calculations

### Background Services

APScheduler runs automated tasks:
- **Hourly snapshots** - Capture total asset value every hour
- **Recurring transfers** - Execute scheduled transfers automatically
- **Gap detection** - Backfill missing snapshots on startup

## Development Workflow

### Running Tests

**Backend:**
```bash
cd backend
pytest                              # Run all tests
pytest --cov=app                    # With coverage
pytest --cov=app --cov-report=html  # HTML coverage report
```

**Frontend:**
```bash
cd frontend
npm run lint    # ESLint
npm run build   # Type-check and build
```

### Database Management

**Inspect database:**
```bash
# Interactive API docs (recommended)
open http://localhost:8000/docs

# SQLite Browser (download from sqlitebrowser.org)
# Open: backend/asset_data.db
```

**Reset database:**
```bash
cd backend
python scripts/reset_database.py  # Creates backup before reset
```

### Adding New Features

1. **Read documentation first** - [RULES.md](RULES.md) and [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md)
2. **Backend:** Router → Service → Model (separation of concerns)
3. **Frontend:** Hook → Component
4. **Types:** Mirror Pydantic schemas in TypeScript
5. **Test:** Verify transaction patterns and calculations

## Contributing

When contributing to this project:

1. Follow the transaction patterns defined in [RULES.md](RULES.md)
2. Maintain type safety (Pydantic for backend, TypeScript for frontend)
3. Write tests for business logic
4. Use conventional commits format:
   ```
   feat: add exchange transaction type
   fix: correct average price calculation
   docs: update API documentation
   test: add unit tests for transfer logic
   ```

## Core Philosophy

**Data integrity > Feature completeness**

- Reality mirroring: Record what actually happened, not what you wish happened
- Log-based truth: Transactions are immutable, holdings are computed
- Time-travel: Support inserting past transactions with automatic recalculation
- Type safety: Use Decimal for money, datetime.date for dates
- Separation of concerns: Business logic in services, not routers

## License

This project is for personal use. No license specified yet.

## Acknowledgments

Built with modern web technologies for local-first financial management.

---

**Made for those who want complete control over their financial data.**
