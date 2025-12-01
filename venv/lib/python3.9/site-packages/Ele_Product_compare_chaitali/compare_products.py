from .normalizers import normalize_features
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
        """Compare all attributes across products."""
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
    

        
