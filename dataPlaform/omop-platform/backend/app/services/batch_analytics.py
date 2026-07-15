import csv
import io
from datetime import datetime

from app.models.incremental import BatchAnalysisSummary
from app.models.raw import ErrorRecord, RawRecord, SourceBatch


class BatchAnalyticsService:
    def __init__(self, db):
        self.db = db

    def build_summary_for_batch(self, batch_id: str) -> BatchAnalysisSummary:
        batch = self.db.query(SourceBatch).filter(SourceBatch.id == batch_id).one()
        summary = (
            self.db.query(BatchAnalysisSummary)
            .filter(BatchAnalysisSummary.batch_id == batch_id)
            .one_or_none()
        )
        if summary is None:
            summary = BatchAnalysisSummary(
                batch_id=batch_id,
                dataset_name=batch.dataset_name,
            )

        summary.total_rows = batch.total_rows or 0
        summary.error_rows = batch.error_rows or 0
        summary.inserted_rows = batch.inserted_rows or 0
        summary.updated_rows = batch.updated_rows or 0
        summary.deleted_rows = batch.deleted_rows or 0
        summary.core_metrics = {
            "raw_records": self.db.query(RawRecord).filter(RawRecord.batch_id == batch_id).count(),
            "error_records": self.db.query(ErrorRecord).filter(ErrorRecord.batch_id == batch_id).count(),
        }

        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    def query_summaries(
        self,
        batch_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        status: str | None = None,
        batch_ids: list[str] | None = None,
    ) -> list[tuple[SourceBatch, BatchAnalysisSummary | None]]:
        query = self.db.query(SourceBatch, BatchAnalysisSummary).outerjoin(
            BatchAnalysisSummary,
            BatchAnalysisSummary.batch_id == SourceBatch.id,
        )

        if batch_type:
            query = query.filter(SourceBatch.batch_type == batch_type)
        if status:
            query = query.filter(SourceBatch.status == status)
        if start_time:
            query = query.filter(SourceBatch.created_at >= start_time)
        if end_time:
            query = query.filter(SourceBatch.created_at <= end_time)
        if batch_ids:
            query = query.filter(SourceBatch.id.in_(batch_ids))

        return query.order_by(SourceBatch.created_at.desc(), SourceBatch.id.desc()).all()

    def serialize_row(
        self,
        batch: SourceBatch,
        summary: BatchAnalysisSummary | None,
    ) -> dict:
        return {
            "id": str(batch.id),
            "filename": str(batch.filename),
            "batch_type": str(batch.batch_type or "full"),
            "dataset_name": str(batch.dataset_name or "ingestion"),
            "trigger_mode": str(batch.trigger_mode or "auto"),
            "window_start": batch.window_start.isoformat() if batch.window_start else None,
            "window_end": batch.window_end.isoformat() if batch.window_end else None,
            "total_rows": int(summary.total_rows if summary else (batch.total_rows or 0)),
            "error_rows": int(summary.error_rows if summary else (batch.error_rows or 0)),
            "inserted_rows": int(summary.inserted_rows if summary else (batch.inserted_rows or 0)),
            "updated_rows": int(summary.updated_rows if summary else (batch.updated_rows or 0)),
            "deleted_rows": int(summary.deleted_rows if summary else (batch.deleted_rows or 0)),
            "unchanged_rows": int(batch.unchanged_rows or 0),
            "success_rate": int(summary.success_rate if summary else 0),
            "processing_duration_ms": int(summary.processing_duration_ms if summary else 0),
            "core_metrics": summary.core_metrics if summary else None,
            "detail_stats": summary.detail_stats if summary else None,
            "status": str(batch.status),
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "processed_at": summary.processed_at.isoformat() if summary and summary.processed_at else None,
        }

    def compare_summaries(self, batch_ids: list[str]) -> list[dict]:
        rows = self.query_summaries(batch_ids=batch_ids)
        serialized = {
            batch.id: self.serialize_row(batch, summary)
            for batch, summary in rows
        }
        return [serialized[batch_id] for batch_id in batch_ids if batch_id in serialized]

    def export_csv(self, batch_ids: list[str] | None = None) -> str:
        rows = self.query_summaries(batch_ids=batch_ids)
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "batch_id",
                "filename",
                "batch_type",
                "status",
                "total_rows",
                "inserted_rows",
                "updated_rows",
                "deleted_rows",
                "error_rows",
            ],
        )
        writer.writeheader()
        for batch, summary in rows:
            item = self.serialize_row(batch, summary)
            writer.writerow(
                {
                    "batch_id": item["id"],
                    "filename": item["filename"],
                    "batch_type": item["batch_type"],
                    "status": item["status"],
                    "total_rows": item["total_rows"],
                    "inserted_rows": item["inserted_rows"],
                    "updated_rows": item["updated_rows"],
                    "deleted_rows": item["deleted_rows"],
                    "error_rows": item["error_rows"],
                }
            )
        return buffer.getvalue()

    def query_summaries(
        self,
        batch_type: str | None = None,
        start_time=None,
        end_time=None,
        status: str | None = None,
    ):
        query = (
            self.db.query(SourceBatch, BatchAnalysisSummary)
            .outerjoin(BatchAnalysisSummary, BatchAnalysisSummary.batch_id == SourceBatch.id)
        )

        if batch_type:
            query = query.filter(SourceBatch.batch_type == batch_type)
        if status:
            query = query.filter(SourceBatch.status == status)
        if start_time:
            query = query.filter(SourceBatch.created_at >= start_time)
        if end_time:
            query = query.filter(SourceBatch.created_at <= end_time)

        return query.order_by(SourceBatch.created_at.desc()).all()

    @staticmethod
    def serialize_row(batch: SourceBatch, summary: BatchAnalysisSummary | None = None) -> dict:
        return {
            "id": batch.id,
            "filename": batch.filename,
            "batch_type": batch.batch_type or "full",
            "dataset_name": batch.dataset_name or "ingestion",
            "trigger_mode": batch.trigger_mode or "auto",
            "window_start": batch.window_start.isoformat() if batch.window_start else None,
            "window_end": batch.window_end.isoformat() if batch.window_end else None,
            "status": batch.status,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "total_rows": batch.total_rows or 0,
            "error_rows": batch.error_rows or 0,
            "inserted_rows": batch.inserted_rows or 0,
            "updated_rows": batch.updated_rows or 0,
            "deleted_rows": batch.deleted_rows or 0,
            "unchanged_rows": batch.unchanged_rows or 0,
            "core_metrics": summary.core_metrics if summary else None,
            "detail_stats": summary.detail_stats if summary else None,
        }

    def export_csv(self, batch_ids: list[str]) -> str:
        rows = self.query_summaries()
        lines = [
            "batch_id,filename,batch_type,status,total_rows,inserted_rows,updated_rows,deleted_rows,error_rows"
        ]
        for batch, _summary in rows:
            if batch_ids and batch.id not in batch_ids:
                continue
            lines.append(
                f"{batch.id},{batch.filename},{batch.batch_type},{batch.status},{batch.total_rows or 0},"
                f"{batch.inserted_rows or 0},{batch.updated_rows or 0},{batch.deleted_rows or 0},{batch.error_rows or 0}"
            )
        return "\n".join(lines)
