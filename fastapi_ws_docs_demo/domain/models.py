from datetime import datetime

from pydantic import BaseModel, Field
from typing_extensions import Optional


class HelloMessage(BaseModel):
    '''Welcome Message'''
    type: str = "hello"
    message: str
    timestamp: datetime | None = None


class ResponseMessage(BaseModel):
    '''Wow, someone reached back'''
    type: str = "response"
    response_to: str
    message: str
    timestamp: datetime | None = None


class ErrorMessage(BaseModel):
    '''Oops, something went wrong'''
    type: str = "error"
    error: str
    details: str
    timestamp: datetime | None = None


class BodyModel(BaseModel):
    name: str = Field(..., examples=['Jarvis'])
    age: Optional[int] = Field(None, ge=0, examples=[42])
