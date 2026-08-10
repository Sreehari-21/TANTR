from datetime import datetime
from pydantic import BaseModel, EmailStr


class EnquiryCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


class EnquiryResponse(EnquiryCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
