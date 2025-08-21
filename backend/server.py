from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import razorpay
import httpx
from urllib.parse import quote

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Kawaii Anime Shop API")
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# API Keys placeholders - user will fill these
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'your_razorpay_key_id_here')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'your_razorpay_key_secret_here')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'your_google_client_id_here')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'your_google_client_secret_here')

# Initialize Razorpay client (if keys are provided)
razor_client = None
if RAZORPAY_KEY_ID != 'your_razorpay_key_id_here':
    razor_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    addresses: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str  # plushes, t-shirts, action-figures
    subcategory: Optional[str] = None  # premium, sustainable (for action figures)
    images: List[str] = []
    price: float
    stock: int = 0
    dimensions: Optional[str] = None
    material: Optional[str] = None
    anime_series: Optional[str] = None
    sizes: List[str] = []  # For t-shirts: S, M, L, XL
    colors: List[str] = []  # For t-shirts
    fit_type: Optional[str] = None  # oversized, regular (for t-shirts)
    reviews: List[Dict[str, Any]] = []
    popularity_score: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    subcategory: Optional[str] = None
    images: List[str] = []
    price: float
    stock: int = 0
    dimensions: Optional[str] = None
    material: Optional[str] = None
    anime_series: Optional[str] = None
    sizes: List[str] = []
    colors: List[str] = []
    fit_type: Optional[str] = None

class CartItem(BaseModel):
    product_id: str
    quantity: int
    selected_size: Optional[str] = None
    selected_color: Optional[str] = None
    selected_fit: Optional[str] = None

class Cart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = []
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem]
    total_amount: float
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    payment_status: str = "pending"  # pending, paid, failed
    status: str = "created"  # created, processing, shipped, delivered, cancelled
    shipping_address: Dict[str, Any]
    coupon_code: Optional[str] = None
    discount_amount: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OrderCreate(BaseModel):
    items: List[CartItem]
    shipping_address: Dict[str, Any]
    coupon_code: Optional[str] = None

class Coupon(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    discount_type: str  # percentage, fixed
    discount_value: float
    usage_limit: int = 100
    used_count: int = 0
    active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CouponCreate(BaseModel):
    code: str
    discount_type: str
    discount_value: float
    usage_limit: int = 100
    expires_at: Optional[datetime] = None

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Authentication helper
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    if not credentials:
        return None
    
    # Check session token in database
    session = await db.sessions.find_one({
        "session_token": credentials.credentials,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not session:
        return None
    
    user = await db.users.find_one({"id": session["user_id"]})
    return User(**user) if user else None

async def require_auth(user: User = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

# Routes

# Health check
@api_router.get("/")
async def root():
    return {"message": "Kawaii Anime Shop API is running!"}

# Authentication routes
@api_router.post("/auth/google")
async def google_auth(request: Request):
    """Handle Google OAuth callback"""
    data = await request.json()
    
    if GOOGLE_CLIENT_ID == 'your_google_client_id_here':
        return {"message": "Please configure Google OAuth credentials"}
    
    # Exchange authorization code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": data.get("code"),
                "grant_type": "authorization_code",
                "redirect_uri": data.get("redirect_uri", ""),
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        tokens = token_response.json()
        
        # Get user info from Google
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = user_response.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_info["email"]})
    
    if not existing_user:
        # Create new user
        user_data = UserCreate(
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture")
        )
        user = User(**user_data.dict())
        await db.users.insert_one(user.dict())
    else:
        user = User(**existing_user)
    
    # Create session
    session_token = str(uuid.uuid4())
    session = Session(
        user_id=user.id,
        session_token=session_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    await db.sessions.insert_one(session.dict())
    
    return {
        "user": user,
        "session_token": session_token,
        "expires_at": session.expires_at
    }

@api_router.post("/auth/logout")
async def logout(user: User = Depends(require_auth)):
    """Logout user and invalidate session"""
    await db.sessions.delete_many({"user_id": user.id})
    return {"message": "Logged out successfully"}

# Product routes
@api_router.get("/products", response_model=List[Product])
async def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    anime_series: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 20
):
    """Get products with filtering and pagination"""
    query = {}
    
    if category:
        query["category"] = category
    if subcategory:
        query["subcategory"] = subcategory
    if anime_series:
        query["anime_series"] = {"$regex": anime_series, "$options": "i"}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"anime_series": {"$regex": search, "$options": "i"}}
        ]
    
    # Sorting
    sort_direction = 1 if sort_order == "asc" else -1
    if sort_by == "price_low":
        sort_by = "price"
        sort_direction = 1
    elif sort_by == "price_high":
        sort_by = "price" 
        sort_direction = -1
    elif sort_by == "popularity":
        sort_by = "popularity_score"
        sort_direction = -1
    
    skip = (page - 1) * per_page
    
    products = await db.products.find(query).sort(sort_by, sort_direction).skip(skip).limit(per_page).to_list(per_page)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get single product by ID"""
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, user: User = Depends(require_auth)):
    """Create new product (admin only)"""
    product = Product(**product_data.dict())
    await db.products.insert_one(product.dict())
    return product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: ProductCreate, user: User = Depends(require_auth)):
    """Update product (admin only)"""
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": product_data.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    updated_product = await db.products.find_one({"id": product_id})
    return Product(**updated_product)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: User = Depends(require_auth)):
    """Delete product (admin only)"""
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# Cart routes
@api_router.get("/cart", response_model=Cart)
async def get_cart(user: User = Depends(require_auth)):
    """Get user's cart"""
    cart = await db.carts.find_one({"user_id": user.id})
    if not cart:
        cart = Cart(user_id=user.id)
        await db.carts.insert_one(cart.dict())
    return Cart(**cart)

@api_router.post("/cart/add")
async def add_to_cart(item: CartItem, user: User = Depends(require_auth)):
    """Add item to cart"""
    cart = await db.carts.find_one({"user_id": user.id})
    if not cart:
        cart = Cart(user_id=user.id, items=[item])
        await db.carts.insert_one(cart.dict())
    else:
        # Check if item already exists in cart
        existing_item = None
        for i, cart_item in enumerate(cart["items"]):
            if (cart_item["product_id"] == item.product_id and 
                cart_item.get("selected_size") == item.selected_size and
                cart_item.get("selected_color") == item.selected_color):
                existing_item = i
                break
        
        if existing_item is not None:
            cart["items"][existing_item]["quantity"] += item.quantity
        else:
            cart["items"].append(item.dict())
        
        await db.carts.update_one(
            {"user_id": user.id},
            {"$set": {"items": cart["items"], "updated_at": datetime.now(timezone.utc)}}
        )
    
    return {"message": "Item added to cart"}

@api_router.delete("/cart/{product_id}")
async def remove_from_cart(product_id: str, user: User = Depends(require_auth)):
    """Remove item from cart"""
    await db.carts.update_one(
        {"user_id": user.id},
        {"$pull": {"items": {"product_id": product_id}}}
    )
    return {"message": "Item removed from cart"}

# Order routes
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate, user: User = Depends(require_auth)):
    """Create new order"""
    # Calculate total amount
    total_amount = 0
    for item in order_data.items:
        product = await db.products.find_one({"id": item.product_id})
        if product:
            total_amount += product["price"] * item.quantity
    
    # Apply coupon if provided
    discount_amount = 0
    if order_data.coupon_code:
        coupon = await db.coupons.find_one({
            "code": order_data.coupon_code,
            "active": True,
            "used_count": {"$lt": coupon.usage_limit}
        })
        if coupon and (not coupon.get("expires_at") or coupon["expires_at"] > datetime.now(timezone.utc)):
            if coupon["discount_type"] == "percentage":
                discount_amount = total_amount * (coupon["discount_value"] / 100)
            else:
                discount_amount = coupon["discount_value"]
            
            # Update coupon usage
            await db.coupons.update_one(
                {"code": order_data.coupon_code},
                {"$inc": {"used_count": 1}}
            )
    
    final_amount = total_amount - discount_amount
    
    # Create order
    order = Order(
        user_id=user.id,
        items=order_data.items,
        total_amount=final_amount,
        shipping_address=order_data.shipping_address,
        coupon_code=order_data.coupon_code,
        discount_amount=discount_amount
    )
    
    # Create Razorpay order if client is available
    if razor_client:
        razor_order = razor_client.order.create({
            "amount": int(final_amount * 100),  # Convert to paise
            "currency": "INR",
            "payment_capture": 1
        })
        order.razorpay_order_id = razor_order["id"]
    
    await db.orders.insert_one(order.dict())
    
    # Clear cart
    await db.carts.update_one(
        {"user_id": user.id},
        {"$set": {"items": []}}
    )
    
    return order

@api_router.get("/orders", response_model=List[Order])
async def get_orders(user: User = Depends(require_auth)):
    """Get user's orders"""
    orders = await db.orders.find({"user_id": user.id}).sort("created_at", -1).to_list(100)
    return [Order(**order) for order in orders]

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, user: User = Depends(require_auth)):
    """Get specific order"""
    order = await db.orders.find_one({"id": order_id, "user_id": user.id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order(**order)

# Payment routes
@api_router.post("/payment/verify")
async def verify_payment(request: Request, user: User = Depends(require_auth)):
    """Verify Razorpay payment"""
    data = await request.json()
    
    if not razor_client:
        raise HTTPException(status_code=400, detail="Payment gateway not configured")
    
    try:
        # Verify payment signature
        razor_client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        
        # Update order status
        await db.orders.update_one(
            {"razorpay_order_id": data['razorpay_order_id']},
            {
                "$set": {
                    "razorpay_payment_id": data['razorpay_payment_id'],
                    "payment_status": "paid",
                    "status": "processing"
                }
            }
        )
        
        # Update product stock
        order = await db.orders.find_one({"razorpay_order_id": data['razorpay_order_id']})
        if order:
            for item in order["items"]:
                await db.products.update_one(
                    {"id": item["product_id"]},
                    {"$inc": {"stock": -item["quantity"]}}
                )
        
        return {"status": "success", "message": "Payment verified"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Coupon routes
@api_router.post("/coupons", response_model=Coupon)
async def create_coupon(coupon_data: CouponCreate, user: User = Depends(require_auth)):
    """Create coupon (admin only)"""
    coupon = Coupon(**coupon_data.dict())
    await db.coupons.insert_one(coupon.dict())
    return coupon

@api_router.post("/coupons/validate/{code}")
async def validate_coupon(code: str, user: User = Depends(require_auth)):
    """Validate coupon code"""
    coupon = await db.coupons.find_one({
        "code": code,
        "active": True,
        "used_count": {"$lt": "$usage_limit"}
    })
    
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon code")
    
    if coupon.get("expires_at") and coupon["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Coupon has expired")
    
    return {"valid": True, "coupon": Coupon(**coupon)}

# Analytics routes
@api_router.get("/analytics/dashboard")
async def get_analytics(user: User = Depends(require_auth)):
    """Get admin dashboard analytics"""
    
    # Total orders
    total_orders = await db.orders.count_documents({})
    
    # Total revenue  
    revenue_result = await db.orders.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
    ]).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Total products
    total_products = await db.products.count_documents({})
    
    # Total users
    total_users = await db.users.count_documents({})
    
    # Recent orders
    recent_orders = await db.orders.find().sort("created_at", -1).limit(5).to_list(5)
    
    # Low stock products
    low_stock = await db.products.find({"stock": {"$lt": 10}}).limit(5).to_list(5)
    
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_products": total_products,
        "total_users": total_users,
        "recent_orders": [Order(**order) for order in recent_orders],
        "low_stock_products": [Product(**product) for product in low_stock]
    }

# User profile routes
@api_router.get("/profile", response_model=User)
async def get_profile(user: User = Depends(require_auth)):
    """Get user profile"""
    return user

@api_router.put("/profile", response_model=User)
async def update_profile(profile_data: dict, user: User = Depends(require_auth)):
    """Update user profile"""
    await db.users.update_one(
        {"id": user.id},
        {"$set": profile_data}
    )
    updated_user = await db.users.find_one({"id": user.id})
    return User(**updated_user)

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()