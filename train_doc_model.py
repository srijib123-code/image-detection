import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Extract numerical features: [ELA_score, Aspect_Ratio, Text_Count, Confidence, Meta_Flag]
# In production, replace dummy X/y with features extracted from your dataset folder
X_dummy = np.array([
    [12.5, 1.41, 45, 0.92, 0.0],  # Genuine document sample
    [85.2, 1.33, 12, 0.45, 1.0],  # Fake document sample
    [10.1, 1.40, 50, 0.89, 0.0],  # Genuine document sample
    [92.4, 1.50, 8, 0.30, 1.0],  # Fake document sample
])
y_dummy = np.array([0, 1, 0, 1])  # 0 = Genuine, 1 = Fake/Tampered

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_dummy, y_dummy)

joblib.dump(model, "doc_fraud_model.pkl")
print("Data-driven document model saved as doc_fraud_model.pkl")