import logging
import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import scan_duration_seconds, scans_total
from app.db.models import ModuleStatus, ScanResult, Target, TargetStatus
from app.services.modules import MODULES, ModuleSpec, get_module
from app.services.notifier import notifier

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _run_module(spec: ModuleSpec, url: str, cwd: str) -> tuple[ModuleStatus, str, str]:
    cmd = spec.command.format(url=shlex.quote(url))
    log.info("module_start", extra={"module": spec.name, "url": url})
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=spec.timeout,
            env={**os.environ, "TARGET": url},
        )
        output = proc.stdout or ""
        if proc.stderr.strip():
            output += f"\n[stderr]\n{proc.stderr}"
        if proc.returncode == 0:
            return ModuleStatus.completed, output, ""
        return ModuleStatus.failed, output, f"exit_code={proc.returncode}"
    except subprocess.TimeoutExpired as exc:
        return ModuleStatus.failed, exc.stdout or "", f"timeout after {spec.timeout}s"
    except Exception as exc:  # noqa: BLE001
        return ModuleStatus.failed, "", repr(exc)


def _read_legacy_output(url: str) -> str | None:
    path = Path(settings.results_dir) / f"{url}-output.txt"
    if path.exists():
        try:
            return path.read_text(errors="replace")
        except Exception:  # noqa: BLE001
            return None
    return None


def _modules_for(target: Target) -> list[ModuleSpec]:
    if not target.selected_modules:
        return MODULES
    chosen: list[ModuleSpec] = []
    for name in target.selected_modules:
        spec = get_module(name)
        if spec:
            chosen.append(spec)
    return chosen or MODULES


def _refresh_cancel(db: Session, target_id: int) -> bool:
    db.expire_all()
    fresh = db.get(Target, target_id)
    return bool(fresh and fresh.cancel_requested)


def run_scan(db: Session, target: Target) -> None:
    started = time.perf_counter()
    target.status = TargetStatus.running
    target.started_at = _now()
    target.error = None
    db.commit()

    notifier.send(f"Recon started for {target.url}")

    cwd = str(Path(settings.modules_dir).parent)
    Path(settings.results_dir).mkdir(parents=True, exist_ok=True)

    failed_modules: list[str] = []
    cancelled = False

    for spec in _modules_for(target):
        if _refresh_cancel(db, target.id):
            cancelled = True
            break

        result = (
            db.query(ScanResult)
            .filter(ScanResult.target_id == target.id, ScanResult.module == spec.name)
            .one_or_none()
        )
        if result is None:
            result = ScanResult(target_id=target.id, module=spec.name)
            db.add(result)

        result.status = ModuleStatus.running
        result.started_at = _now()
        result.error = None
        db.commit()

        status, output, error = _run_module(spec, target.url, cwd)

        result.status = status
        result.output = output or None
        result.error = error or None
        result.completed_at = _now()
        db.commit()

        if status == ModuleStatus.failed:
            failed_modules.append(spec.name)

    legacy = _read_legacy_output(target.url)
    if legacy:
        summary = (
            db.query(ScanResult)
            .filter(ScanResult.target_id == target.id, ScanResult.module == "summary")
            .one_or_none()
        )
        if summary is None:
            summary = ScanResult(target_id=target.id, module="summary")
            db.add(summary)
        summary.status = ModuleStatus.completed
        summary.output = legacy
        summary.started_at = summary.started_at or _now()
        summary.completed_at = _now()
        db.commit()

    target.completed_at = _now()
    if cancelled:
        target.status = TargetStatus.cancelled
        target.error = "cancelled by user"
    elif failed_modules and len(failed_modules) == len(_modules_for(target)):
        target.status = TargetStatus.failed
        target.error = "all modules failed"
    else:
        target.status = TargetStatus.completed
        if failed_modules:
            target.error = f"partial failure: {', '.join(failed_modules)}"
    db.commit()

    scans_total.labels(status=target.status.value).inc()
    scan_duration_seconds.observe(time.perf_counter() - started)

    if target.status == TargetStatus.completed:
        msg = f"Recon for {target.url} completed"
    elif target.status == TargetStatus.cancelled:
        msg = f"Recon for {target.url} was cancelled"
    else:
        msg = f"Recon for {target.url} failed: {target.error}"
    notifier.send(msg)
