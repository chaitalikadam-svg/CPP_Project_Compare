
def normalize_features(features: dict) -> dict:
    """Standardize feature keys and values."""
    if not isinstance(features, dict):
        return {}
    return {str(k).strip(): str(v).strip() for k, v in features.items()}

def normalize_competitor_prices(raw: dict) -> list:
    """Extract shopping results into a clean list of dicts."""
    items = []
    for item in raw.get("shopping_results", []):
        items.append({
            "title": item.get("title", "No title"),
            "price": item.get("price", "N/A"),
            "source": item.get("source", "Unknown"),
            "link": item.get("link", "#"),
        })
    return items