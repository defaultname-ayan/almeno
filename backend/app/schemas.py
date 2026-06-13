from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UploadJobResponse(BaseModel):
    job_id: UUID
    status: str


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    status: str
    row_count_raw: int | None = None
    row_count_clean: int | None = None
    created_at: datetime


class JobSummaryBrief(BaseModel):
    total_spend_inr: float | None = None
    total_spend_usd: float | None = None
    anomaly_count: int = 0
    risk_level: str | None = None


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    summary: JobSummaryBrief | None = None
    error_message: str | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    txn_id: str
    txn_date: date | None = None
    merchant: str
    amount: float
    currency: str
    status: str
    category: str
    account_id: str
    notes: str | None = None
    is_anomaly: bool
    anomaly_reason: str | None = None
    llm_category: str | None = None
    llm_failed: bool


class JobSummaryOut(BaseModel):
    total_spend_inr: float | None = None
    total_spend_usd: float | None = None
    top_merchants: list[dict[str, Any]] | dict[str, Any] | None = None
    category_breakdown: dict[str, float] | None = None
    anomaly_count: int = 0
    narrative: str | None = None
    risk_level: str | None = None


class JobResultsResponse(BaseModel):
    job_id: UUID
    status: str
    cleaned_transactions: list[TransactionOut]
    flagged_anomalies: list[TransactionOut]
    category_breakdown: dict[str, float]
    narrative_summary: JobSummaryOut | None = None
