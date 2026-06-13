import enum
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    row_count_raw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count_clean: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    summary: Mapped["JobSummary | None"] = relationship(
        "JobSummary",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    txn_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    txn_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    merchant: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    anomaly_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    llm_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_failed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    job: Mapped["Job"] = relationship("Job", back_populates="transactions")


class JobSummary(Base):
    __tablename__ = "job_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    total_spend_inr: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    total_spend_usd: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    top_merchants: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    category_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    anomaly_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[RiskLevel | None] = mapped_column(
        Enum(RiskLevel, name="risk_level_enum"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    job: Mapped["Job"] = relationship("Job", back_populates="summary")
#indexing for better retrival
Index("ix_transactions_job_account", Transaction.job_id, Transaction.account_id)
Index("ix_transactions_job_merchant", Transaction.job_id, Transaction.merchant)
Index("ix_transactions_job_anomaly", Transaction.job_id, Transaction.is_anomaly)
Index("ix_jobs_status_created", Job.status, Job.created_at)
