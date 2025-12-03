from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
from . import database as db

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Allow frontend to call the API

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ---------- Models ----------

class CartItem(BaseModel):
    id: str
    user_id: str
    product_id: str
    quantity: int

class Order(BaseModel):
    id: str
    user_id: str
    items: List[CartItem]
    status: str
    total: Optional[float] = None

class Product(BaseModel):
    id: str
    name: str
    category: str
    price: float

class CartItem(BaseModel):
    id: str
    user_id: str
    product_id: str
    quantity: int

class Order(BaseModel):
    id: str
    user_id: str
    items: List[CartItem]
    status: str

# ---------- HTML homepage ----------

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")


# ---------- /health ----------

@app.get("/health")
def health():
    # simple check: try reading 1 product; if it fails, error
    try:
        products = db.get_all_products()
        return {"status": "ok", "product_count": len(products)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ---------- Products ----------

@app.get("/api/v1/products", response_model=List[Product])
def list_products(category: Optional[str] = Query(default=None, alias="category")):
    """
    GET /api/v1/products
    GET /api/v1/products?category={cat}
    """
    items = db.get_all_products(category=category)
    return items

@app.get("/api/v1/products/{id}", response_model=Product)
def get_product(id: str):
    item = db.get_product_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return item

@app.get("/api/v1/categories", response_model=List[str])
def list_categories():
    return db.get_categories()

# ---------- Cart ----------

@app.get("/api/v1/cart")
async def get_cart(user_id: str = "demo"):
    return db.get_cart_items(user_id)

@app.post("/api/v1/cart/items", response_model=CartItem)
async def add_cart_item(item: CartItem):
    updated = db.add_or_increment_cart_item(
        user_id=item.user_id,
        product_id=item.product_id,
        quantity=item.quantity or 1,
    )
    return updated

@app.delete("/api/v1/cart/items/{id}")
def remove_cart_item(id: str, user_id: str = "demo"):
    ok = db.delete_cart_item(item_id=id, user_id=user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"status": "deleted"}

@app.delete("/api/v1/cart/items/{item_id}")
async def delete_cart_item_endpoint(item_id: str, user_id: str = "demo"):
    ok = db.delete_cart_item(item_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"status": "deleted"}


@app.delete("/api/v1/cart/items/{item_id}")
async def delete_cart_item(item_id: str, user_id: str = "demo"):
    try:
        db.delete_cart_item(item_id, user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"status": "deleted"}
# ---------- Orders ----------

@app.post("/api/v1/orders", response_model=Order)
async def create_order(order: Order):
    # calculate total from products in Cosmos
    total = 0.0
    for item in order.items:
        product = db.get_product_by_id(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        price = product["price"]
        total += price * item.quantity

    order_dict = order.dict()
    order_dict["total"] = total

    created = db.create_order(order_dict)
    db.clear_cart_for_user(order.user_id)
    return created
    
@app.get("/api/v1/orders", response_model=List[Order])
def list_orders(user_id: str = "demo"):
    items = db.get_orders(user_id=user_id)
    return items

