
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.transaction import Transaction
from app.models.user import User
from app.models.account import Account
from app.api.auth import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


# =========================
# Database Dependency
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# Admin Authorization
# =========================

def require_admin(current_user: User):
    if str(current_user.role).upper() != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )


# =========================
# Get Fraud Transactions
# ADMIN ONLY
# =========================

@router.get("/fraud-transactions")
def get_fraud_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)

    transactions = (
        db.query(Transaction)
        .filter(Transaction.status == "FRAUD")
        .order_by(Transaction.created_at.desc())
        .all()
    )

    result = []

    for transaction in transactions:
        result.append({
            "transaction_id": transaction.id,
            "sender_account_id": transaction.sender_account_id,
            "receiver_account_id": transaction.receiver_account_id,
            "amount": float(transaction.amount),
            "transaction_type": transaction.transaction_type,
            "status": transaction.status,
            "fraud_score": float(transaction.fraud_score),
            "created_at": transaction.created_at
        })

    return {
        "fraud_transaction_count": len(result),
        "fraud_transactions": result
    }


# =========================
# View All Users
# ADMIN ONLY
# =========================

@router.get("/users")
def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)

    users = db.query(User).order_by(User.id).all()

    return {
        "total_users": len(users),
        "users": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at
            }
            for user in users
        ]
    }


# =========================
# View All Bank Accounts
# ADMIN ONLY
# =========================

@router.get("/accounts")
def get_all_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)

    accounts = (
        db.query(Account)
        .order_by(Account.id)
        .all()
    )

    result = []

    for account in accounts:
        owner = db.query(User).filter(
            User.id == account.user_id
        ).first()

        result.append({
            "account_id": account.id,
            "account_number": account.account_number,
            "user_id": account.user_id,
            "owner_name": owner.name if owner else None,
            "owner_email": owner.email if owner else None,
            "account_type": account.account_type,
            "balance": float(account.balance),
            "is_blocked": account.is_blocked
        })

    return {
        "total_accounts": len(result),
        "accounts": result
    }


# =========================
# Block Bank Account
# ADMIN ONLY
# =========================

@router.put("/accounts/{account_id}/block")
def block_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)

    account = db.query(Account).filter(
        Account.id == account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Bank account not found"
        )

    if account.is_blocked:
        return {
            "message": "Account is already blocked",
            "account_id": account.id,
            "is_blocked": True
        }

    account.is_blocked = True
    db.commit()
    db.refresh(account)

    return {
        "message": "Bank account blocked successfully",
        "account_id": account.id,
        "account_number": account.account_number,
        "is_blocked": account.is_blocked
    }


# =========================
# Unblock Bank Account
# ADMIN ONLY
# =========================

@router.put("/accounts/{account_id}/unblock")
def unblock_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_admin(current_user)

    account = db.query(Account).filter(
        Account.id == account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Bank account not found"
        )

    if not account.is_blocked:
        return {
            "message": "Account is already active",
            "account_id": account.id,
            "is_blocked": False
        }

    account.is_blocked = False
    db.commit()
    db.refresh(account)

    return {
        "message": "Bank account unblocked successfully",
        "account_id": account.id,
        "account_number": account.account_number,
        "is_blocked": account.is_blocked
    }
