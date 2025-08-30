"""
Evidence API module.

This module handles evidence upload, processing, and management for Green Score calculation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import uuid
from datetime import datetime

from app.db import get_db
from app.models import User, Evidence
from app.utilis import create_presigned_put, process_ocr, process_climate_practices
from app.config import settings
from app.main import get_current_user

router = APIRouter(prefix="/evidence", tags=["evidence"])

@router.post("/", response_model=Dict[str, Any])
async def create_evidence(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new evidence record and generate upload URL.
    
    Args:
        user: Current authenticated user
        db: Database session
        
    Returns:
        Dict with evidence ID and upload URL
    """
    try:
        evidence_id = str(uuid.uuid4())
        key = f"evidence/{user.id}/{evidence_id}.jpg"
        
        # Generate presigned URL for upload
        upload_url = create_presigned_put(key, "image/jpeg")
        
        # Create evidence record in database
        evidence = Evidence(
            id=evidence_id,
            user_id=user.id,
            s3_key=key,
            status="pending"
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        
        return {
            "id": evidence_id,
            "url": upload_url,
            "status": "pending",
            "message": "Upload URL generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create evidence: {str(e)}"
        )

@router.post("/{evidence_id}/finalize", response_model=Dict[str, Any])
async def finalize_evidence(
    evidence_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalize evidence processing and trigger AI analysis.
    
    Args:
        evidence_id: Evidence ID to finalize
        user: Current authenticated user
        db: Database session
        
    Returns:
        Dict with processing status
    """
    try:
        # Get evidence record
        evidence = db.query(Evidence).filter(
            Evidence.id == evidence_id,
            Evidence.user_id == user.id
        ).first()
        
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        # Update status to processing
        evidence.status = "processing"
        db.commit()
        
        # Trigger background processing
        try:
            # Start OCR processing
            ocr_task = process_ocr.delay(evidence_id)
            
            # Start climate practice detection
            climate_task = process_climate_practices.delay(evidence_id)
            
            return {
                "id": evidence_id,
                "status": "processing",
                "message": "Evidence processing started",
                "tasks": {
                    "ocr_task_id": str(ocr_task.id),
                    "climate_task_id": str(climate_task.id)
                }
            }
            
        except Exception as e:
            # If background processing fails, update status
            evidence.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start processing: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize evidence: {str(e)}"
        )

@router.get("/", response_model=List[Dict[str, Any]])
async def list_evidence(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all evidence for the current user.
    
    Args:
        user: Current authenticated user
        db: Database session
        
    Returns:
        List of evidence records
    """
    try:
        evidence_list = db.query(Evidence).filter(
            Evidence.user_id == user.id
        ).order_by(Evidence.created_at.desc()).all()
        
        return [
            {
                "id": str(evidence.id),
                "status": evidence.status,
                "created_at": evidence.created_at.isoformat(),
                "s3_key": evidence.s3_key
            }
            for evidence in evidence_list
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list evidence: {str(e)}"
        )

@router.get("/{evidence_id}", response_model=Dict[str, Any])
async def get_evidence(
    evidence_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific evidence details.
    
    Args:
        evidence_id: Evidence ID
        user: Current authenticated user
        db: Database session
        
    Returns:
        Evidence details
    """
    try:
        evidence = db.query(Evidence).filter(
            Evidence.id == evidence_id,
            Evidence.user_id == user.id
        ).first()
        
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        return {
            "id": str(evidence.id),
            "status": evidence.status,
            "created_at": evidence.created_at.isoformat(),
            "s3_key": evidence.s3_key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evidence: {str(e)}"
        )

@router.delete("/{evidence_id}")
async def delete_evidence(
    evidence_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete evidence record.
    
    Args:
        evidence_id: Evidence ID to delete
        user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        evidence = db.query(Evidence).filter(
            Evidence.id == evidence_id,
            Evidence.user_id == user.id
        ).first()
        
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        db.delete(evidence)
        db.commit()
        
        return {"message": "Evidence deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete evidence: {str(e)}"
        )
