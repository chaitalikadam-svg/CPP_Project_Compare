from .normalizers import normalize_features, normalize_competitor_prices
from .db_client import fetch_products_by_ids
import requests

class ProductComparator:
    def __init__(self, product_ids=None, table_name="ElectronicItem", region="us-east-1"):
        """product_ids: list of product IDs to fetch from DynamoDB"""
        if product_ids:
            self.products = fetch_products_by_ids(table_name, product_ids, region)
        else:
            self.products = []
    
    def compare_features(self):
        """Compare all attributes across products, including merged features."""
        all_keys = set()
        for product in self.products:
            all_keys.update(product.keys())

        rows = []
        for key in sorted(all_keys):
            row = {"attribute": key, "values": []}
            for product in self.products:
                row["values"].append(product.get(key, "N/A"))
            rows.append(row)
        return rows
    
    def competitor_prices(self):
        """Fetch competitor prices for each product."""
        data = {}
        for product in self.products:
            query = product.get("name")
            raw = fetch_google_shopping(query)
            data[product["productid"]] = normalize_competitor_prices(raw)
        return data
        
        
def fetch_google_shopping(query: str) -> dict:
        return {
            "error": f"No competitor API configured. Cannot fetch results for query: {query}"
        }