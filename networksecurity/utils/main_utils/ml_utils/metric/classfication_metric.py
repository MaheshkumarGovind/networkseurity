from networksecurity.entity.artifact_entity import ClassificationMetricArtifact
from networksecurity.exception.exception import NetworkSecurityException
from sklearn.metrics import f1_score, precision_score, recall_score
import sys

def get_classification_score(y_true, y_pred) -> ClassificationMetricArtifact:
    try:
        # **FIX 1: Set pos_label to match your string labels ('attack' = positive class)**
        pos_label = 'attack'  # Swap to 'normal' if that's your positive class instead
        
        # **FIX 2: Add pos_label and zero_division to all metrics**
        model_f1_score = f1_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
        model_recall_score = recall_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
        model_precision_score = precision_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
        
        classification_metric = ClassificationMetricArtifact(
            f1_score=model_f1_score,
            precision_score=model_precision_score,
            recall_score=model_recall_score
        )
        return classification_metric
    except Exception as e:
        raise NetworkSecurityException(e, sys)