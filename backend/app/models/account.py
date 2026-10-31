
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Boolean
from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)

    account_number = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    balance = Column(
        Numeric(15, 2),
        default=0.00,
        nullable=False
    )

    account_type = Column(
        String(20),
        default="SAVINGS"
    )

    # Account blocking controlled by admin
    is_blocked = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )
