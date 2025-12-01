def normalize_features(features: dict) -> dict:
    #Standardize feature into keys and values
    if not isinstance(features, dict):
        return {}
    return {str(k).strip(): str(v).strip() for k, v in features.items()}