"""
OptiFlow — Prescriptions API Router
Handles AI-powered parsing of prescription images.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.rx_parser import parse_rx_image
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

class ParseResponse(BaseModel):
    parsed_data: Dict[str, Any]
    confidence: Dict[str, Any]

@router.post("/parse-image", response_model=ParseResponse)
async def parse_prescription_image(
    file: UploadFile = File(...),
):
    """
    Accepts an uploaded image of an optical prescription, sends it to the xAI Grok
    Vision API, and returns the structured optical data and confidence scores.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    try:
        contents = await file.read()
        parsed_data, confidence = await parse_rx_image(contents, file.content_type)
        return ParseResponse(parsed_data=parsed_data, confidence=confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {str(e)}")
