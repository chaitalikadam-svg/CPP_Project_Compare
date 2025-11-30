import boto3
from boto3.dynamodb.conditions import Key

def normalize_product(item: dict) -> dict:
    def flatten(value):
        if isinstance(value, dict) and len(value) == 1 and list(value.keys())[0] in ["S", "N", "BOOL"]:
            return list(value.values())[0]
        elif isinstance(value, dict):
            return {k: flatten(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [flatten(v) for v in value]
        else:
            return value

    flat = flatten(item)

    if "features" in flat and isinstance(flat["features"], dict):
        flat.update(flat["features"])
        del flat["features"]

    return flat

def fetch_products_by_ids(table_name: str, ids: list, region="us-east-1"):
    dynamodb_client = boto3.client("dynamodb", region_name=region)
    keys = [{"category": {"S": category}, "productid": {"S": pid}} for category, pid in ids]
    response = dynamodb_client.batch_get_item(RequestItems={table_name: {"Keys": keys}})
    items = response["Responses"].get(table_name, [])
    return [normalize_product(item) for item in items]
    

def fetch_products_by_category(table_name: str, category: str, region="us-east-1"):
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    resp = table.query(KeyConditionExpression=Key("category").eq(category))
    items = resp.get("Items", [])
    return [normalize_product(item) for item in items]