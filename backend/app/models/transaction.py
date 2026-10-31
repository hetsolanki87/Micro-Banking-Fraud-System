from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    sender_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=True
    )

    receiver_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=True
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False
    )

    transaction_type = Column(
        String(20),
        default="TRANSFER"
    )

    status = Column(
        String(20),
        default="COMPLETED"
    )

    fraud_score = Column(
        Numeric(5, 2),
        default=0.00
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )