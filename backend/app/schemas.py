from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class NotePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def at_least_one_field(self) -> NotePatch:
        if self.title is None and self.content is None:
            raise ValueError("At least one field must be provided")
        return self


class ActionItemCreate(BaseModel):
    description: str = Field(..., min_length=1)


class ActionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime


class ActionItemPatch(BaseModel):
    description: str | None = Field(default=None, min_length=1)
    completed: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> ActionItemPatch:
        if self.description is None and self.completed is None:
            raise ValueError("At least one field must be provided")
        return self


class PaginatedMeta(BaseModel):
    total: int
    skip: int
    limit: int


class PaginatedNotes(BaseModel):
    items: list[NoteRead]
    meta: PaginatedMeta


class PaginatedActionItems(BaseModel):
    items: list[ActionItemRead]
    meta: PaginatedMeta
