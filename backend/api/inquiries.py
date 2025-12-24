"""
Inquiry API endpoints
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.api.requests import InquiryCreateRequest
from models.api.responses import InquiryResponse
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


@router.post("/", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
async def create_inquiry(
    inquiry_request: InquiryCreateRequest,
    db: Session = Depends(get_db)
) -> InquiryResponse:
    """
    Create a new inquiry from user input.
    
    Args:
        inquiry_request: The inquiry creation request
        db: Database session
        
    Returns:
        InquiryResponse: The created inquiry
        
    Raises:
        HTTPException: If inquiry creation fails
    """
    try:
        # Create new inquiry model
        inquiry = InquiryModel(
            user_id=inquiry_request.user_id,
            content=inquiry_request.content,
            language=inquiry_request.language,
            status=InquiryStatus.RECEIVED.value,
            inquiry_metadata={}
        )
        
        # Save to database
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        
        # Convert to response model using model_validate
        return InquiryResponse.model_validate({
            "id": inquiry.id,
            "user_id": inquiry.user_id,
            "content": inquiry.content,
            "language": inquiry.language,
            "timestamp": inquiry.timestamp,
            "status": InquiryStatus(inquiry.status),
            "metadata": inquiry.inquiry_metadata or {}
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inquiry: {str(e)}"
        )


@router.get("/", response_model=List[InquiryResponse])
async def get_inquiries(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[InquiryResponse]:
    """
    Get list of inquiries, optionally filtered by user.
    
    Args:
        user_id: Optional user ID to filter by
        limit: Maximum number of inquiries to return (default: 100)
        offset: Number of inquiries to skip (default: 0)
        db: Database session
        
    Returns:
        List[InquiryResponse]: List of inquiries
    """
    try:
        query = db.query(InquiryModel)
        
        # Filter by user_id if provided
        if user_id:
            query = query.filter(InquiryModel.user_id == user_id)
        
        # Apply pagination
        inquiries = query.offset(offset).limit(limit).all()
        
        # Convert to response models
        result = []
        for inquiry in inquiries:
            response = InquiryResponse.model_validate({
                "id": inquiry.id,
                "user_id": inquiry.user_id,
                "content": inquiry.content,
                "language": inquiry.language,
                "timestamp": inquiry.timestamp,
                "status": InquiryStatus(inquiry.status),
                "metadata": inquiry.inquiry_metadata or {}
            })
            result.append(response)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inquiries: {str(e)}"
        )


@router.get("/{inquiry_id}", response_model=InquiryResponse)
async def get_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db)
) -> InquiryResponse:
    """
    Get a specific inquiry by ID.
    
    Args:
        inquiry_id: The inquiry ID
        db: Database session
        
    Returns:
        InquiryResponse: The requested inquiry
        
    Raises:
        HTTPException: If inquiry not found
    """
    try:
        inquiry = db.query(InquiryModel).filter(InquiryModel.id == inquiry_id).first()
        
        if not inquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inquiry with id {inquiry_id} not found"
            )
        
        return InquiryResponse.model_validate({
            "id": inquiry.id,
            "user_id": inquiry.user_id,
            "content": inquiry.content,
            "language": inquiry.language,
            "timestamp": inquiry.timestamp,
            "status": InquiryStatus(inquiry.status),
            "metadata": inquiry.inquiry_metadata or {}
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inquiry: {str(e)}"
        )