#!/usr/bin/env python3
"""
Backend API Testing Script for Kawaii Anime Shop
Tests all backend API endpoints to ensure proper functionality
"""
import asyncio
import aiohttp
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / 'frontend' / '.env')

# Get backend URL from frontend environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name, success, message, data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "data": data
        })
    
    async def test_health_check(self):
        """Test the basic health check endpoint GET /api/"""
        try:
            async with self.session.get(f"{API_BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if "message" in data and "Kawaii Anime Shop API" in data["message"]:
                        self.log_test("Health Check", True, f"API is running - {data['message']}")
                        return True
                    else:
                        self.log_test("Health Check", False, f"Unexpected response: {data}")
                        return False
                else:
                    self.log_test("Health Check", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    async def test_products_endpoint(self):
        """Test the products API GET /api/products"""
        try:
            async with self.session.get(f"{API_BASE_URL}/products") as response:
                if response.status == 200:
                    products = await response.json()
                    if isinstance(products, list):
                        total_products = len(products)
                        if total_products > 0:
                            # Check if we have the expected 230 products (with pagination, we get first 20)
                            self.log_test("Products Endpoint", True, 
                                        f"Retrieved {total_products} products (first page)")
                            
                            # Verify product structure
                            sample_product = products[0]
                            required_fields = ['id', 'name', 'description', 'category', 'price', 'stock']
                            missing_fields = [field for field in required_fields if field not in sample_product]
                            
                            if not missing_fields:
                                self.log_test("Product Structure", True, "All required fields present")
                            else:
                                self.log_test("Product Structure", False, f"Missing fields: {missing_fields}")
                            
                            return True, products
                        else:
                            self.log_test("Products Endpoint", False, "No products found in response")
                            return False, []
                    else:
                        self.log_test("Products Endpoint", False, f"Expected list, got {type(products)}")
                        return False, []
                else:
                    self.log_test("Products Endpoint", False, f"HTTP {response.status}")
                    return False, []
        except Exception as e:
            self.log_test("Products Endpoint", False, f"Error: {str(e)}")
            return False, []
    
    async def test_products_filtering(self):
        """Test product filtering by category"""
        categories_to_test = ["plushes", "t-shirts", "action-figures"]
        
        for category in categories_to_test:
            try:
                async with self.session.get(f"{API_BASE_URL}/products?category={category}") as response:
                    if response.status == 200:
                        products = await response.json()
                        if isinstance(products, list) and len(products) > 0:
                            # Verify all products belong to the requested category
                            correct_category = all(product.get('category') == category for product in products)
                            if correct_category:
                                self.log_test(f"Filter by {category}", True, 
                                            f"Found {len(products)} {category} products")
                            else:
                                wrong_categories = [p.get('category') for p in products if p.get('category') != category]
                                self.log_test(f"Filter by {category}", False, 
                                            f"Found products with wrong categories: {set(wrong_categories)}")
                        else:
                            self.log_test(f"Filter by {category}", False, "No products found for this category")
                    else:
                        self.log_test(f"Filter by {category}", False, f"HTTP {response.status}")
            except Exception as e:
                self.log_test(f"Filter by {category}", False, f"Error: {str(e)}")
    
    async def test_subcategory_filtering(self):
        """Test action-figures subcategory filtering"""
        subcategories = ["premium", "sustainable"]
        
        for subcategory in subcategories:
            try:
                url = f"{API_BASE_URL}/products?category=action-figures&subcategory={subcategory}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        products = await response.json()
                        if isinstance(products, list) and len(products) > 0:
                            # Verify all products are action-figures with correct subcategory
                            correct_filter = all(
                                product.get('category') == 'action-figures' and 
                                product.get('subcategory') == subcategory 
                                for product in products
                            )
                            if correct_filter:
                                self.log_test(f"Filter {subcategory} action-figures", True, 
                                            f"Found {len(products)} {subcategory} action figures")
                            else:
                                self.log_test(f"Filter {subcategory} action-figures", False, 
                                            "Products don't match filter criteria")
                        else:
                            self.log_test(f"Filter {subcategory} action-figures", False, 
                                        f"No {subcategory} action figures found")
                    else:
                        self.log_test(f"Filter {subcategory} action-figures", False, f"HTTP {response.status}")
            except Exception as e:
                self.log_test(f"Filter {subcategory} action-figures", False, f"Error: {str(e)}")
    
    async def test_search_functionality(self):
        """Test search functionality with 'Naruto'"""
        search_term = "Naruto"
        try:
            async with self.session.get(f"{API_BASE_URL}/products?search={search_term}") as response:
                if response.status == 200:
                    products = await response.json()
                    if isinstance(products, list) and len(products) > 0:
                        # Verify search results contain the search term
                        valid_results = []
                        for product in products:
                            name = product.get('name', '').lower()
                            description = product.get('description', '').lower()
                            anime_series = product.get('anime_series', '').lower()
                            
                            if (search_term.lower() in name or 
                                search_term.lower() in description or 
                                search_term.lower() in anime_series):
                                valid_results.append(product)
                        
                        if len(valid_results) == len(products):
                            self.log_test("Search Functionality", True, 
                                        f"Found {len(products)} products matching '{search_term}'")
                        else:
                            self.log_test("Search Functionality", False, 
                                        f"Some results don't contain '{search_term}': {len(valid_results)}/{len(products)} valid")
                    else:
                        self.log_test("Search Functionality", False, f"No products found for search term '{search_term}'")
                else:
                    self.log_test("Search Functionality", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Search Functionality", False, f"Error: {str(e)}")
    
    async def test_database_product_count(self):
        """Test if database has expected number of products"""
        try:
            # Test with high per_page to get more products
            async with self.session.get(f"{API_BASE_URL}/products?per_page=250") as response:
                if response.status == 200:
                    products = await response.json()
                    total_count = len(products)
                    
                    if total_count == 230:
                        self.log_test("Database Product Count", True, f"Found expected 230 products")
                    else:
                        self.log_test("Database Product Count", False, 
                                    f"Expected 230 products, found {total_count}")
                    
                    # Break down by category
                    categories = {}
                    for product in products:
                        cat = product.get('category', 'unknown')
                        subcat = product.get('subcategory')
                        
                        if cat not in categories:
                            categories[cat] = {}
                        
                        if subcat:
                            key = f"{cat}-{subcat}"
                        else:
                            key = cat
                            
                        categories[cat][key] = categories[cat].get(key, 0) + 1
                    
                    # Expected counts: 50 plushes, 80 t-shirts, 60 premium action figures, 40 sustainable action figures
                    expected = {
                        'plushes': 50,
                        't-shirts': 80,
                        'action-figures': 100  # 60 premium + 40 sustainable
                    }
                    
                    for category, expected_count in expected.items():
                        actual_count = sum(categories.get(category, {}).values())
                        if actual_count == expected_count:
                            self.log_test(f"Category Count - {category}", True, 
                                        f"Found {actual_count} {category}")
                        else:
                            self.log_test(f"Category Count - {category}", False, 
                                        f"Expected {expected_count} {category}, found {actual_count}")
                    
                else:
                    self.log_test("Database Product Count", False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test("Database Product Count", False, f"Error: {str(e)}")
    
    async def test_individual_product_endpoint(self):
        """Test getting individual product by ID"""
        try:
            # First get a product ID
            async with self.session.get(f"{API_BASE_URL}/products?per_page=1") as response:
                if response.status == 200:
                    products = await response.json()
                    if products and len(products) > 0:
                        product_id = products[0]['id']
                        
                        # Test individual product endpoint
                        async with self.session.get(f"{API_BASE_URL}/products/{product_id}") as prod_response:
                            if prod_response.status == 200:
                                product = await prod_response.json()
                                if product.get('id') == product_id:
                                    self.log_test("Individual Product", True, 
                                                f"Successfully retrieved product {product_id}")
                                else:
                                    self.log_test("Individual Product", False, "Product ID mismatch")
                            else:
                                self.log_test("Individual Product", False, f"HTTP {prod_response.status}")
                    else:
                        self.log_test("Individual Product", False, "No products available to test")
                else:
                    self.log_test("Individual Product", False, f"Failed to get products: HTTP {response.status}")
        except Exception as e:
            self.log_test("Individual Product", False, f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting Backend API Tests for {API_BASE_URL}")
        print("=" * 60)
        
        # Test 1: Health check
        await self.test_health_check()
        
        # Test 2: Products endpoint
        success, products = await self.test_products_endpoint()
        
        # Test 3: Product filtering by category
        await self.test_products_filtering()
        
        # Test 4: Subcategory filtering
        await self.test_subcategory_filtering()
        
        # Test 5: Search functionality
        await self.test_search_functionality()
        
        # Test 6: Database product count
        await self.test_database_product_count()
        
        # Test 7: Individual product endpoint
        await self.test_individual_product_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

async def main():
    """Main test runner"""
    async with BackendTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)