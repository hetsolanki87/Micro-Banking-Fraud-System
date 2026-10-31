from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.account import Account
from app.models.user import User
from app.api.auth import get_current_user


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
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
# Get My Account
# =========================

@router.get("/me")
def get_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    account = (
        db.query(Account)
        .filter(Account.user_id == current_user.id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="No bank account found for this user"
        )

    return {
        "account_number": account.account_number,
        "account_type": account.account_type,
        "balance": float(account.balance)
    }