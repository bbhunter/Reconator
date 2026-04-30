import logging
import signal
import sys
import time

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.models import Target, TargetStatus
from app.db.session import SessionLocal, engine
from app.services.scanner import run_scan

log = logging.getLogger(__name__)
_shutdown = False


def _handle_signal(signum, _frame) -> None:  # noqa: ANN001
    global _shutdown
    log.info("worker received signal=%s — shutting down after current job", signum)
    _shutdown = True


def _claim_next() -> Target | None:
    with SessionLocal() as db:
        target = db.scalar(
            select(Target)
            .where(Target.status == TargetStatus.queued)
            .order_by(Target.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if target is None:
            return None
        target.status = TargetStatus.running
        db.commit()
        db.refresh(target)
        return target


def _process(target_id: int) -> None:
    with SessionLocal() as db:
        target = db.get(Target, target_id)
        if target is None:
            log.warning("target id=%s vanished", target_id)
            return
        try:
            run_scan(db, target)
        except Exception as exc:  # noqa: BLE001
            log.exception("scan failed target_id=%s", target_id)
            target.status = TargetStatus.failed
            target.error = repr(exc)[:1000]
            db.commit()


def main() -> None:
    configure_logging()
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    log.info("worker starting poll_interval=%ss", settings.worker_poll_interval_seconds)

    Base.metadata.create_all(bind=engine)

    while not _shutdown:
        target = _claim_next()
        if target is None:
            for _ in range(settings.worker_poll_interval_seconds):
                if _shutdown:
                    break
                time.sleep(1)
            continue

        log.info("processing target_id=%s url=%s", target.id, target.url)
        _process(target.id)

    log.info("worker stopped")


if __name__ == "__main__":
    sys.exit(main())
