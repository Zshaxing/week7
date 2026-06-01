from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActionItem, Note
from ..schemas import (
    ActionItemCreate,
    ActionItemPatch,
    ActionItemRead,
    PaginatedActionItems,
    PaginatedMeta,
)
from .common import apply_sort, paginate

router = APIRouter(prefix="/action-items", tags=["action_items"])

ACTION_ITEM_SORT_FIELDS = {"id", "description", "completed", "created_at", "updated_at"}


@router.get("/", response_model=PaginatedActionItems)
def list_items(
    db: Session = Depends(get_db),
    completed: Optional[bool] = None,
    note_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort: str = Query("-created_at"),
) -> PaginatedActionItems:
    stmt = select(ActionItem)
    if completed is not None:
        stmt = stmt.where(ActionItem.completed.is_(completed))
    if note_id is not None:
        stmt = stmt.where(ActionItem.note_id == note_id)

    stmt = apply_sort(stmt, ActionItem, sort, ACTION_ITEM_SORT_FIELDS)
    rows, total = paginate(db, stmt, skip=skip, limit=limit)
    return PaginatedActionItems(
        items=[ActionItemRead.model_validate(row) for row in rows],
        meta=PaginatedMeta(total=total, skip=skip, limit=limit),
    )


@router.post("/", response_model=ActionItemRead, status_code=201)
def create_item(payload: ActionItemCreate, db: Session = Depends(get_db)) -> ActionItemRead:
    if payload.note_id is not None and db.get(Note, payload.note_id) is None:
        raise HTTPException(status_code=400, detail="Linked note not found")

    item = ActionItem(description=payload.description, completed=False, note_id=payload.note_id)
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.get("/{item_id}", response_model=ActionItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)) -> ActionItemRead:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return ActionItemRead.model_validate(item)


@router.put("/{item_id}/complete", response_model=ActionItemRead)
def complete_item(item_id: int, db: Session = Depends(get_db)) -> ActionItemRead:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    item.completed = True
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.patch("/{item_id}", response_model=ActionItemRead)
def patch_item(item_id: int, payload: ActionItemPatch, db: Session = Depends(get_db)) -> ActionItemRead:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    if payload.description is not None:
        item.description = payload.description
    if payload.completed is not None:
        item.completed = payload.completed
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    db.delete(item)
