
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.api.auth import get_current_user
from app.services.fraud_detection import calculate_fraud_assessment


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


# =========================
# Request Models
# =========================

class DepositRequest(BaseModel):
    amount: Decimal


class WithdrawalRequest(BaseModel):
    amount: Decimal


class TransferRequest(BaseModel):
    receiver_account_number: str
    amount: Decimal


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
# Deposit Money
# =========================

@router.post("/deposit")
def deposit_money(
    data: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be greater than zero")

    account = db.query(Account).filter(
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="No bank account found for this user")

    if account.is_blocked:
        raise HTTPException(status_code=403, detail="Your bank account is blocked. Deposits are not allowed.")

    account.balance += data.amount

    transaction = Transaction(
        sender_account_id=None,
        receiver_account_id=account.id,
        amount=data.amount,
        transaction_type="DEPOSIT",
        status="COMPLETED",
        fraud_score=0.00
    )

    db.add(transaction)
    db.commit()
    db.refresh(account)
    db.refresh(transaction)

    return {
        "message": "Money deposited successfully",
        "transaction_id": transaction.id,
        "account_number": account.account_number,
        "amount_deposited": float(data.amount),
        "new_balance": float(account.balance)
    }


# =========================
# Withdraw Money
# =========================

@router.post("/withdraw")
def withdraw_money(
    data: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Withdrawal amount must be greater than zero")

    account = db.query(Account).filter(
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="No bank account found for this user")

    if account.is_blocked:
        raise HTTPException(status_code=403, detail="Your bank account is blocked. Withdrawals are not allowed.")

    if account.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    account.balance -= data.amount

    transaction = Transaction(
        sender_account_id=account.id,
        receiver_account_id=None,
        amount=data.amount,
        transaction_type="WITHDRAWAL",
        status="COMPLETED",
        fraud_score=0.00
    )

    db.add(transaction)
    db.commit()
    db.refresh(account)
    db.refresh(transaction)

    return {
        "message": "Money withdrawn successfully",
        "transaction_id": transaction.id,
        "account_number": account.account_number,
        "amount_withdrawn": float(data.amount),
        "new_balance": float(account.balance)
    }


# =========================
# Transfer Money
# =========================

@router.post("/transfer")
def transfer_money(
    data: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be greater than zero")

    sender_account = db.query(Account).filter(
        Account.user_id == current_user.id
    ).first()

    if not sender_account:
        raise HTTPException(status_code=404, detail="Sender bank account not found")

    if sender_account.is_blocked:
        raise HTTPException(status_code=403, detail="Your bank account is blocked. Transfers are not allowed.")

    receiver_account = db.query(Account).filter(
        Account.account_number == data.receiver_account_number
    ).first()

    if not receiver_account:
        raise HTTPException(status_code=404, detail="Receiver bank account not found")

    if receiver_account.is_blocked:
        raise HTTPException(status_code=403, detail="The receiver's bank account is blocked. Transfer is not allowed.")

    if sender_account.id == receiver_account.id:
        raise HTTPException(status_code=400, detail="Cannot transfer money to your own account")

    if sender_account.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # ML + rule-based fraud assessment
    fraud_assessment = calculate_fraud_assessment(
        data.amount,
        sender_account.balance,
        sender_account.id,
        db
    )

    fraud_score = fraud_assessment["fraud_score"]
    risk_level = fraud_assessment["risk_level"]
    risk_factors = fraud_assessment["risk_factors"]
    rule_based_score = fraud_assessment["rule_based_score"]

    # Block high-risk transfers
    if fraud_score >= 70 or rule_based_score >= 70:
        transaction = Transaction(
            sender_account_id=sender_account.id,
            receiver_account_id=receiver_account.id,
            amount=data.amount,
            transaction_type="TRANSFER",
            status="FRAUD",
            fraud_score=fraud_score
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return {
            "message": "Transaction blocked due to suspected fraud",
            "transaction_id": transaction.id,
            "fraud_score": fraud_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "status": "FRAUD"
        }

    # Complete transfer
    sender_account.balance -= data.amount
    receiver_account.balance += data.amount

    transaction = Transaction(
        sender_account_id=sender_account.id,
        receiver_account_id=receiver_account.id,
        amount=data.amount,
        transaction_type="TRANSFER",
        status="COMPLETED",
        fraud_score=fraud_score
    )

    db.add(transaction)
    db.commit()
    db.refresh(sender_account)
    db.refresh(receiver_account)
    db.refresh(transaction)

    return {
        "message": "Money transferred successfully",
        "transaction_id": transaction.id,
        "from_account": sender_account.account_number,
        "to_account": receiver_account.account_number,
        "amount_transferred": float(data.amount),
        "sender_new_balance": float(sender_account.balance),
        "receiver_new_balance": float(receiver_account.balance),
        "fraud_score": fraud_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "status": "COMPLETED"
    }


# =========================
# Transaction History
# =========================

@router.get("/history")
def transaction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(Account).filter(
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="No bank account found for this user")

    transactions = (
        db.query(Transaction)
        .filter(
            (Transaction.sender_account_id == account.id)
            | (Transaction.receiver_account_id == account.id)
        )
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
        "account_number": account.account_number,
        "transaction_count": len(result),
        "transactions": result
    }


# =========================
# Admin Statistics
# ADMIN ONLY
# =========================

@router.get("/statistics")
def get_admin_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if str(current_user.role).upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    total_transactions = db.query(Transaction).count()

    completed_transactions = db.query(Transaction).filter(
        Transaction.status == "COMPLETED"
    ).count()

    fraud_transactions = db.query(Transaction).filter(
        Transaction.status == "FRAUD"
    ).count()

    high_risk_transactions = db.query(Transaction).filter(
        Transaction.fraud_score >= 70
    ).count()

    total_amount = db.query(Transaction.amount).filter(
        Transaction.status == "COMPLETED"
    ).all()

    total_transaction_amount = sum(float(row[0]) for row in total_amount)

    all_scores = db.query(Transaction.fraud_score).all()

    average_fraud_score = (
        sum(float(row[0]) for row in all_scores) / len(all_scores)
        if all_scores else 0.0
    )

    return {
        "total_transactions": total_transactions,
        "completed_transactions": completed_transactions,
        "fraud_transactions": fraud_transactions,
        "high_risk_transactions": high_risk_transactions,
        "total_transaction_amount": total_transaction_amount,
        "average_fraud_score": round(average_fraud_score, 2)
    }

# =========================
# All Transactions
# ADMIN ONLY
# =========================

@router.get("/admin/all-transactions")
def get_all_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if str(current_user.role).upper() != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    transactions = (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return {
        "transaction_count": len(transactions),
        "transactions": [
            {
                "transaction_id": transaction.id,
                "sender_account_id": transaction.sender_account_id,
                "receiver_account_id": transaction.receiver_account_id,
                "amount": float(transaction.amount),
                "transaction_type": transaction.transaction_type,
                "status": transaction.status,
                "fraud_score": float(transaction.fraud_score or 0),
                "created_at": transaction.created_at
            }
            for transaction in transactions
        ]
    }
