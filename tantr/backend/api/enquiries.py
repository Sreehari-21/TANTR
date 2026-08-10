from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from models import get_db, Enquiry
from schemas.enquiry import EnquiryCreate, EnquiryResponse

router = APIRouter()


@router.post("/", response_model=EnquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_enquiry(data: EnquiryCreate, db: Session = Depends(get_db)):
    """Public endpoint to submit a contact form enquiry."""
    enquiry = Enquiry(
        name=data.name,
        email=data.email,
        subject=data.subject,
        message=data.message,
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    return enquiry
