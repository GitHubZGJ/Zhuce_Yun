from datetime import date, datetime, time
from statistics import mean

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import AiPhase, AiTaskStatus, AI_PHASE_LABELS
from app.core.exceptions import BizException
from app.modules.ai_ops.grading import (
    ESCALATION_RULES,
    GRADING_TABLE,
    LEVELS,
    RUBRIC,
    THRESHOLDS,
)
from app.modules.ai_ops.models import AiTask, Defect
from app.modules.ai_ops.schemas import AiTaskCreate, AiTaskUpdate, DefectCreate, DefectUpdate

PHASE_ORDER = [phase.value for phase in AiPhase]
WEIGHTS = {"correctness": 25, "completeness": 20, "runnability": 25, "maintainability": 15, "compliance": 15}


def compute_failure_score(
    correctness: int,
    completeness: int,
    runnability: int,
    maintainability: int,
    compliance: int,
) -> float:
    """失效分 FS = 20 × Σ(权重×维度分) / 100，范围 0–100，越高越不可靠。"""
    weighted = (
        WEIGHTS["correctness"] * correctness
        + WEIGHTS["completeness"] * completeness
        + WEIGHTS["runnability"] * runnability
        + WEIGHTS["maintainability"] * maintainability
        + WEIGHTS["compliance"] * compliance
    )
    return round(weighted / 5, 1)


def failure_band(score: float) -> dict:
    for item in THRESHOLDS:
        if item["min"] <= score <= item["max"]:
            return {"level": item["level"], "label": item["label"], "action": item["action"]}
    return {"level": "CRITICAL", "label": "严重失效", "action": "阻断交付并根因分析"}


def serialize_task(task: AiTask) -> dict:
    return {
        "id": task.id,
        "phase": task.phase,
        "phase_name": AI_PHASE_LABELS.get(task.phase, task.phase),
        "task_name": task.task_name,
        "level": task.level,
        "agent_name": task.agent_name,
        "status": task.status,
        "correctness": task.correctness,
        "completeness": task.completeness,
        "runnability": task.runnability,
        "maintainability": task.maintainability,
        "compliance": task.compliance,
        "failure_score": task.failure_score,
        "failure_band": failure_band(task.failure_score),
        "reliability": round(100 - task.failure_score, 1),
        "human_minutes": task.human_minutes,
        "retries": task.retries,
        "occurred_at": task.occurred_at,
        "notes": task.notes,
        "created_at": task.created_at,
    }


def serialize_defect(defect: Defect) -> dict:
    return {
        "id": defect.id,
        "title": defect.title,
        "phase": defect.phase,
        "phase_name": AI_PHASE_LABELS.get(defect.phase, defect.phase),
        "category": defect.category,
        "severity": defect.severity,
        "occurrences": defect.occurrences,
        "ai_related": defect.ai_related,
        "status": defect.status,
        "found_at": defect.found_at,
        "root_cause": defect.root_cause,
        "fix_action": defect.fix_action,
        "created_at": defect.created_at,
    }


def list_tasks(
    db: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    phase: str | None = None,
    level: str | None = None,
    status: str | None = None,
):
    stmt = select(AiTask)
    if q:
        keyword = f"%{q.strip()}%"
        stmt = stmt.where(or_(AiTask.task_name.ilike(keyword), AiTask.agent_name.ilike(keyword)))
    if phase:
        stmt = stmt.where(AiTask.phase == phase)
    if level:
        stmt = stmt.where(AiTask.level == level)
    if status:
        stmt = stmt.where(AiTask.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(AiTask.occurred_at.desc(), AiTask.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [serialize_task(item) for item in items], total


def create_task(db: Session, payload: AiTaskCreate) -> dict:
    data = payload.model_dump(exclude={"phase", "level", "status", "occurred_at"})
    task = AiTask(
        **data,
        phase=payload.phase.value,
        level=payload.level.value,
        status=payload.status.value,
        occurred_at=(
            datetime.combine(payload.occurred_at, time(9, 0))
            if payload.occurred_at
            else datetime.now()
        ),
    )
    task.failure_score = compute_failure_score(
        payload.correctness,
        payload.completeness,
        payload.runnability,
        payload.maintainability,
        payload.compliance,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return serialize_task(task)


def update_task(db: Session, task_id: int, payload: AiTaskUpdate) -> dict:
    task = db.get(AiTask, task_id)
    if task is None:
        raise BizException(40401, "AI 任务不存在", 404)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is None:
            continue
        if field == "occurred_at":
            value = datetime.combine(value, time(9, 0))
        elif field in ("phase", "level", "status"):
            value = value.value if hasattr(value, "value") else value
        setattr(task, field, value)
    task.failure_score = compute_failure_score(
        task.correctness,
        task.completeness,
        task.runnability,
        task.maintainability,
        task.compliance,
    )
    db.commit()
    db.refresh(task)
    return serialize_task(task)


def delete_task(db: Session, task_id: int) -> None:
    task = db.get(AiTask, task_id)
    if task is None:
        raise BizException(40401, "AI 任务不存在", 404)
    db.delete(task)
    db.commit()


def list_defects(
    db: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    phase: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    status: str | None = None,
):
    stmt = select(Defect)
    if q:
        keyword = f"%{q.strip()}%"
        stmt = stmt.where(or_(Defect.title.ilike(keyword), Defect.category.ilike(keyword)))
    if phase:
        stmt = stmt.where(Defect.phase == phase)
    if category:
        stmt = stmt.where(Defect.category == category)
    if severity:
        stmt = stmt.where(Defect.severity == severity)
    if status:
        stmt = stmt.where(Defect.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Defect.occurrences.desc(), Defect.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [serialize_defect(item) for item in items], total


def create_defect(db: Session, payload: DefectCreate) -> dict:
    defect = Defect(
        title=payload.title,
        phase=payload.phase.value,
        category=payload.category.strip(),
        severity=payload.severity.value,
        occurrences=payload.occurrences,
        ai_related=payload.ai_related,
        status=payload.status.value,
        found_at=payload.found_at or date.today(),
        root_cause=payload.root_cause,
        fix_action=payload.fix_action,
    )
    db.add(defect)
    db.commit()
    db.refresh(defect)
    return serialize_defect(defect)


def update_defect(db: Session, defect_id: int, payload: DefectUpdate) -> dict:
    defect = db.get(Defect, defect_id)
    if defect is None:
        raise BizException(40401, "缺陷记录不存在", 404)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is None:
            continue
        if field in ("phase", "severity", "status"):
            value = value.value if hasattr(value, "value") else value
        setattr(defect, field, value)
    db.commit()
    db.refresh(defect)
    return serialize_defect(defect)


def delete_defect(db: Session, defect_id: int) -> None:
    defect = db.get(Defect, defect_id)
    if defect is None:
        raise BizException(40401, "缺陷记录不存在", 404)
    db.delete(defect)
    db.commit()


def reliability_overview(tasks: list[AiTask]) -> dict:
    if not tasks:
        return {
            "task_count": 0,
            "avg_failure_score": 0.0,
            "success_rate": 0.0,
            "reliability": 0.0,
            "high_failure_count": 0,
        }
    avg_score = mean(task.failure_score for task in tasks)
    success_rate = sum(1 for task in tasks if task.status == AiTaskStatus.SUCCESS.value) / len(tasks) * 100
    reliability = 0.6 * (100 - avg_score) + 0.4 * success_rate
    return {
        "task_count": len(tasks),
        "avg_failure_score": round(avg_score, 1),
        "success_rate": round(success_rate, 1),
        "reliability": round(reliability, 1),
        "high_failure_count": sum(1 for task in tasks if task.failure_score >= 40),
    }


def pareto_data(db: Session) -> list[dict]:
    rows = db.execute(
        select(Defect.category, func.sum(Defect.occurrences).label("occurrences"))
        .group_by(Defect.category)
        .order_by(func.sum(Defect.occurrences).desc())
    ).all()
    total = sum(row.occurrences for row in rows) or 1
    result = []
    cumulative = 0
    for row in rows:
        cumulative += row.occurrences
        result.append(
            {
                "category": row.category,
                "occurrences": int(row.occurrences),
                "share": round(row.occurrences / total * 100, 1),
                "cumulative": round(cumulative / total * 100, 1),
            }
        )
    return result


def stats(db: Session) -> dict:
    tasks = db.scalars(select(AiTask)).all()
    overview = reliability_overview(tasks)

    by_phase = []
    for phase in PHASE_ORDER:
        phase_tasks = [task for task in tasks if task.phase == phase]
        phase_overview = reliability_overview(phase_tasks)
        by_phase.append(
            {
                "phase": phase,
                "phase_name": AI_PHASE_LABELS[phase],
                **phase_overview,
            }
        )

    level_counts = {level: 0 for level in ("L1", "L2", "L3")}
    status_counts = {status: 0 for status in ("SUCCESS", "PARTIAL", "FAILED")}
    for task in tasks:
        level_counts[task.level] = level_counts.get(task.level, 0) + 1
        status_counts[task.status] = status_counts.get(task.status, 0) + 1

    defects = db.scalars(select(Defect)).all()
    total_occurrences = sum(defect.occurrences for defect in defects)
    open_occurrences = sum(
        defect.occurrences for defect in defects if defect.status == "OPEN"
    )
    ai_occurrences = sum(
        defect.occurrences for defect in defects if defect.ai_related
    )
    severity_counts = {severity: 0 for severity in ("CRITICAL", "MAJOR", "MINOR", "TRIVIAL")}
    for defect in defects:
        severity_counts[defect.severity] = (
            severity_counts.get(defect.severity, 0) + defect.occurrences
        )

    failure_cases = sorted(
        [serialize_task(task) for task in tasks if task.failure_score >= 40],
        key=lambda item: item["failure_score"],
        reverse=True,
    )

    pareto = pareto_data(db)

    return {
        "summary": {
            **overview,
            "human_minutes": sum(task.human_minutes for task in tasks),
            "retry_count": sum(task.retries for task in tasks),
            "defect_records": len(defects),
            "defect_occurrences": total_occurrences,
            "open_occurrences": open_occurrences,
            "ai_related_occurrences": ai_occurrences,
            "ai_related_rate": round(ai_occurrences / total_occurrences * 100, 1)
            if total_occurrences
            else 0.0,
            "open_rate": round(open_occurrences / total_occurrences * 100, 1)
            if total_occurrences
            else 0.0,
        },
        "by_phase": by_phase,
        "level_distribution": [
            {"level": level, "count": count} for level, count in level_counts.items()
        ],
        "status_distribution": [
            {"status": status, "count": count} for status, count in status_counts.items()
        ],
        "severity_distribution": [
            {"severity": severity, "count": count}
            for severity, count in severity_counts.items()
        ],
        "failure_cases": failure_cases,
        "pareto": pareto,
        "rubric": RUBRIC,
        "thresholds": THRESHOLDS,
        "formula": "FS = 20 × (25C + 20I + 25R + 15M + 15S) / 100；R = 0.6×(100−平均FS) + 0.4×一次通过率×100",
    }


def grading_config() -> dict:
    return {
        "levels": LEVELS,
        "rules": ESCALATION_RULES,
        "table": GRADING_TABLE,
        "rubric": RUBRIC,
        "thresholds": THRESHOLDS,
    }
