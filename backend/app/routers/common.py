from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


def apply_sort(stmt: Select[Any], model: type, sort: str, allowed_fields: set[str] | None = None) -> Select[Any]:
    sort_field = sort.lstrip("-")
    fields = allowed_fields or {"id", "created_at", "updated_at"}
    if sort_field not in fields or not hasattr(model, sort_field):
        allowed = ", ".join(sorted(fields))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field '{sort_field}'. Allowed: {allowed}",
        )
    order_fn = desc if sort.startswith("-") else asc
    return stmt.order_by(order_fn(getattr(model, sort_field)))


def paginate(db: Session, stmt: Select[Any], *, skip: int, limit: int) -> tuple[list[Any], int]:
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return list(rows), total
