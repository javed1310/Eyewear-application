import pytest
from app.services.rx_parser import cross_check_rx
from app.core.config import settings

def test_cross_check_rx_match():
    manual_data = {
        "od_sph": -1.5, "od_cyl": -0.5, "od_axis": 90, "od_pd": 32,
        "os_sph": -1.25, "os_cyl": -0.75, "os_axis": 180, "os_pd": 31.5
    }
    ai_data = manual_data.copy()
    confidence = {
        "overall": 0.95,
        "fields": {k: 0.95 for k in manual_data.keys()}
    }

    needs_review, discrepancies = cross_check_rx(manual_data, ai_data, confidence)
    
    assert needs_review is False
    assert len(discrepancies) == 0

def test_cross_check_rx_discrepancy():
    manual_data = {
        "od_sph": -1.5, "od_cyl": -0.5, "od_axis": 90, "od_pd": 32,
        "os_sph": -1.25, "os_cyl": -0.75, "os_axis": 180, "os_pd": 31.5
    }
    ai_data = manual_data.copy()
    ai_data["od_cyl"] = -0.75  # Discrepancy!
    
    confidence = {
        "overall": 0.95,
        "fields": {k: 0.95 for k in manual_data.keys()}
    }

    needs_review, discrepancies = cross_check_rx(manual_data, ai_data, confidence)
    
    assert needs_review is True
    assert len(discrepancies) == 1
    assert discrepancies[0]["field"] == "od_cyl"
    assert discrepancies[0]["manual"] == -0.5
    assert discrepancies[0]["ai"] == -0.75

def test_cross_check_rx_low_confidence():
    manual_data = {
        "od_sph": -1.5, "od_cyl": -0.5, "od_axis": 90, "od_pd": 32,
        "os_sph": -1.25, "os_cyl": -0.75, "os_axis": 180, "os_pd": 31.5
    }
    ai_data = manual_data.copy()
    
    # Even if they match, low overall confidence flags it
    confidence = {
        "overall": 0.60,  # Below threshold
        "fields": {k: 0.60 for k in manual_data.keys()}
    }

    # Temporarily set threshold high
    old_threshold = settings.RX_CONFIDENCE_THRESHOLD
    settings.RX_CONFIDENCE_THRESHOLD = 0.85
    
    needs_review, discrepancies = cross_check_rx(manual_data, ai_data, confidence)
    
    assert needs_review is True
    assert len(discrepancies) == 0
    
    settings.RX_CONFIDENCE_THRESHOLD = old_threshold
