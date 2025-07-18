from datetime import datetime

from pydantic import BaseModel


class HelloMessage(BaseModel):
    type: str = "hello"
    message: str
    timestamp: datetime | None = None


class ResponseMessage(BaseModel):
    type: str = "response"
    message: str
    timestamp: datetime | None = None


class ErrorMessage(BaseModel):
    type: str = "error"
    message: str
    timestamp: datetime | None = None
