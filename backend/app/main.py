from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine

from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction

from app.api import admin
from app.api.users import router as users_router
from app.api.transactions import router as transactions_router
from app.api.auth import router as auth_router
from app.api.accounts import router as accounts_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Micro-Banking & Fraud Detection System",
    version="1.0.0"
)


# ================================
# CORS CONFIGURATION
# ================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================
# ROUTERS
# ================================

app.include_router(users_router)
app.include_router(transactions_router)
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(admin.router)


# ================================
# ROOT
# ================================

@app.get("/")
def root():
    return {
        "message": "Micro-Banking & Fraud Detection API is running"
    }


# ================================
# HEALTH CHECK
# ================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }