# CONTEXT.md - Personal Asset Manager

## Project Overview

**Personal Asset Manager (PAM)** is a local-first, reality-mirroring financial dashboard for tracking personal assets across multiple account types (checking, brokerage, foreign currency, MMF). Unlike traditional accounting software that focuses on budgeting, PAM reconstructs your complete financial state from transaction logs, enabling "time travel" to see how past transactions affect current asset valuation.

**This is a professional Asset Management System (PMS) beyond a simple household ledger.** While the UI remains intuitive and simple, the backend logic is designed to be accounting-strict (incorporating double-entry bookkeeping concepts) to track all asset fluctuations in the real world without omission.

## Core Concepts

### Reality Mirroring Philosophy

Instead of treating your asset dashboard as a static record you manually update, PAM models real-world financial activities:

- **You don't "set" your balance** - you record transactions that happened
- **Every transaction has a real date** - when it actually occurred, not when you entered it
- **Market reality is respected** - stock prices and exchange rates from the transaction date are used

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

The `Holding` table (current balances) is a **computed view** derived from `Transaction` history. If you add a transaction from 6 months ago, the system recalculates everything from that point forward.

## Key Features

### 1. Multi-Account Support
- **Deposit/Withdrawal accounts (입출금통장)** - KRW cash only. Daily spending, linked to household account book
- **Securities accounts (증권계좌)** - All currencies and securities (stocks, ETFs, gold, etc.). Full investment management
- **Foreign Currency accounts (외화통장)** - USD holdings. Currency exchange with other accounts
- **Money Market accounts (MMF)** - KRW cash only. Money market fund with interest tracking

### 2. Four Core Transaction Patterns

PAM formalizes the flow of money in reality into 4 fundamental patterns:

#### **Pattern ① Pure Income/Expense**
- **Examples:** Salary deposit, food expense, bill payment
- **Logic:** The cash balance of a single account increases or decreases
- **Asset Impact:** Total assets change

| Type | Description | Asset Impact |
|------|-------------|--------------|
| `Deposit` | Income (salary, gift) | Total assets ↑ |
| `Withdrawal` | Expense (payment, fee) | Total assets ↓ |
| `Dividend` | Stock dividend received | Total assets ↑ |

#### **Pattern ② Simple Transfer**
- **Example:** Transfer from Toss account → Kiwoom Securities account
- **Logic:**
  - Withdrawal from Account A (`Transfer_Out`) + Deposit into Account B (`Transfer_In`)
  - Two transactions must be connected via `Linked_Tx_ID`
- **Asset Impact:** **No change in total assets** (moving from left pocket to right pocket)

| Type | Description | Asset Impact |
|------|-------------|--------------|
| `Transfer_In/Out` | Move money between accounts | Total assets unchanged |

#### **Pattern ③ Asset Form Conversion (Invest/Liquidate)**
- **Example:** Buying Samsung Electronics with cash in a securities account
- **Logic:**
  - Cash decreases + Stock quantity increases within the same account
  - **No change in total asset value** at the moment of purchase (excluding fees)
  - Asset value changes afterwards based on stock price fluctuations

| Type | Description | Asset Impact |
|------|-------------|--------------|
| `Buy` | Purchase securities with cash | Total assets unchanged (at transaction time) |
| `Sell` | Liquidate securities to cash | Total assets unchanged (at transaction time) |

#### **Pattern ④ Exchange**
- **Example:** Selling KRW to buy USD
- **Logic:**
  - Withdrawal from Account A (KRW) + Deposit into Account A (USD)
  - The exchange ratio (rate) between currencies is recorded

| Type | Description | Asset Impact |
|------|-------------|--------------|
| `Exchange` | Convert currency | Total assets unchanged (at transaction time) |

### 3. Time Machine

When you enter a transaction for a past date:

1. System fetches market data (stock prices, exchange rates) from that date
2. Recalculates `Holding` average prices from that point forward
3. Updates `AssetSnapshot` graph data for the timeline
4. Dashboard reflects the corrected historical asset flow

**Example:** You forgot to record buying 10 shares of AAPL on Jan 15 at $150. Today is March 1, AAPL is $180. When you input the Jan 15 transaction, the system:
- Uses the $150 price for the purchase
- Shows the correct asset graph from Jan 15 to Mar 1
- Reflects the $300 gain in your current holdings

### 4. Asset Valuation

**Current Total Assets = Sum of all holdings valued at current market prices**

For each holding:
```
Value = Quantity × Current_Price (from MarketData)
```

For cash holdings:
```
Value = Amount (no price lookup needed)
```

Multi-currency conversion:
```
Total_Assets_KRW = Σ(Holding_Value_in_Original_Currency × Current_Exchange_Rate)
```

## Architecture Decisions

### Why SQLite?
- **Zero configuration** - No database server setup
- **File-based Storage** - Entire database in one file (e.g., `asset_data.db`) within the project directory
- **Portable** - Works on Windows, Mac, Linux without changes
- **Data Ownership & Backup:**
  - **Zero-Config Backup:** The user can back up the entire database simply by copying the `.db` file
  - **Cloud Sync:** Placing the project or DB file in a synced folder (Dropbox, Google Drive, iCloud) automatically provides real-time cloud backup and version history without any extra code

### Why FastAPI + Next.js?

**Frontend (Next.js):**
- **Core Framework:** Next.js (App Router)
  - Runs on `localhost:3000`
  - **Connectivity (Rewrites):** Instead of making direct requests to the backend port, the client calls `/api` paths. Next.js handles the proxy to the FastAPI backend (e.g., `localhost:8000`), naturally bypassing CORS issues and simplifying configuration
  - **State Management:** React Query (TanStack Query) for efficient data fetching and caching in a local environment where network latency is negligible

**Backend (FastAPI):**
- **Core Framework:** FastAPI (Python)
  - Runs on a background port (e.g., `localhost:8000`) to handle calculations
  - **Server Runner:** Uvicorn (lightweight, avoiding heavy production-grade WSGI configurations)
  - **Environment:** Uses `python-dotenv` to manage settings and runs within a dedicated virtual environment (venv)
  - Fast Python framework with automatic API docs, type safety

**Separation of concerns:**
- UI logic separate from calculation logic
- **Local development** - Both run on `localhost`, no deployment complexity

### Why Not Use a Cloud Service?
- **Privacy** - Financial data never leaves your computer
- **Cost** - No monthly subscription, no API limits
- **Speed** - No network latency
- **Control** - You own your data format and history

## Application Structure (Sitemap)

### **A. Dashboard (`/home`)**
A control tower to view the flow of total assets.

**Components:**
- **Total Asset Card:**
  - Total Valuation (KRW/USD toggle, hide amount feature)
  - Increase/Decrease Rate by Period (Day, Month, Year)
  - Current Exchange Rate ($/₩) display

- **Charts:**
  - **Asset Allocation:** Pie chart (by asset class e.g., stock/cash/bond or by nature e.g., safe/risk)
  - **Size Ranking:** Top N assets bar chart
  - **Asset Volatility:** Visualizing changes in total asset value like a stock chart (candle/line)

### **B. Account List (`/accounts`)**
Lists and manages all held accounts in a card format.

**Features:**
- Account Name, Balance, Type indicator
- 'Add New Account' button
- **Action Buttons by Type:**
  - **Deposit/Withdrawal:** Transfer, Transaction History, (Future) Payment, Auto-transfer setup
  - **Securities:** Input Dividends, Check Trading Records
  - **Foreign Currency:** Exchange (Buy/Sell Dollars)
  - **MMF:** Check Interest (Profit)

### **C. Account Details (`/accounts/[id]`)**
Check in-depth information of a specific account.

**Layout:**
- **Summary Header:** Total Valuation, Valuation Gain/Loss (P/L), Cash (Deposit)
- **Tab 1. Holdings (Inventory):**
  - Item List (Ticker, Quantity, Avg. Price vs. Current Price, Return Rate)
  - Cash is also treated as an 'item' and included in the list
- **Tab 2. Transaction History:**
  - Timeline-style log (Deposit, Withdrawal, Buy, Sell, Dividend, etc.)
  - Filtering and manual edit/delete functions
- **Tab 3. Analysis:**
  - Asset trend graph for this specific account
  - Dividend Calendar (Securities account only)

### **D. Data Entry Modal (`/add`, `/record`)**
- **Initial Balance Setup:** Applies the exchange rate/closing price of the specific date when designated
- **Transaction Entry:** Input When (Date), What (Ticker), At what price (Price), and How many (Qty)

## User Workflow

### Initial Setup
1. Run the backend: `uvicorn app.main:app --reload`
2. Run the frontend: `npm run dev`
3. Open browser to `localhost:3000`
4. Create accounts (e.g., "Toss Checking", "Kiwoom Brokerage")
5. Set initial balances with transaction date

### Daily Usage
1. **Dashboard** - See total asset value, allocation chart, volatility graph
2. **Add transaction** - Record what you did today (bought stock, paid rent, etc.)
3. **Check account details** - View holdings, transaction history, P/L

### Periodic Tasks
- **Backfill past transactions** - Add transactions you forgot to record
- **Reconcile** - Compare dashboard balances with real account statements
- **Backup** - Copy `asset_data.db` to external drive or cloud

## Data Flow Examples

### Example 1: Simple Transfer
```
User action: Transfer $500 from Deposit to Securities account

Transaction 1:
  account_id: 1 (Deposit account)
  type: Transfer_Out
  amount: -500
  linked_tx_id: 2

Transaction 2:
  account_id: 2 (Securities account)
  type: Transfer_In
  amount: 500
  linked_tx_id: 1

Holding changes:
  Account 1 CASH: 1000 → 500
  Account 2 CASH: 0 → 500

Total assets: No change
```

### Example 2: Stock Purchase
```
User action: Buy 10 shares of AAPL at $150 (total $1500)

Transaction:
  account_id: 2 (Securities account)
  type: Buy
  ticker: AAPL
  quantity: 10
  price: 150
  amount: -1500

Holding changes:
  Account 2 CASH: 2000 → 500
  Account 2 AAPL: 0 qty → 10 qty (avg price $150)

Total assets: No change (at transaction time)
```

### Example 3: Asset Valuation After Price Change
```
Initial state (from Example 2):
  AAPL holding: 10 shares @ avg $150
  Current AAPL price: $180

Valuation:
  Holding value = 10 × $180 = $1800
  Cost basis = 10 × $150 = $1500
  Unrealized gain = $300 (+20%)

Total assets: Increased by $300 since purchase
```

## Technical Constraints

### Backend
- Python 3.10+
- FastAPI 0.100+
- SQLAlchemy 2.0+ for ORM
- Uvicorn for ASGI server
- python-dotenv for environment management

### Frontend
- Node.js 18+
- Next.js 14+ (App Router)
- React Query (TanStack Query) for data fetching
- Recharts for visualization
- Tailwind CSS for styling

### Database
- SQLite 3.35+
- Foreign key constraints enabled
- WAL mode for better concurrency

## External Dependencies

### Market Data API
- **Stock prices:** Yahoo Finance API or Alpha Vantage (free tier)
- **Exchange rates:** Open Exchange Rates or similar
- **Caching:** Store fetched data in `MarketData` table to minimize API calls

### Limitations
- Free tier APIs have rate limits (handle gracefully)
- Historical data may have gaps (weekends, holidays)
- Some stocks may not have data for very old dates

## Deployment Model

**Personal Asset Manager is NOT deployed** - it runs entirely on the user's local machine:

1. User clones the repository
2. Sets up Python virtual environment
3. Installs Node dependencies
4. Runs backend and frontend in separate terminals
5. Accesses via `localhost:3000`

**No Docker/Nginx/cloud hosting** - designed for maximum simplicity and data ownership.

## Future Extensions (Out of Scope for MVP)

- Automatic bank sync via Plaid
- Mobile app (React Native)
- Multi-user support (household accounts)
- Tax report generation
- Budget forecasting
- Investment recommendations

## Glossary

- **Holding:** Current quantity of an asset (stock, cash, etc.) in an account
- **Transaction:** A single financial event (buy, sell, transfer, etc.)
- **Ticker:** Stock symbol (e.g., AAPL, MSFT) or special value CASH
- **Linked Transaction:** Two transactions that form a transfer (connected via `linked_tx_id`)
- **Market Data:** Historical stock prices and exchange rates
- **Asset Snapshot:** Daily total asset value record for graphing
- **Avg Price:** Average purchase price of a holding (cost basis)
- **P/L:** Profit/Loss (current value - cost basis)
