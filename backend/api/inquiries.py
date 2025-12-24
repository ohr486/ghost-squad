"""
Inquiry API endpoints
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models.api.requests import InquiryCreateRequest
from models.api.responses import InquiryResponse
from models.database.inquiry import InquiryModel
from models.enums.inquiry_status import InquiryStatus

# Configure logger
logger = logging.getLogger(__name__)

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
        
        # Convert to response model - ORM object can be passed directly
        return InquiryResponse.model_validate(inquiry)
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while creating inquiry: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="データベースエラーが発生しました"
        )
    except ValidationError as e:
        db.rollback()
        logger.error(f"Validation error while creating inquiry: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="データの検証に失敗しました"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error while creating inquiry: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="予期しないエラーが発生しました"
        )


@router.get("/", response_model=List[InquiryResponse])
async def get_inquiries(
    user_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of inquiries to return (1-1000)"),
    offset: int = Query(default=0, ge=0, description="Number of inquiries to skip (non-negative)"),
    db: Session = Depends(get_db)
) -> List[InquiryResponse]:
    """
    Get list of inquiries, optionally filtered by user.
    
    Args:
        user_id: Optional user ID to filter by
        limit: Maximum number of inquiries to return (1-1000, default: 100)
        offset: Number of inquiries to skip (non-negative, default: 0)
        db: Database session
        
    Returns:
        List[InquiryResponse]: List of inquiries
    """
    try:
        query = db.query(InquiryModel)
        
        # Filter by user_id if provided
        if user_id:
            query = query.filter(InquiryModel.user_id == user_id)
        
        # Add explicit ordering for consistent pagination behavior
        # Order by timestamp descending (newest first), then by id descending as secondary sort
        query = query.order_by(InquiryModel.timestamp.desc(), InquiryModel.id.desc())
        
        # Apply pagination
        inquiries = query.offset(offset).limit(limit).all()
        
        # Convert to response models using list comprehension - ORM objects can be passed directly
        return [InquiryResponse.model_validate(inquiry) for inquiry in inquiries]
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving inquiries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="データベースエラーが発生しました"
        )
    except ValidationError as e:
        logger.error(f"Validation error while processing inquiries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="データの検証に失敗しました"
        )
    except Exception as e:
        logger.error(f"Unexpected error while retrieving inquiries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="予期しないエラーが発生しました"
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
        
        # Convert to response model - ORM object can be passed directly
        return InquiryResponse.model_validate(inquiry)
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without modification
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving inquiry {inquiry_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="データベースエラーが発生しました"
        )
    except ValidationError as e:
        logger.error(f"Validation error while processing inquiry {inquiry_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="データの検証に失敗しました"
        )
    except Exception as e:
        logger.error(f"Unexpected error while retrieving inquiry {inquiry_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="予期しないエラーが発生しました"
        )