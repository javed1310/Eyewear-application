"""
OptiFlow — TAT Risk Prediction Service
Loads the trained Random Forest model to predict the probability of an SLA breach for an order.
"""

import os
import joblib
import pandas as pd
from datetime import datetime, timezone

from app.models.order import Order
from app.models.lens_spec import LensSpec
from app.models.enums import RiskLevel
from app.core.config import settings

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "tat_model.joblib")

class TATPredictor:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            print(f"Warning: Model not found at {MODEL_PATH}. Prediction will return default.")

    def predict_risk(self, order: Order, lens_spec: LensSpec) -> float:
        """
        Returns the probability (0.0 to 1.0) that the order will breach its SLA.
        """
        if not self.model:
            return 0.0

        # Calculate dwell hours in current stage
        dwell_hours = 0.0
        if order.current_stage_entered_at:
            now = datetime.now(timezone.utc)
            delta = now - order.current_stage_entered_at
            dwell_hours = delta.total_seconds() / 3600.0

        # Construct feature dictionary matching training data
        features = {
            'lens_type': [lens_spec.lens_type.value if hasattr(lens_spec.lens_type, 'value') else lens_spec.lens_type],
            'lens_index': [float(lens_spec.lens_index)],
            'coatings_count': [len(lens_spec.coatings)],
            'external_procurement': [1 if order.external_procurement else 0],
            'loopback_count': [order.loopback_count],
            'dwell_hours': [dwell_hours]
        }

        df = pd.DataFrame(features)
        
        # predict_proba returns [[prob_0, prob_1]]
        probability = self.model.predict_proba(df)[0][1]
        return float(probability)

predictor = TATPredictor()

def update_order_risk(order: Order, lens_spec: LensSpec, probability_threshold: float = 0.6) -> bool:
    """
    Evaluates the breach probability and updates the order's risk level.
    Returns True if the risk level changed.
    """
    prob = predictor.predict_risk(order, lens_spec)
    
    new_risk = RiskLevel.ON_TRACK
    if prob >= probability_threshold:
        new_risk = RiskLevel.AT_RISK
        
    # Hard override if SLA is already breached by time
    if order.sla_target_at and datetime.now(timezone.utc) > order.sla_target_at:
        new_risk = RiskLevel.BREACHED

    if order.risk_level != new_risk:
        order.risk_level = new_risk
        return True
        
    return False
