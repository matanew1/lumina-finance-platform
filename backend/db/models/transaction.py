from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("action IN ('buy', 'sell')", name="transaction_action_valid"),
        CheckConstraint("quantity > 0", name="transaction_quantity_positive"),
        CheckConstraint("price > 0", name="transaction_price_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    isin: Mapped[str] = mapped_column(String(12), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
