import requests
from django.conf import settings

#API to fetch competitor data 
def fetch_google_shopping(query):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping_light",
        "q": query,
        "location": "United Kingdom", 
        "google_domain": "google.com",
        "hl": "en",
        "gl": "ie",
        "api_key": settings.SERPAPI_KEY,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def normalize_products(data):
    products = []
    for item in data.get("shopping_results", []):
        products.append({
            "title": item.get("title"),
            "price": item.get("price"),
            "source": item.get("source"),
            "rating": item.get("rating"),
        })
    return products