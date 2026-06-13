import asyncio
import os
from datetime import datetime, timezone
from uuid import UUID

from celery import Celery
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Job, JobStatus, JobSummary, Transaction
from app.services.anomaly_service import annotate_anomalies
from app.services.csv_processor import clean_transactions_csv
from app.services.llm_service import (
    classify_missing_categories_batch,
    generate_narrative_summary,
)

celery_app = Celery(
    "worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task(name="app.tasks.ping")
def ping():
    return {"status": "ok"}


@celery_app.task(name="app.tasks.process_job")
def process_job(job_id: str):
    return asyncio.run(process_job_async(job_id))


async def process_job_async(job_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Job).options(selectinload(Job.summary)).where(Job.id == UUID(job_id))
        )
        job = result.scalar_one_or_none()

        if not job:
            return {"error": "job not found"}

        try:
            job.status = JobStatus.PROCESSING
            await session.commit()

            file_path = os.path.join(settings.upload_dir, f"{job.id}.csv")

            records, raw_count, clean_count = clean_transactions_csv(file_path)
            records = annotate_anomalies(records)
            records = classify_missing_categories_batch(records)
            summary_payload = generate_narrative_summary(records)

            job.row_count_raw = raw_count
            job.row_count_clean = clean_count

            await session.execute(delete(Transaction).where(Transaction.job_id == job.id))
            if job.summary:
                await session.delete(job.summary)
                await session.flush()

            for record in records:
                session.add(
                    Transaction(
                        job_id=job.id,
                        txn_id=record["txn_id"],
                        txn_date=record["txn_date"],
                        merchant=record["merchant"],
                        amount=record["amount"],
                        currency=record["currency"],
                        status=record["status"],
                        category=record["category"],
                        account_id=record["account_id"],
                        notes=record["notes"],
                        is_anomaly=record["is_anomaly"],
                        anomaly_reason=record["anomaly_reason"],
                        llm_category=record["llm_category"],
                        llm_raw_response=record["llm_raw_response"],
                        llm_failed=record["llm_failed"],
                    )
                )

            session.add(
                JobSummary(
                    job_id=job.id,
                    total_spend_inr=summary_payload["total_spend_inr"],
                    total_spend_usd=summary_payload["total_spend_usd"],
                    top_merchants=summary_payload["top_merchants"],
                    category_breakdown=summary_payload["category_breakdown"],
                    anomaly_count=summary_payload["anomaly_count"],
                    narrative=summary_payload["narrative"],
                    risk_level=summary_payload["risk_level"],
                )
            )

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)

            await session.commit()
            return {"job_id": job_id, "status": "completed"}

        except Exception as exc:
            await session.rollback()

            result = await session.execute(select(Job).where(Job.id == UUID(job_id)))
            failed_job = result.scalar_one_or_none()
            if failed_job:
                failed_job.status = JobStatus.FAILED
                failed_job.error_message = str(exc)
                await session.commit()

            return {"job_id": job_id, "status": "failed", "error": str(exc)}
