from datetime import datetime

from pydantic import BaseModel

from .models import JobStatus, Type


class ItemBase(BaseModel):
    created_at: datetime
    updated_at: datetime


class Model(ItemBase):
    id: int
    name: str

    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    name: str


class Job(ItemBase):
    id: int
    status: JobStatus
    progress: str | None
    result_path: str | None
    failed_log: str | None

    class Config:
        from_attributes = True


class ArgInfo(BaseModel):
    value: str
    type: Type
    index: int


class JobCreate(BaseModel):
    model_id: int
    argument_infos: list[ArgInfo]


class ArgsCreated(BaseModel):
    argument_infos: list[ArgInfo]
