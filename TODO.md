# TODO.md - Personal Asset Manager

## Phase 1: Project Setup & Core Infrastructure

### Backend Setup
- [ ] Initialize Python virtual environment
- [ ] Create `requirements.txt` with core dependencies (FastAPI, SQLAlchemy, uvicorn, python-dotenv)
- [ ] Set up FastAPI project structure (`app/main.py`, `app/models/`, `app/schemas/`, `app/routers/`, `app/services/`)
- [ ] Configure SQLAlchemy with SQLite connection
- [ ] Create `.env` template with database path and API keys
- [ ] Set up CORS middleware for local development

### Frontend Setup
- [ ] Initialize Next.js 14+ project with TypeScript
- [ ] Install core dependencies (React Query, Recharts, Tailwind CSS)
- [ ] Configure `next.config.js` with API rewrites to proxy backend
- [ ] Set up project directory structure (`app/`, `components/`, `lib/`)
- [ ] Create base layout with navigation

### Database Schema
- [ ] Define `User` model (id, currency_setting, join_date)
- [ ] Define `Account` model (id, user_id, name, type, currency)
- [ ] Define `Holding` model (id, account_id, ticker, quantity, avg_price)
- [ ] Define `Transaction` model (id, account_id, date, type, ticker, quantity, price, amount, linked_tx_id)
- [ ] Define `MarketData` model (id, date, ticker, closing_price, exchange_rate)
- [ ] Define `AssetSnapshot` model (id, user_id, date, total_assets_krw, total_assets_usd, principal)
- [ ] Create database migration/initialization script
- [ ] Add indexes for performance (transaction.date, transaction.account_id, marketdata.date+ticker)

## Phase 2: Backend Core Logic

### Transaction Services
- [ ] Implement deposit/withdrawal logic (single account balance change)
- [ ] Implement transfer logic (linked transactions, validation)
- [ ] Implement buy/sell logic (asset conversion within account)
- [ ] Implement exchange logic (cross-currency conversion)
- [ ] Implement dividend recording logic
- [ ] Create transaction validation service (check linked_tx integrity, date validity)

### Calculation Engine
- [ ] Calculate holding average price from transaction history
- [ ] Calculate current holding value from market data
- [ ] Calculate unrealized P/L (current value vs cost basis)
- [ ] Calculate total assets across all accounts
- [ ] Handle multi-currency conversion
- [ ] Implement time-travel recalculation (when past transaction inserted)

### Market Data Integration
- [ ] Create market data API client (Yahoo Finance or Alpha Vantage)
- [ ] Implement stock price fetching by date
- [ ] Implement exchange rate fetching by date
- [ ] Create caching layer (store in MarketData table)
- [ ] Handle API errors and rate limits gracefully
- [ ] Allow manual price entry as fallback

### API Endpoints
- [ ] `POST /accounts` - Create new account
- [ ] `GET /accounts` - List all accounts
- [ ] `GET /accounts/{id}` - Get account details with holdings
- [ ] `POST /transactions` - Record new transaction
- [ ] `GET /transactions` - List transactions with filters
- [ ] `PUT /transactions/{id}` - Edit transaction
- [ ] `DELETE /transactions/{id}` - Soft delete transaction
- [ ] `GET /dashboard/summary` - Total assets, allocation, stats
- [ ] `GET /dashboard/chart` - Asset volatility time series
- [ ] `GET /market-data/{ticker}` - Fetch current/historical price

## Phase 3: Frontend UI Components

### Dashboard (`/home`)
- [ ] Total asset card with KRW/USD toggle
- [ ] Hide/show amount privacy toggle
- [ ] Increase/decrease rate by period (day/month/year)
- [ ] Current exchange rate display
- [ ] Asset allocation pie chart (Recharts)
- [ ] Top N assets bar chart
- [ ] Asset volatility line/candle chart

### Account List (`/accounts`)
- [ ] Account card grid layout
- [ ] Display account name, balance, type indicator
- [ ] "Add New Account" button with modal
- [ ] Action buttons by account type (transfer, trade, exchange, etc.)
- [ ] Search/filter accounts

### Account Details (`/accounts/[id]`)
- [ ] Summary header (total value, P/L, cash balance)
- [ ] Tab 1: Holdings list (ticker, qty, avg price, current price, return %)
- [ ] Tab 2: Transaction history timeline
- [ ] Tab 3: Analysis (account-specific asset graph, dividend calendar)
- [ ] Transaction filtering by type/date
- [ ] Edit/delete transaction buttons

### Data Entry Modals
- [ ] Add Account modal (name, type, currency, initial balance)
- [ ] Add Transaction modal (date picker, type selector, ticker input, price/qty)
- [ ] Transfer modal (from account, to account, amount)
- [ ] Exchange modal (from currency, to currency, rate)
- [ ] Buy/Sell modal (ticker search, quantity, price)

## Phase 4: Data Flow & State Management

### React Query Setup
- [ ] Configure QueryClient with local cache
- [ ] Create query hooks for accounts (`useAccounts`, `useAccountDetails`)
- [ ] Create query hooks for transactions (`useTransactions`)
- [ ] Create query hooks for dashboard data (`useDashboardSummary`, `useAssetChart`)
- [ ] Implement optimistic updates for transaction creation
- [ ] Handle error states and retry logic

### Form Handling
- [ ] Create reusable form components (input, select, date picker)
- [ ] Add form validation (required fields, date ranges, positive amounts)
- [ ] Handle linked transaction creation (transfer flow)
- [ ] Auto-fetch market data when ticker entered

## Phase 5: Time Travel & Historical Data

### Past Transaction Handling
- [ ] Validate transaction date is not in the future
- [ ] Fetch market data for the specified transaction date
- [ ] Trigger recalculation of holdings after transaction date
- [ ] Update AssetSnapshot records for affected date range
- [ ] Show visual indicator when viewing recalculated data
- [ ] Test edge cases (weekend dates, market holidays, missing data)

### Asset Snapshot Generation
- [ ] Create daily snapshot calculation job
- [ ] Backfill historical snapshots from transaction history
- [ ] Handle gaps in market data (weekends, holidays)
- [ ] Optimize snapshot queries for chart rendering

## Phase 6: Testing & Validation

### Unit Tests (Backend)
- [ ] Test average price calculation logic
- [ ] Test P/L calculation with various scenarios
- [ ] Test multi-currency conversion
- [ ] Test transaction linking validation
- [ ] Test time-travel recalculation accuracy

### Integration Tests
- [ ] Test complete deposit flow (API → DB → calculation)
- [ ] Test transfer flow (linked transactions)
- [ ] Test buy/sell flow (asset conversion)
- [ ] Test past transaction insertion (recalculation)
- [ ] Test API error handling

### End-to-End Tests (Frontend)
- [ ] Test dashboard loads correctly
- [ ] Test account creation flow
- [ ] Test transaction entry flow
- [ ] Test account detail navigation
- [ ] Test chart rendering with real data

## Phase 7: Polish & Documentation

### User Experience
- [ ] Add loading states for all async operations
- [ ] Add success/error toast notifications
- [ ] Improve mobile responsiveness
- [ ] Add keyboard shortcuts for common actions
- [ ] Create onboarding tutorial for first-time users

### Documentation
- [ ] Write README.md with setup instructions
- [ ] Document API endpoints (FastAPI auto-docs)
- [ ] Create user guide with screenshots
- [ ] Add inline code comments for complex logic
- [ ] Document backup and restore procedure

### Performance Optimization
- [ ] Add database indexes for slow queries
- [ ] Implement pagination for transaction history
- [ ] Optimize chart data queries (aggregate by day/week)
- [ ] Lazy load account details
- [ ] Cache frequently accessed market data

## Phase 8: Advanced Features (Post-MVP)

### Analytics
- [ ] Monthly spending breakdown by category
- [ ] Investment performance report (IRR, Sharpe ratio)
- [ ] Tax lot tracking (FIFO/LIFO)
- [ ] Dividend income summary

### Automation
- [ ] Recurring transaction templates
- [ ] Auto-fetch latest market data on dashboard load
- [ ] Scheduled snapshot generation (daily job)

### Import/Export
- [ ] Export transactions to CSV
- [ ] Import transactions from CSV
- [ ] Export asset report to PDF

### Settings
- [ ] User preferences (default currency, date format)
- [ ] Theme customization (dark mode)
- [ ] Data backup reminder
- [ ] API key management UI

## Deployment Checklist

### Pre-Launch
- [ ] Test on Windows, Mac, Linux
- [ ] Create installation script (automated setup)
- [ ] Write troubleshooting guide
- [ ] Prepare sample data for demo

### Launch
- [ ] Create GitHub repository with MIT license
- [ ] Tag v1.0.0 release
- [ ] Write announcement post
- [ ] Create demo video

## Ongoing Maintenance

### Monitoring
- [ ] Track API call usage (avoid hitting rate limits)
- [ ] Monitor database file size growth
- [ ] Check for slow queries

### Updates
- [ ] Keep dependencies updated (npm, pip)
- [ ] Handle breaking changes in market data APIs
- [ ] Add new asset types as needed (crypto, commodities)

---

## Current Priority (Start Here)

1. **Phase 1:** Complete project setup
2. **Phase 2:** Implement core transaction logic
3. **Phase 3:** Build basic dashboard UI
4. **Phase 4:** Connect frontend to backend with React Query
5. **Phase 5:** Add time-travel functionality
6. **Phase 6:** Test thoroughly
7. **Phase 7:** Polish and document
8. **Phase 8:** Add advanced features based on user feedback
