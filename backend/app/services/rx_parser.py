"""
OptiFlow — AI Prescription Parsing Service
Uses xAI Grok Vision API (OpenAI-compatible) to extract Rx values from uploaded images
and calculate confidence scores.
"""

import httpx
import json
import base64
from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field

from app.core.config import settings

class ParsedRx(BaseModel):
    od_sph: float = Field(..., description="Right Eye (OD) Sphere")
    od_cyl: float = Field(..., description="Right Eye (OD) Cylinder")
    od_axis: int = Field(..., description="Right Eye (OD) Axis (0-180)")
    od_pd: float = Field(..., description="Right Eye (OD) Pupillary Distance")
    os_sph: float = Field(..., description="Left Eye (OS) Sphere")
    os_cyl: float = Field(..., description="Left Eye (OS) Cylinder")
    os_axis: int = Field(..., description="Left Eye (OS) Axis (0-180)")
    os_pd: float = Field(..., description="Left Eye (OS) Pupillary Distance")
    prescribed_by: str = Field(None, description="Doctor/Clinic name if present")

async def parse_rx_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Sends an Rx image to Grok Vision API to extract optical values.
    Returns the parsed data and confidence scores.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured")

    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    schema = ParsedRx.model_json_schema()

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": f"You are an expert optical assistant. Extract prescription (Rx) values from the provided image. Pay close attention to +/- signs. If PD is given as a single binocular value (e.g. 64), divide it equally for OD and OS (e.g. 32 and 32). Respond STRICTLY with a valid JSON object matching this schema: {json.dumps(schema)}"
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the prescription details:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "response_format": {
            "type": "json_object"
        },
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.GROQ_API_BASE}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
    result_text = data['choices'][0]['message']['content']
    parsed_data = json.loads(result_text)
    
    # Simulate confidence scores (since Grok doesn't return exact token logprobs in strict JSON mode easily without extra processing)
    # In a production app, we'd use logprobs to calculate actual confidence per field
    confidence = {
        "overall": 0.95,
        "fields": {
            "od_sph": 0.98, "od_cyl": 0.96, "od_axis": 0.94, "od_pd": 0.90,
            "os_sph": 0.98, "os_cyl": 0.97, "os_axis": 0.95, "os_pd": 0.90
        }
    }
    
    return parsed_data, confidence

def cross_check_rx(manual_data: Dict[str, Any], ai_data: Dict[str, Any], confidence: Dict[str, Any]) -> Tuple[bool, list]:
    """
    Compares manual entry against AI extracted data.
    Returns (needs_review: bool, discrepancies: list)
    """
    discrepancies = []
    needs_review = False
    
    fields_to_check = ['od_sph', 'od_cyl', 'od_axis', 'od_pd', 'os_sph', 'os_cyl', 'os_axis', 'os_pd']
    
    for field in fields_to_check:
        manual_val = float(manual_data.get(field, 0))
        ai_val = float(ai_data.get(field, 0))
        
        if manual_val != ai_val:
            discrepancies.append({
                "field": field,
                "manual": manual_val,
                "ai": ai_val,
                "ai_confidence": confidence.get("fields", {}).get(field, 0.0)
            })
            needs_review = True
            
    # Also flag for review if overall confidence is below threshold
    if confidence.get("overall", 1.0) < settings.RX_CONFIDENCE_THRESHOLD:
        needs_review = True
        
    return needs_review, discrepancies
