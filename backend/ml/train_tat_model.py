"""
OptiFlow — TAT (Turnaround Time) Prediction Model Trainer
Generates synthetic historical order data and trains a Random Forest model
to predict the likelihood of an SLA breach.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def generate_synthetic_data(num_samples: int = 2000) -> pd.DataFrame:
    """
    Generates synthetic historical data for eyewear orders.
    Features:
      - lens_type: Single Vision, Bifocal, Progressive
      - lens_index: 1.56, 1.61, 1.67
      - coatings_count: 0, 1, 2, 3
      - external_procurement: 0 or 1
      - loopback_count: Number of times it failed QC
      - current_stage_dwell_hours: How long it has sat in the current stage
    Target:
      - breached_sla: 1 (Breached), 0 (On Track)
    """
    np.random.seed(42)
    
    lens_types = np.random.choice(['single_vision', 'bifocal', 'progressive'], size=num_samples, p=[0.6, 0.2, 0.2])
    lens_indices = np.random.choice([1.56, 1.61, 1.67], size=num_samples, p=[0.4, 0.4, 0.2])
    coatings_count = np.random.randint(0, 4, size=num_samples)
    external_procurement = np.random.binomial(1, 0.3, size=num_samples)
    loopback_count = np.random.poisson(0.5, size=num_samples)
    dwell_hours = np.random.exponential(12, size=num_samples)
    
    # Calculate probability of breach based on logic
    # Progress lens + external + loopbacks = high risk
    logits = -3.0 \
           + (lens_types == 'progressive') * 1.5 \
           + external_procurement * 2.0 \
           + loopback_count * 1.8 \
           + coatings_count * 0.3 \
           + (dwell_hours > 24) * 2.5
           
    probabilities = 1 / (1 + np.exp(-logits))
    breached_sla = np.random.binomial(1, probabilities)
    
    return pd.DataFrame({
        'lens_type': lens_types,
        'lens_index': lens_indices,
        'coatings_count': coatings_count,
        'external_procurement': external_procurement,
        'loopback_count': loopback_count,
        'dwell_hours': dwell_hours,
        'breached_sla': breached_sla
    })

def train_and_save_model():
    print("Generating synthetic data...")
    df = generate_synthetic_data(5000)
    
    X = df.drop('breached_sla', axis=1)
    y = df['breached_sla']
    
    print(f"Dataset generated. Shape: {X.shape}, Breaches: {y.sum()}")
    
    # Preprocessing
    categorical_features = ['lens_type']
    numeric_features = ['lens_index', 'coatings_count', 'external_procurement', 'loopback_count', 'dwell_hours']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
        
    # Pipeline
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42))
    ])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Classifier...")
    model.fit(X_train, y_train)
    
    score = model.score(X_test, y_test)
    print(f"Model accuracy on test set: {score:.3f}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    
    model_path = os.path.join(os.path.dirname(__file__), 'tat_model.joblib')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_and_save_model()
