# comparator_pkg/db_client.py
import boto3
from boto3.dynamodb.conditions import Attr

def fetch_products_by_ids(table_name: str, ids: list, region="us-east-1"):
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    products = []
    for pid in ids:
        resp = table.get_item(Key={"productid": pid})
        if "Item" in resp:
            products.append(resp["Item"])
    return products

def fetch_products_by_category(table_name: str, category: str, region="us-east-1"):
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    resp = table.scan(FilterExpression=Attr("category").eq(category))
    return resp.get("Items", [])