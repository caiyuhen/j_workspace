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
