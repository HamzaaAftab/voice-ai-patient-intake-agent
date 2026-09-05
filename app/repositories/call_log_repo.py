from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.call_log import CallLog
from app.repositories.base import BaseRepository


class CallLogRepository(BaseRepository[CallLog]):
    """Data access repository for telephony call logs and transcripts."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CallLog, session)

    async def create(self, call_log: CallLog) -> CallLog:
        self.session.add(call_log)
        await self.session.flush()
        await self.session.refresh(call_log)
        return call_log

    async def get_by_call_id(self, call_id: str) -> Optional[CallLog]:
        stmt = select(CallLog).where(CallLog.call_id == call_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(
        self, patient_id: Optional[str] = None, limit: int = 50
    ) -> List[CallLog]:
        from sqlalchemy.orm import selectinload
        stmt = select(CallLog).options(selectinload(CallLog.patient))
        if patient_id:
            stmt = stmt.where(CallLog.patient_id == patient_id)
        stmt = stmt.order_by(CallLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_post_call(
        self,
        call_id: str,
        transcript: Optional[str] = None,
        recording_url: Optional[str] = None,
        duration_seconds: int = 0,
        patient_id: Optional[str] = None,
    ) -> Optional[CallLog]:
        log = await self.get_by_call_id(call_id)
        if not log:
            return None
        if transcript:
            log.transcript = transcript
        if recording_url:
            log.recording_url = recording_url
        if duration_seconds:
            log.duration_seconds = duration_seconds
        if patient_id:
            log.patient_id = patient_id
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log
