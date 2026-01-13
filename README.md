<div align="center">

# 💰 Personal Asset Management System (PAMS)

### _Your Financial Life, Perfectly Reconstructed_

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-Personal_Use-red.svg)](LICENSE)

**A professional-grade Asset Management System designed for complete financial autonomy**

[Features](#-key-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture-highlights)

---

</div>

## 🎯 What is PAMS?

PAMS is a **local-first financial dashboard** that goes far beyond simple expense tracking. It's a professional Asset Management System (PMS) that reconstructs your complete financial state from transaction logs, enabling powerful "time travel" capabilities to see how past transactions affect current asset valuation.

### 🌟 The Core Philosophy

**Reality Mirroring** → Record what actually happened, not what you wish happened
**Log-Based Truth** → Transactions are immutable, holdings are computed
**Time Travel** → Insert past transactions and automatically recalculate everything forward
**Complete Privacy** → Your data never leaves your computer

Think of it as Git for your finances - every transaction is a commit, and you can reconstruct any point in your financial history.

## ✨ Key Features

### 🔒 Local-First Architecture

<table>
<tr>
<td width="33%" align="center">
<h4>🏠 Complete Data Ownership</h4>
All data stored locally in SQLite<br/>
<em>Your data, your computer, your control</em>
</td>
<td width="33%" align="center">
<h4>☁️ No Cloud Dependencies</h4>
Runs entirely on your machine<br/>
<em>No subscriptions, no internet required</em>
</td>
<td width="33%" align="center">
<h4>🔐 Privacy-Focused</h4>
Financial data never leaves your computer<br/>
<em>Zero external data transmission</em>
</td>
</tr>
</table>

### 🏦 Multi-Account Support

PAMS supports all major account types used in modern financial management:

| Account Type           | Symbol | Use Case                   | Key Features                                           |
| ---------------------- | ------ | -------------------------- | ------------------------------------------------------ |
| **Deposit/Withdrawal** | 💳     | Daily spending & cash      | Transaction tracking, balance monitoring               |
| **Securities**         | 📈     | Stocks, ETFs, bonds        | Buy/sell tracking, P/L calculation, dividend recording |
| **Foreign Currency**   | 💱     | Multi-currency holdings    | Exchange rate tracking, currency conversion            |
| **Money Market (MMF)** | 💵     | Short-term cash management | Interest tracking, high liquidity                      |
| **Savings**            | 🏦     | Interest-earning deposits  | Any currency, interest calculation                     |

### 🔄 Reality-Mirroring Transaction System

Four core transaction patterns that model **real-world financial activities**:

<table>
<tr>
<td width="25%" align="center">
<h3>1️⃣ Income/Expense</h3>
<p><strong>Salary • Dividends • Expenses</strong></p>
<p>💡 Total assets <strong>CHANGE</strong></p>
<p><em>Money enters or leaves your financial universe</em></p>
</td>
<td width="25%" align="center">
<h3>2️⃣ Transfer</h3>
<p><strong>Move Between Accounts</strong></p>
<p>💡 Total assets <strong>UNCHANGED</strong></p>
<p><em>Money moves, but stays in your universe</em></p>
</td>
<td width="25%" align="center">
<h3>3️⃣ Buy/Sell</h3>
<p><strong>Cash ↔ Securities</strong></p>
<p>💡 Total assets <strong>UNCHANGED*</strong></p>
<p><em>Convert between cash and investments</em></p>
</td>
<td width="25%" align="center">
<h3>4️⃣ Exchange</h3>
<p><strong>Currency Conversion</strong></p>
<p>💡 Total assets <strong>UNCHANGED*</strong></p>
<p><em>Convert between currencies</em></p>
</td>
</tr>
</table>

<sub>\*Unchanged at transaction time; value changes later due to market movements</sub>

### 🚀 Advanced Capabilities

<details>
<summary><b>⏰ Time-Travel Recalculation</b></summary>
<br/>
Add a transaction from 6 months ago, and PAMS automatically recalculates:

- All holdings from that date forward
- Every asset snapshot after that date
- Average purchase prices for securities
- Cumulative profit/loss calculations

**It's like Git rebase for your finances** - the history is rewritten consistently.

</details>

<details>
<summary><b>📊 Hourly Asset Snapshots</b></summary>
<br/>

- Automated capture of total portfolio value every hour
- Historical tracking of asset growth over time
- Visual volatility graphs and trend analysis
- Gap detection and backfill on startup
</details>

<details>
<summary><b>🔁 Recurring Transfers</b></summary>
<br/>

Schedule automated financial flows:

- Monthly salary deposits
- Recurring rent/mortgage payments
- Regular investment contributions
- Subscription payments

Set it once, let PAMS execute automatically at the right time.

</details>

<details>
<summary><b>📈 Market Data Integration</b></summary>
<br/>

- Real-time price tracking for stocks, ETFs, bonds
- Exchange rate updates for multiple currencies
- Automatic calculation of current portfolio value
- Historical price data for analytics
</details>

<details>
<summary><b>📉 Comprehensive Analytics</b></summary>
<br/>

**Portfolio Analytics:**

- Asset allocation pie charts
- Account-level and ticker-level breakdowns
- Currency distribution analysis

**Performance Tracking:**

- Realized and unrealized P/L
- Average purchase price tracking
- ROI calculations per security

**Risk Analysis:**

- Volatility graphs over time
- Drawdown analysis
- Total asset value trends
</details>

## 🛠️ Tech Stack

<div align="center">

### Backend Power 🐍

| Technology      | Purpose        | Why We Chose It                                |
| --------------- | -------------- | ---------------------------------------------- |
| **FastAPI**     | Web Framework  | Async support, automatic API docs, type hints  |
| **SQLAlchemy**  | ORM            | Robust ORM with relationship handling          |
| **SQLite**      | Database       | Zero-config, embedded, perfect for local-first |
| **APScheduler** | Job Scheduling | Hourly snapshots & recurring transfers         |
| **Pydantic**    | Validation     | Type-safe request/response schemas             |

### Frontend Excellence ⚛️

| Technology       | Purpose            | Why We Chose It                           |
| ---------------- | ------------------ | ----------------------------------------- |
| **Next.js 14**   | React Framework    | App Router, server components, API routes |
| **TypeScript**   | Type Safety        | Catch errors at compile time, not runtime |
| **React Query**  | State Management   | Caching, auto-refetch, optimistic updates |
| **Tailwind CSS** | Styling            | Rapid UI development with utility classes |
| **Recharts**     | Data Visualization | Beautiful charts with minimal code        |
| **Lucide React** | Icons              | Consistent, customizable icon library     |

</div>

### 🏗️ Why This Stack?

- **Python + TypeScript**: Type safety across the entire stack
- **FastAPI + Next.js**: Modern, async-first, developer-friendly
- **SQLite**: Zero maintenance database, perfect for local-first apps
- **React Query**: Automatic data synchronization without complex state management
- **No Docker/Nginx**: Simple standalone application, runs anywhere

## 📁 Project Structure

```
PAMS/
├── 🐍 backend/                    # Python FastAPI Application
│   ├── app/
│   │   ├── models/                # 📊 SQLAlchemy database models
│   │   │   ├── account.py         # Account entity (5 types)
│   │   │   ├── transaction.py     # Transaction log (immutable)
│   │   │   ├── holding.py         # Current balances (computed)
│   │   │   ├── market_data.py     # Price/exchange rate cache
│   │   │   └── asset_snapshot.py  # Hourly portfolio snapshots
│   │   ├── schemas/               # 📝 Pydantic request/response schemas
│   │   ├── services/              # 🧠 Business logic layer
│   │   │   ├── transaction_service.py    # Transaction patterns
│   │   │   ├── holding_service.py        # Holding calculations
│   │   │   ├── market_data_service.py    # Price fetching
│   │   │   └── snapshot_service.py       # Asset snapshots
│   │   ├── routers/               # 🛣️ API endpoint definitions
│   │   └── main.py                # 🚀 FastAPI application entry
│   ├── tests/                     # ✅ Backend test suite
│   ├── scripts/                   # 🔧 Database utilities & migrations
│   └── asset_data.db              # 💾 SQLite database file
│
├── ⚛️ frontend/                   # Next.js React Application
│   ├── app/                       # 📄 Next.js App Router pages
│   │   ├── page.tsx               # Dashboard (total assets)
│   │   ├── accounts/              # Account list & details
│   │   ├── ledger/                # Transaction ledger
│   │   └── recurring-transfers/   # Scheduled transfers
│   ├── components/                # 🧩 Reusable React components
│   │   ├── charts/                # Data visualization
│   │   ├── modals/                # Transaction entry forms
│   │   └── ui/                    # Shared UI components
│   ├── lib/
│   │   ├── hooks/                 # 🪝 React Query custom hooks
│   │   └── types.ts               # 📐 TypeScript type definitions
│   └── public/                    # 🖼️ Static assets
│
└── 📚 docs/                       # Comprehensive documentation
    ├── CONTEXT.md                 # Project philosophy
    ├── RULES.md                   # Development constraints
    ├── TRANSACTION_PATTERNS.md    # Transaction logic guide
    └── ...                        # API specs, database schema
```

## 🚀 Quick Start

### 📋 Prerequisites

Make sure you have these installed:

- 🐍 **Python 3.10+** with pip → [Download](https://www.python.org/downloads/)
- 🟢 **Node.js 18+** with npm → [Download](https://nodejs.org/)
- 📦 **Git** for cloning → [Download](https://git-scm.com/)

### ⚡ Installation

<details open>
<summary><b>Step 1️⃣: Clone the Repository</b></summary>

```bash
git clone https://github.com/Myophily/PAMS.git
cd PAMS
```

</details>

<details open>
<summary><b>Step 2️⃣: Set Up the Backend (Python)</b></summary>

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

**✅ You should see (venv) in your terminal prompt**

</details>

<details open>
<summary><b>Step 3️⃣: Set Up the Frontend (Node.js)</b></summary>

```bash
cd ../frontend

# Install dependencies
npm install
```

**✅ This will install Next.js, React, TypeScript, and all UI libraries**

</details>

<details open>
<summary><b>Step 4️⃣: Configure Environment Variables</b></summary>

**Backend Configuration** (create `backend/.env`):

```env
CORS_ORIGINS=http://localhost:3000
```

**Frontend Configuration** (create `frontend/.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

**✅ These files are in .gitignore for security**

</details>

---

### 🎮 Running the Application

You need **TWO terminal windows** running simultaneously:

#### 🖥️ Terminal 1: Backend Server

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**✅ Success indicators:**

- `INFO: Uvicorn running on http://127.0.0.1:8000`
- `INFO: Application startup complete`
- `INFO: Scheduler started`

#### 🖥️ Terminal 2: Frontend Server

```bash
cd frontend
npm run dev -- --webpack
```

**✅ Success indicators:**

- `✓ Ready in XXXms`
- `○ Local: http://localhost:3000`
- `✓ Compiled successfully`

---

### 🌐 Access Your Application

<table>
<tr>
<td align="center" width="33%">
<h3>🏠 Frontend Dashboard</h3>
<a href="http://localhost:3000">http://localhost:3000</a><br/>
<em>Main user interface</em>
</td>
<td align="center" width="33%">
<h3>📚 API Documentation</h3>
<a href="http://localhost:8000/docs">http://localhost:8000/docs</a><br/>
<em>Interactive Swagger UI</em>
</td>
<td align="center" width="33%">
<h3>💚 Health Check</h3>
<a href="http://localhost:8000/api/health">http://localhost:8000/api/health</a><br/>
<em>Backend status</em>
</td>
</tr>
</table>

> **💡 Pro Tip:** Bookmark the API documentation page - it's an interactive playground for testing endpoints!

## 📚 Documentation

> **Comprehensive guides to understand and extend PAMS**

### 🎓 Essential Reading (Start Here!)

These documents explain the **"why"** behind PAMS:

| Document                        | Purpose                                                   | Read When                          |
| ------------------------------- | --------------------------------------------------------- | ---------------------------------- |
| **[CONTEXT.md](CONTEXT.md)** 📖 | Project philosophy, core concepts, architecture decisions | Before making ANY changes          |
| **[RULES.md](RULES.md)** ⚠️     | Development constraints & the 4 transaction patterns      | Before modifying transaction logic |
| **[TODO.md](TODO.md)** 📝       | Current development priorities and roadmap                | Planning new features              |

### 🔧 Technical Documentation (Implementation Details)

Detailed specs for building and extending features:

| Document                                                  | Purpose                                         | Use For                      |
| --------------------------------------------------------- | ----------------------------------------------- | ---------------------------- |
| **[API_SPEC.md](API_SPEC.md)** 🔌                         | Complete API endpoint reference                 | Creating/modifying endpoints |
| **[DATABASE.md](DATABASE.md)** 🗄️                         | Database schema, relationships, queries         | Understanding data structure |
| **[TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md)** 💸 | Detailed transaction logic & calculations       | Implementing financial flows |
| **[FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md)** 🎨   | UI component specifications & React Query hooks | Building UI features         |
| **[SETUP.md](SETUP.md)** 🛠️                               | Detailed setup & troubleshooting guide          | Installation issues          |

### 👨‍💻 For Developers & AI Assistants

| Document                      | Purpose                                 | Audience                       |
| ----------------------------- | --------------------------------------- | ------------------------------ |
| **[CLAUDE.md](CLAUDE.md)** 🤖 | Development guidelines, coding patterns | AI assistants & new developers |

> **⚡ Quick Tip:** Press `Ctrl+F` in the documentation to search for specific topics!

## 🏗️ Architecture Highlights

### 📊 Log-Based State Architecture

The heart of PAMS is its **event-sourcing inspired** design:

```
┌─────────────────────────────────────┐
│   Transaction Logs (Immutable)      │  ← Source of Truth
│   "What Actually Happened"           │
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│     Calculation Engine               │  ← Business Logic
│  (Time-Travel Recalculation)        │
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│  Current State (Holdings)            │  ← Computed View
│  "What You Own Right Now"            │
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│      Dashboard UI                    │  ← User Interface
│   (Next.js + React Query)           │
└─────────────────────────────────────┘
```

### 🔐 Data Integrity Rules (Non-Negotiable)

These rules ensure financial accuracy is **never** compromised:

| #     | Rule                                        | Why It Matters                              |
| ----- | ------------------------------------------- | ------------------------------------------- |
| **1** | **Holdings are computed, never manual**     | Prevents manual errors, ensures audit trail |
| **2** | **Transactions are immutable**              | Preserves history, enables time-travel      |
| **3** | **Linked transactions are bidirectional**   | Ensures referential integrity               |
| **4** | **Past transactions trigger recalculation** | Maintains consistency across time           |
| **5** | **Use Decimal for money**                   | Avoids floating-point rounding errors       |

> **💡 Key Insight:** The `Holding` table is like a **database view** - it's always derivable from `Transaction` history. If you add a transaction from 6 months ago, PAMS recalculates everything from that point forward.

### ⚙️ Background Services

APScheduler runs inside the FastAPI backend to automate critical tasks:

<table>
<tr>
<td width="33%">
<h4>⏰ Hourly Snapshots</h4>
<ul>
<li>Captures total portfolio value every hour</li>
<li>Creates historical chart data</li>
<li>Tracks asset growth over time</li>
</ul>
</td>
<td width="33%">
<h4>🔁 Recurring Transfers</h4>
<ul>
<li>Executes scheduled transfers automatically</li>
<li>Handles salary deposits, bills</li>
<li>Runs based on day-of-month triggers</li>
</ul>
</td>
<td width="33%">
<h4>🔍 Gap Detection</h4>
<ul>
<li>Detects missing snapshots</li>
<li>Backfills data on startup</li>
<li>Ensures continuous history</li>
</ul>
</td>
</tr>
</table>

**Implementation Details:**

- Job storage: SQLite (same database as app data)
- Executor: Single-threaded (prevents race conditions)
- Lifecycle: Starts with backend, graceful shutdown

## 🧪 Development Workflow

### ✅ Running Tests

**Backend Tests (pytest):**

```bash
cd backend
pytest                              # Run all tests
pytest --cov=app                    # With coverage report
pytest --cov=app --cov-report=html  # HTML coverage report
pytest tests/test_transactions.py   # Run specific test file
pytest -k "test_transfer"           # Run tests matching pattern
```

**Test Coverage:**

- ✅ Unit tests (calculation logic, utilities)
- ✅ Service tests (transaction patterns, business logic)
- ✅ API tests (endpoint behavior, validation)
- ✅ Integration tests (full transaction flows)

**Frontend Checks:**

```bash
cd frontend
npm run lint    # ESLint (code quality)
npm run build   # Type-check and build (catches TypeScript errors)
```

---

### 🗄️ Database Management

<details>
<summary><b>Inspect Database</b></summary>

**Option 1: Interactive API Docs (Recommended)**

```bash
open http://localhost:8000/docs
```

Use FastAPI's Swagger UI to query and inspect data.

**Option 2: SQLite Browser GUI**

1. Download from [sqlitebrowser.org](https://sqlitebrowser.org/)
2. Open `backend/asset_data.db`
3. Browse tables, run queries, inspect schema

**Option 3: Command Line**

```bash
sqlite3 backend/asset_data.db
.tables                    # List all tables
.schema Transaction        # Show table schema
SELECT * FROM Account;     # Query data
```

</details>

<details>
<summary><b>Reset Database (Clean Slate)</b></summary>

```bash
cd backend
python scripts/reset_database.py  # Creates backup before reset
```

**What this does:**

- Creates timestamped backup (`asset_data_backup_YYYYMMDD_HHMMSS.db`)
- Drops all tables
- Recreates schema from models
- Fresh start with empty database
</details>

<details>
<summary><b>Database Migrations</b></summary>

**Automatic Migrations:**
Migrations run automatically on server startup:

- Account type enum updates
- Date to datetime conversions
- Schema changes for recurring transfers
- Snapshot timestamp migrations

**Manual Migration (if needed):**

```bash
cd backend/scripts
python run_migration_003.py  # Run specific migration
```

</details>

---

### 🚀 Adding New Features

Follow this systematic approach:

<table>
<tr>
<td width="20%" align="center"><b>Step 1</b><br/>📖<br/>Read Docs</td>
<td width="20%" align="center"><b>Step 2</b><br/>🐍<br/>Backend Code</td>
<td width="20%" align="center"><b>Step 3</b><br/>⚛️<br/>Frontend Code</td>
<td width="20%" align="center"><b>Step 4</b><br/>📐<br/>Type Safety</td>
<td width="20%" align="center"><b>Step 5</b><br/>✅<br/>Test</td>
</tr>
</table>

**Detailed Steps:**

1. **Read documentation first**

   - Review [RULES.md](RULES.md) for constraints
   - Check [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md) for transaction logic

2. **Backend (Python)**

   - Router → Service → Model (separation of concerns)
   - Add Pydantic schemas for validation
   - Implement business logic in services
   - Create API endpoints in routers

3. **Frontend (TypeScript)**

   - Hook → Component
   - Create React Query hooks in `lib/hooks/`
   - Build UI components
   - Handle loading and error states

4. **Type Safety**

   - Mirror Pydantic schemas in TypeScript (`lib/types.ts`)
   - Use type hints everywhere
   - No `any` types allowed

5. **Test**
   - Write unit tests for calculations
   - Test transaction patterns
   - Verify API endpoints
   - Check edge cases

## 🤝 Contributing

We welcome contributions that align with PAMS' core philosophy!

### 📋 Contribution Guidelines

<table>
<tr>
<td width="25%">
<h4>1️⃣ Follow Patterns</h4>
Adhere to the 4 transaction patterns defined in <a href="RULES.md">RULES.md</a>
</td>
<td width="25%">
<h4>2️⃣ Type Safety</h4>
Use Pydantic (backend) and TypeScript (frontend) everywhere
</td>
<td width="25%">
<h4>3️⃣ Write Tests</h4>
Add tests for all business logic and calculations
</td>
<td width="25%">
<h4>4️⃣ Document</h4>
Update relevant docs when adding features
</td>
</tr>
</table>

### 📝 Commit Message Format

Use conventional commits for clear history:

```bash
feat: add exchange transaction type
fix: correct average price calculation
docs: update API documentation
test: add unit tests for transfer logic
refactor: extract market data fetching to service
perf: optimize holding calculation query
```

**Format:** `<type>: <description>`

**Types:**

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `test` - Adding tests
- `refactor` - Code restructuring
- `perf` - Performance improvement
- `chore` - Maintenance tasks

---

## 💭 Core Philosophy

> **Data Integrity > Feature Completeness**

### The PAMS Principles

<table>
<tr>
<td width="50%">

**🎯 Reality Mirroring**
Record what actually happened, not what you wish happened. Every transaction reflects real-world events.

**📜 Log-Based Truth**
Transactions are immutable logs. Holdings are always computed from these logs. Like Git for finances.

**⏰ Time-Travel Support**
Insert a transaction from the past, and everything forward gets recalculated automatically.

</td>
<td width="50%">

**📐 Type Safety**
Use `Decimal` for money (never `float`), `datetime.date` for dates. Catch errors at compile time.

**🏗️ Separation of Concerns**
Business logic lives in services, not routers. Clean architecture matters.

**🔍 Testability First**
If you can't test it, you can't trust it. All business logic must be unit testable.

</td>
</tr>
</table>

### 🎨 Design Decisions

| Decision                   | Rationale                                                     |
| -------------------------- | ------------------------------------------------------------- |
| **SQLite over PostgreSQL** | Local-first, zero configuration, perfect for personal finance |
| **Computed holdings**      | Single source of truth, automatic consistency                 |
| **Immutable transactions** | Audit trail, time-travel, never lose history                  |
| **Linked transactions**    | Model real-world relationships (transfers, exchanges)         |
| **Type safety everywhere** | Catch bugs early, self-documenting code                       |

## 📜 License

This project is currently for **personal use**. No license specified yet.

> **Note:** If you're interested in using or contributing to this project, please open an issue to discuss licensing options.

---

## 🙏 Acknowledgments

PAMS stands on the shoulders of giants:

### 🔧 Technologies

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Next.js](https://nextjs.org/)** - The React framework for production
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Python SQL toolkit and ORM
- **[React Query](https://tanstack.com/query)** - Powerful data synchronization for React
- **[Tailwind CSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **[Recharts](https://recharts.org/)** - Composable charting library

### 💡 Inspiration

- **Event Sourcing** - Architecture pattern for immutable transaction logs
- **Double-Entry Bookkeeping** - Centuries-old accounting principles
- **Git** - Version control concepts applied to financial data
- **Local-First Software** - Philosophy of user data ownership

---

<div align="center">

## 🚀 Ready to Get Started?

<table>
<tr>
<td align="center" width="33%">
<h3>📖 Read the Docs</h3>
<a href="CONTEXT.md">Project Philosophy</a><br/>
<a href="RULES.md">Development Rules</a><br/>
<a href="TODO.md">Roadmap</a>
</td>
<td align="center" width="33%">
<h3>💻 Install & Run</h3>
<a href="#-quick-start">Quick Start Guide</a><br/>
<a href="SETUP.md">Detailed Setup</a><br/>
<a href="http://localhost:3000">Launch App</a>
</td>
<td align="center" width="33%">
<h3>🔧 Develop</h3>
<a href="API_SPEC.md">API Reference</a><br/>
<a href="DATABASE.md">Database Schema</a><br/>
<a href="CLAUDE.md">Dev Guidelines</a>
</td>
</tr>
</table>

---

### **Made for those who want complete control over their financial data** 🎯

<sub>Coded by Claude Sonnet 4.5 & GLM 4.7</sub>

</div>
