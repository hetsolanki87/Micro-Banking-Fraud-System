from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.account import Account


router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_account_number(db: Session) -> str:
    while True:
        account_number = str(random.randint(1000000000, 9999999999))

        existing_account = (
            db.query(Account)
            .filter(Account.account_number == account_number)
            .first()
        )

        if not existing_account:
            return account_number


@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
        role="USER"
    )

    db.add(new_user)
    db.flush()

    new_account = Account(
        account_number=generate_account_number(db),
        user_id=new_user.id,
        balance=0.00,
        account_type="SAVINGS"
    )

    db.add(new_account)
    db.commit()

    db.refresh(new_user)
    db.refresh(new_account)

    return {
        "message": "User and bank account created successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "account_number": new_account.account_number,
        "account_type": new_account.account_type,
        "balance": float(new_account.balance)
    }