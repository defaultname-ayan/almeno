import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_session
from app.models import Job, JobStatus
from app.schemas import (
    JobListItem,
    JobResultsResponse,
    JobStatusResponse,
    JobSummaryBrief,
    JobSummaryOut,
    TransactionOut,
    UploadJobResponse,
)
from app.tasks import process_job

router = APIRouter()


@router.post("/upload", response_model=UploadJobResponse)
async def upload_csv(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV uploads are allowed")

    job = Job(filename=file.filename, status=JobStatus.PENDING)
    session.add(job)
    await session.commit()
    await session.refresh(job)

    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, f"{job.id}.csv")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    process_job.delay(str(job.id))

    return UploadJobResponse(job_id=job.id, status=job.status.value)


@router.get("", response_model=list[JobListItem])
async def list_jobs(
    status: JobStatus | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Job).order_by(Job.created_at.desc())
    if status:
        stmt = stmt.where(Job.status == status)

    result = await session.execute(stmt)
    jobs = result.scalars().all()
    return jobs


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Job)
        .options(selectinload(Job.summary))
        .where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    summary = None
    if job.status == JobStatus.COMPLETED and job.summary:
        summary = JobSummaryBrief(
            total_spend_inr=float(job.summary.total_spend_inr or 0),
            total_spend_usd=float(job.summary.total_spend_usd or 0),
            anomaly_count=job.summary.anomaly_count,
            risk_level=job.summary.risk_level.value if job.summary.risk_level else None,
        )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        summary=summary,
        error_message=job.error_message,
    )


@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Job)
        .options(selectinload(Job.transactions), selectinload(Job.summary))
        .where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    transactions = [
        TransactionOut(
            txn_id=t.txn_id,
            txn_date=t.txn_date,
            merchant=t.merchant,
            amount=float(t.amount),
            currency=t.currency,
            status=t.status,
            category=t.category,
            account_id=t.account_id,
            notes=t.notes,
            is_anomaly=t.is_anomaly,
            anomaly_reason=t.anomaly_reason,
            llm_category=t.llm_category,
            llm_failed=t.llm_failed,
        )
        for t in job.transactions
    ]

    anomalies = [t for t in transactions if t.is_anomaly]

    category_breakdown = {}
    narrative_summary = None

    if job.summary:
        category_breakdown = job.summary.category_breakdown or {}
        narrative_summary = JobSummaryOut(
            total_spend_inr=float(job.summary.total_spend_inr or 0),
            total_spend_usd=float(job.summary.total_spend_usd or 0),
            top_merchants=job.summary.top_merchants,
            category_breakdown=job.summary.category_breakdown or {},
            anomaly_count=job.summary.anomaly_count,
            narrative=job.summary.narrative,
            risk_level=job.summary.risk_level.value if job.summary.risk_level else None,
        )

    return JobResultsResponse(
        job_id=job.id,
        status=job.status.value,
        cleaned_transactions=transactions,
        flagged_anomalies=anomalies,
        category_breakdown=category_breakdown,
        narrative_summary=narrative_summary,
    )
