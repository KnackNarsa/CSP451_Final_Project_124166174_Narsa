import os
from dotenv import load_dotenv
from typing import List, Optional
from uuid import uuid4
from azure.cosmos import CosmosClient, PartitionKey, exceptions

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB_NAME = "cloudmart"

#if not COSMOS_ENDPOINT or not COSMOS_KEY:
#    raise RuntimeError("COSMOS_ENDPOINT and COSMOS_KEY must be set as env vars")

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
db = client.get_database_client(COSMOS_DB_NAME)

product_container = db.get_container_client("product")
cart_container = db.get_container_client("cart")
orders_container = db.get_container_client("orders")

# ---------- Product helpers ----------

def get_all_products(category: Optional[str] = None) -> List[dict]:
    if category:
        query = "SELECT * FROM c WHERE c.category = @cat"
        params = [{"name": "@cat", "value": category}]
        items = list(product_container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True
        ))
    else:
        items = list(product_container.read_all_items())
    return items

def get_product_by_id(product_id: str) -> Optional[dict]:
    query = "SELECT * FROM c WHERE c.id = @id"
    params = [{"name": "@id", "value": product_id}]
    items = list(product_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True
    ))
    return items[0] if items else None

def get_categories() -> List[str]:
    query = "SELECT DISTINCT c.category FROM c"
    items = list(product_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    return [i["category"] for i in items]


def get_product_by_id(product_id: str) -> Optional[dict]:
    query = "SELECT * FROM c WHERE c.id = @id"
    params = [{"name": "@id", "value": product_id}]
    items = list(product_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
    ))
    return items[0] if items else None



def get_product_price(product_id: str) -> float:
    query = "SELECT c.price FROM c WHERE c.id = @id"
    params = [{"name": "@id", "value": product_id}]
    results = list(product_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True
    ))
    if not results:
        raise ValueError(f"Product {product_id} not found")
    return results[0]["price"]

# ---------- Cart helpers ----------

def get_cart_items(user_id: str) -> List[dict]:
    query = "SELECT * FROM c WHERE c.user_id = @uid"
    params = [{"name": "@uid", "value": user_id}]
    items = list(cart_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True
    ))
    return items

def add_cart_item(item: dict) -> dict:
    # item must have user_id as partition key
    created = cart_container.create_item(body=item)
    return created

def add_or_increment_cart_item(user_id: str, product_id: str, quantity: int = 1) -> dict:
    # Check if this user already has this product in their cart
    query = "SELECT * FROM c WHERE c.user_id = @uid AND c.product_id = @pid"
    params = [
        {"name": "@uid", "value": user_id},
        {"name": "@pid", "value": product_id},
    ]
    existing = list(cart_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
    ))

    if existing:
        doc = existing[0]
        doc["quantity"] = doc.get("quantity", 0) + quantity
        cart_container.replace_item(doc, doc)
        return doc
    else:
        new_item = {
            "id": str(uuid4()),
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
        }
        cart_container.create_item(body=new_item)
        return new_item

def delete_cart_item(item_id: str, user_id: str) -> bool:
    try:
        cart_container.delete_item(item=item_id, partition_key=user_id)
        return True
    except exceptions.CosmosResourceNotFoundError:
        return False

# ---------- Order helpers ----------

def clear_cart_for_user(user_id: str) -> None:
    query = "SELECT c.id FROM c WHERE c.user_id = @uid"
    params = [{"name": "@uid", "value": user_id}]

    items = cart_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
    )

    for item in items:
        cart_container.delete_item(item["id"], partition_key=user_id)

def create_order(order: dict) -> dict:
    return orders_container.create_item(body=order)

def get_orders(user_id: str) -> List[dict]:
    query = "SELECT * FROM c WHERE c.user_id = @uid"
    params = [{"name": "@uid", "value": user_id}]
    items = list(orders_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True
    ))
    return items
