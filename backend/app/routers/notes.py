from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note
from ..schemas import (
    ExtractRequest,
    ExtractResponse,
    NoteCreate,
    NotePatch,
    NoteRead,
    PaginatedMeta,
    PaginatedNotes,
)
from ..services.extract import extract_action_items
from .common import apply_sort, paginate

router = APIRouter(prefix="/notes", tags=["notes"])

NOTE_SORT_FIELDS = {"id", "title", "created_at", "updated_at"}


@router.get("/", response_model=PaginatedNotes)
def list_notes(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort: str = Query("-created_at", description="Sort by field, prefix with - for desc"),
) -> PaginatedNotes:
    stmt = select(Note)
    if q:
        stmt = stmt.where((Note.title.contains(q)) | (Note.content.contains(q)))

    stmt = apply_sort(stmt, Note, sort, NOTE_SORT_FIELDS)
    rows, total = paginate(db, stmt, skip=skip, limit=limit)
    return PaginatedNotes(
        items=[NoteRead.model_validate(row) for row in rows],
        meta=PaginatedMeta(total=total, skip=skip, limit=limit),
    )


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.post("/extract", response_model=ExtractResponse)
def extract_from_text(payload: ExtractRequest) -> ExtractResponse:
    items = extract_action_items(payload.text)
    return ExtractResponse(items=items, count=len(items))


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.model_validate(note)


@router.patch("/{note_id}", response_model=NoteRead)
def patch_note(note_id: int, payload: NotePatch, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)


@router.post("/{note_id}/extract", response_model=ExtractResponse)
def extract_from_note(note_id: int, db: Session = Depends(get_db)) -> ExtractResponse:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    items = extract_action_items(note.content)
    return ExtractResponse(items=items, count=len(items))
