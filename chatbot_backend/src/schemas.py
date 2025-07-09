from pydantic import BaseModel
from typing import Optional, List, Literal


class SchemaAskRequest(BaseModel):
    user_id: str
    chat_id: Optional[str]
    question: str


class SchemaAskResponse(BaseModel):
    user_id: str
    chat_id: str
    answer: str


class SchemaChatMessage(BaseModel):
    role: Literal["system", "human", "ai"]
    message: str
    timestamp: str


class SchemaFileUploadStatus(BaseModel):
    filename: str
    status: Literal["skipped", "started"]
    message: str


class SchemaUploadResponse(BaseModel):
    results: List[SchemaFileUploadStatus]
