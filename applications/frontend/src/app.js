// Change this if your backend runs elsewhere
const API_BASE = "http://localhost:8000";

const productsDiv = document.getElementById("products");
const cartDiv = document.getElementById("cart");
const cartTotalSpan = document.getElementById("cartTotal");
const categorySelect = document.getElementById("categorySelect");
const filterBtn = document.getElementById("filterBtn");
const placeOrderBtn = document.getElementById("placeOrderBtn");
const orderMessageDiv = document.getElementById("orderMessage")

// cache products so we can look up name/price for cart
let productsById = {};

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return await res.json();
}

async function loadCategories() {
  const categories = await fetchJSON(`${API_BASE}/api/v1/categories`);
  categories.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    categorySelect.appendChild(opt);
  });
}

async function loadProducts(category = "") {
  const products = await fetchJSON(`${API_BASE}/api/v1/products`);

  // refresh the global map of ALL products
  allProductsById = {};
  products.forEach(p => {
    allProductsById[p.id] = p;
  });

  const toShow = category
    ? products.filter(p => p.category === category)
    : products;

  productsDiv.innerHTML = "";
  
  toShow.forEach(p => {
    const div = document.createElement("div");
    div.className = "product";
    div.innerHTML = `
      <strong>${p.name}</strong><br/>
      Category: ${p.category}<br/>
      Price: $${p.price.toFixed(2)}<br/>
      <button data-id="${p.id}">Add to Cart</button>
    `;
    const btn = div.querySelector("button");
    btn.addEventListener("click", () => addToCart(p.id));
    productsDiv.appendChild(div);
  });
}

async function loadCart() {
  const items = await fetchJSON(`${API_BASE}/api/v1/cart`);
  cartDiv.innerHTML = "";
  let total = 0;

  items.forEach(item => {
    const product = allProductsById[item.product_id];
    const price = product ? product.price : 0;
    const lineTotal = price * item.quantity;
    total += lineTotal;

    const div = document.createElement("div");
    div.className = "cart-item";
    div.innerHTML = `
      Product: ${product ? product.name : item.product_id}<br/>
      Quantity: ${item.quantity}<br/>
      Unit Price: $${price.toFixed(2)}<br/>
      Line Total: $${lineTotal.toFixed(2)}<br/>
      <button data-id="${item.id}">Remove</button>
    `;

    const removeBtn = div.querySelector("button");
    removeBtn.addEventListener("click", () => removeFromCart(item.id));

    cartDiv.appendChild(div);
  });

  cartTotalSpan.textContent = total.toFixed(2);
}


async function addToCart(productId) {
  const quantity = 1; // simple demo: always add 1

  const payload = {
    id: `cart-${Date.now()}`,
    user_id: "demo",
    product_id: productId,
    quantity: quantity
  };

  await fetchJSON(`${API_BASE}/api/v1/cart/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  await loadCart();
}

async function removeFromCart(itemId) {
  try {
    await fetch(`${API_BASE}/api/v1/cart/items/${encodeURIComponent(itemId)}`, {
      method: "DELETE"
    });
    await loadCart();
  } catch (err) {
    console.error("Remove error:", err);
  }
}


async function placeOrder() {
  orderMessageDiv.textContent = "";

  // 1) Get cart items from API
  const items = await fetchJSON(`${API_BASE}/api/v1/cart`);

  if (!items.length) {
    orderMessageDiv.textContent = "Cart is empty. Add some products first.";
    return;
  }

  // 2) Build order payload
  const payload = {
    id: `order-${Date.now()}`,
    user_id: "demo",
    items: items,
    status: "confirmed"
  };

  let order;
  try {
    order = await fetchJSON(`${API_BASE}/api/v1/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch (err) {
    console.error("Order error:", err);
    orderMessageDiv.textContent = "Error placing order.";
    return;
  }
  await loadCart();
  console.log("Order response from API:", order);

  // 3) Decide what total to show
  let total = order.total;

  // Fallback: compute from cart if backend didn't send total
  if (total === undefined || total === null) {
    total = 0;
    items.forEach(item => {
      const product = allProductsById[item.product_id];
      const price = product ? product.price : 0;
      total += price * item.quantity;
    });
  }

  orderMessageDiv.innerHTML = `
    <strong>Order placed!</strong><br/>
    Order ID: ${order.id}<br/>
    Status: ${order.status}<br/>
    Total: $${total.toFixed(2)}
  `;
}


  // You *could* clear the cart here by DELETE-ing items, but not required for screenshots

// Wire up events
filterBtn.addEventListener("click", () => {
  const cat = categorySelect.value;
  loadProducts(cat).then(loadCart);
});

placeOrderBtn.addEventListener("click", () => {
  placeOrder().catch(err => {
    console.error(err);
    orderMessageDiv.textContent = "Error placing order.";
  });
});

// Initial load
(async function init() {
  try {
    await loadCategories();
    await loadProducts();
  } catch (err) {
    console.error("Init error:", err);
  }
})();
