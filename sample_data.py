#!/usr/bin/env python3
"""
Sample data script to populate the Kawaii Anime Shop database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / 'backend' / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Sample anime series for filtering
ANIME_SERIES = [
    "Naruto", "One Piece", "Dragon Ball", "Attack on Titan", "My Hero Academia",
    "Demon Slayer", "Jujutsu Kaisen", "Tokyo Ghoul", "Death Note", "Bleach",
    "Hunter x Hunter", "Fullmetal Alchemist", "One Punch Man", "Mob Psycho 100",
    "Assassination Classroom", "Haikyuu", "Kuroko no Basketball", "Food Wars",
    "Pokemon", "Digimon", "Sailor Moon", "Cardcaptor Sakura", "Evangelion",
    "Cowboy Bebop", "Studio Ghibli", "Your Name", "Weathering With You",
    "Violet Evergarden", "Kimetsu no Yaiba", "Fire Force", "Dr. Stone"
]

# Sample product images
PLUSH_IMAGES = [
    "https://images.unsplash.com/photo-1571757767119-68b8dbed8c97",
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96",
    "https://images.pexels.com/photos/6249454/pexels-photo-6249454.jpeg"
]

TSHIRT_IMAGES = [
    "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab",
    "https://images.unsplash.com/photo-1576566588028-4147f3842f27",
    "https://images.unsplash.com/photo-1503341338985-95b5b3070d1b"
]

FIGURE_IMAGES = [
    "https://images.unsplash.com/photo-1610496975819-707150c4c369",
    "https://images.pexels.com/photos/6249454/pexels-photo-6249454.jpeg",
    "https://images.unsplash.com/photo-1571757767119-68b8dbed8c97"
]

async def create_sample_products():
    """Create sample products for all categories"""
    
    products = []
    
    # Create Plushes (50 products for demo)
    for i in range(50):
        series = ANIME_SERIES[i % len(ANIME_SERIES)]
        product = {
            "id": str(uuid.uuid4()),
            "name": f"{series} Plush Character {i+1}",
            "description": f"Super soft and cuddly {series} character plush. Perfect for fans of the series!",
            "category": "plushes",
            "subcategory": None,
            "images": PLUSH_IMAGES[:2],
            "price": round(15.99 + (i % 20) * 2.5, 2),
            "stock": 10 + (i % 50),
            "dimensions": f"{8 + (i % 5)} inches tall",
            "material": "Premium polyester filling with soft cotton exterior",
            "anime_series": series,
            "sizes": [],
            "colors": ["Original", "Pink", "Blue", "White"][:(i % 4) + 1],
            "fit_type": None,
            "reviews": [],
            "popularity_score": i % 100,
            "created_at": datetime.now(timezone.utc)
        }
        products.append(product)
    
    # Create T-shirts (80 products for demo)
    for i in range(80):
        series = ANIME_SERIES[i % len(ANIME_SERIES)]
        product = {
            "id": str(uuid.uuid4()),
            "name": f"{series} Logo T-Shirt {i+1}",
            "description": f"Official {series} themed t-shirt with high-quality print. Comfortable cotton blend.",
            "category": "t-shirts",
            "subcategory": None,
            "images": TSHIRT_IMAGES,
            "price": round(19.99 + (i % 25) * 1.5, 2),
            "stock": 15 + (i % 40),
            "dimensions": None,
            "material": "100% cotton premium quality",
            "anime_series": series,
            "sizes": ["S", "M", "L", "XL"],
            "colors": ["Black", "White", "Gray", "Navy", "Red", "Pink"][:(i % 6) + 1],
            "fit_type": "oversized" if i % 2 == 0 else "regular",
            "reviews": [],
            "popularity_score": i % 100,
            "created_at": datetime.now(timezone.utc)
        }
        products.append(product)
    
    # Create Premium Action Figures (60 products for demo)
    for i in range(60):
        series = ANIME_SERIES[i % len(ANIME_SERIES)]
        product = {
            "id": str(uuid.uuid4()),
            "name": f"{series} Premium Action Figure {i+1}",
            "description": f"High-quality collectible {series} action figure with incredible detail and articulation.",
            "category": "action-figures",
            "subcategory": "premium",
            "images": FIGURE_IMAGES,
            "price": round(49.99 + (i % 30) * 5.0, 2),
            "stock": 5 + (i % 20),
            "dimensions": f"{6 + (i % 6)} inches tall",
            "material": "High-grade PVC with metal joints",
            "anime_series": series,
            "sizes": [],
            "colors": [],
            "fit_type": None,
            "reviews": [],
            "popularity_score": i % 100,
            "created_at": datetime.now(timezone.utc)
        }
        products.append(product)
    
    # Create Sustainable Action Figures (40 products for demo)
    for i in range(40):
        series = ANIME_SERIES[i % len(ANIME_SERIES)]
        product = {
            "id": str(uuid.uuid4()),
            "name": f"{series} Eco-Friendly Figure {i+1}",
            "description": f"Sustainable {series} action figure made with eco-friendly materials and recyclable packaging.",
            "category": "action-figures",
            "subcategory": "sustainable",
            "images": FIGURE_IMAGES[:2],
            "price": round(35.99 + (i % 20) * 3.0, 2),
            "stock": 8 + (i % 25),
            "dimensions": f"{5 + (i % 4)} inches tall",
            "material": "Recycled plastic with biodegradable paint",
            "anime_series": series,
            "sizes": [],
            "colors": [],
            "fit_type": None,
            "reviews": [],
            "popularity_score": i % 100,
            "created_at": datetime.now(timezone.utc)
        }
        products.append(product)
    
    # Insert all products
    await db.products.insert_many(products)
    print(f"Created {len(products)} sample products")

async def create_sample_coupons():
    """Create sample coupon codes"""
    
    coupons = [
        {
            "id": str(uuid.uuid4()),
            "code": "WELCOME10",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "usage_limit": 100,
            "used_count": 0,
            "active": True,
            "expires_at": None,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "code": "ANIME50",
            "discount_type": "fixed",
            "discount_value": 50.0,
            "usage_limit": 50,
            "used_count": 0,
            "active": True,
            "expires_at": None,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "code": "KAWAII15",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "usage_limit": 200,
            "used_count": 0,
            "active": True,
            "expires_at": None,
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    await db.coupons.insert_many(coupons)
    print(f"Created {len(coupons)} sample coupons")

async def main():
    """Main function to populate database"""
    
    print("Populating Kawaii Anime Shop database...")
    
    # Clear existing products and coupons
    await db.products.delete_many({})
    await db.coupons.delete_many({})
    print("Cleared existing data")
    
    # Create sample data
    await create_sample_products()
    await create_sample_coupons()
    
    print("Database population completed!")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(main())