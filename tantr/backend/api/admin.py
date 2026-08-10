from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from models import get_db, Enquiry, User
from schemas.enquiry import EnquiryResponse
from api.dependencies import get_admin_user

router = APIRouter()


@router.get("/enquiries", response_model=List[EnquiryResponse])
def list_enquiries(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Admin endpoint to list all enquiries."""
    return db.query(Enquiry).order_by(Enquiry.created_at.desc()).all()
