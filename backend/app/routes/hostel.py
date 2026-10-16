from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.hostel import Hostel, HostelMember
from app.schemas.hostel import HostelCreate, HostelResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/hostels", tags=["Hostels"])


@router.post(
    "", 
    response_model=HostelResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new hostel"
)
def create_hostel(
    hostel_in: HostelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new hostel and automatically registers the creator as ADMIN.
    """
    hostel = Hostel(
        hostel_name=hostel_in.hostel_name.strip(),
        created_by=current_user.id
    )
    db.add(hostel)
    db.commit()
    db.refresh(hostel)

    # Automatically add creator as ADMIN member
    admin_member = HostelMember(
        hostel_id=hostel.id,
        user_id=current_user.id,
        role="ADMIN"
    )
    db.add(admin_member)
    db.commit()

    return {
        "id": hostel.id,
        "hostel_name": hostel.hostel_name,
        "created_by": hostel.created_by,
        "created_at": hostel.created_at,
        "member_count": 1
    }


@router.get(
    "", 
    response_model=List[HostelResponse],
    summary="List all hostels the user belongs to"
)
def get_user_hostels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns all hostels where the current user is a registered member or creator.
    """
    memberships = db.query(HostelMember).filter(HostelMember.user_id == current_user.id).all()
    hostel_ids = [m.hostel_id for m in memberships]

    hostels = db.query(Hostel).filter(Hostel.id.in_(hostel_ids)).all()
    
    result = []
    for h in hostels:
        count = db.query(HostelMember).filter(HostelMember.hostel_id == h.id).count()
        result.append({
            "id": h.id,
            "hostel_name": h.hostel_name,
            "created_by": h.created_by,
            "created_at": h.created_at,
            "member_count": count
        })
    return result


@router.get(
    "/{hostel_id}", 
    response_model=HostelResponse,
    summary="Get details of a specific hostel"
)
def get_hostel_by_id(
    hostel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves details of a hostel by ID.
    """
    hostel = db.query(Hostel).filter(Hostel.id == hostel_id).first()
    if not hostel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hostel not found")

    count = db.query(HostelMember).filter(HostelMember.hostel_id == hostel.id).count()
    return {
        "id": hostel.id,
        "hostel_name": hostel.hostel_name,
        "created_by": hostel.created_by,
        "created_at": hostel.created_at,
        "member_count": count
    }
