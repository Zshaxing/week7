from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note, Tag
from ..schemas import (
    ExtractRequest,
    ExtractResponse,
    NoteCreate,
    NotePatch,
    NoteRead,
    NoteTagsUpdate,
    PaginatedMeta,
    PaginatedNotes,
)
from ..services.extract import extract_action_items
from .common import apply_sort, paginate

router = APIRouter(prefix="/notes", tags=["notes"])

NOTE_SORT_FIELDS = {"id", "title", "created_at", "updated_at"}


def serialize_note(note: Note) -> NoteRead:
    return NoteRead(
        id=note.id,
        title=note.title,
        content=note.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
        tag_ids=[tag.id for tag in note.tags],
    )


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
        items=[serialize_note(row) for row in rows],
        meta=PaginatedMeta(total=total, skip=skip, limit=limit),
    )


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.flush()
    db.refresh(note)
    return serialize_note(note)


@router.post("/extract", response_model=ExtractResponse)
def extract_from_text(payload: ExtractRequest) -> ExtractResponse:
    items = extract_action_items(payload.text)
    return ExtractResponse(items=items, count=len(items))


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return serialize_note(note)


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
    return serialize_note(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)


@router.put("/{note_id}/tags", response_model=NoteRead)
def set_note_tags(note_id: int, payload: NoteTagsUpdate, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    tags = db.execute(select(Tag).where(Tag.id.in_(payload.tag_ids))).scalars().all()
    if len(tags) != len(set(payload.tag_ids)):
        raise HTTPException(status_code=400, detail="One or more tag IDs are invalid")

    note.tags = tags
    db.add(note)
    db.flush()
    db.refresh(note)
    return serialize_note(note)


@router.post("/{note_id}/extract", response_model=ExtractResponse)
def extract_from_note(note_id: int, db: Session = Depends(get_db)) -> ExtractResponse:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    items = extract_action_items(note.content)
    return ExtractResponse(items=items, count=len(items))
