from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import accounts, transactions, dashboard, market_data
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Personal Asset Manager API",
    version="1.0.0",
    description="Local-first financial dashboard API"
)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(market_data.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint to verify API and database connection."""
    from app.database import SessionLocal
    from app.models import Account

    db = SessionLocal()
    try:
        # Test database connection
        count = db.query(Account).count()
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "accounts_count": count
        }
    except Exception as e:
        db.close()
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }
