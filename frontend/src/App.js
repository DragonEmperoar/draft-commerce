import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Set up axios with base URL
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'https://kawaiishop.preview.emergentagent.com';
axios.defaults.baseURL = API_BASE_URL;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('session_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get('/api/profile');
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('session_token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = (userData, token) => {
    setUser(userData);
    localStorage.setItem('session_token', token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  const logout = async () => {
    try {
      await axios.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    }
    setUser(null);
    localStorage.removeItem('session_token');
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    login,
    logout,
    loading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Header Component
const Header = () => {
  const { user, logout } = useAuth();
  const [cartCount, setCartCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      fetchCartCount();
    }
  }, [user]);

  const fetchCartCount = async () => {
    try {
      const response = await axios.get('/api/cart');
      const count = response.data.items.reduce((total, item) => total + item.quantity, 0);
      setCartCount(count);
    } catch (error) {
      console.error('Error fetching cart:', error);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleGoogleLogin = () => {
    const redirectUri = `${window.location.origin}/auth/google`;
    const googleAuthUrl = `https://accounts.google.com/oauth/authorize?client_id=YOUR_GOOGLE_CLIENT_ID&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=openid email profile`;
    window.location.href = googleAuthUrl;
  };

  return (
    <header className="bg-gradient-to-r from-purple-600 via-pink-500 to-red-500 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold flex items-center space-x-2">
            <span className="text-3xl">🌸</span>
            <span>Kawaii Shop</span>
          </Link>
          
          <form onSubmit={handleSearch} className="hidden md:flex items-center space-x-2 bg-white rounded-full px-4 py-2">
            <input
              type="text"
              placeholder="Search anime, products..."
              className="flex-1 outline-none text-gray-800 min-w-[300px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="text-purple-600 hover:text-purple-800">
              🔍
            </button>
          </form>

          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Link to="/cart" className="relative">
                  <span className="text-2xl">🛒</span>
                  {cartCount > 0 && (
                    <span className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full text-xs px-1 min-w-[20px] h-5 flex items-center justify-center">
                      {cartCount}
                    </span>
                  )}
                </Link>
                <div className="relative group">
                  <button className="flex items-center space-x-2">
                    <img src={user.picture || '/api/placeholder/32/32'} alt="Profile" className="w-8 h-8 rounded-full" />
                    <span className="hidden md:block">{user.name}</span>
                  </button>
                  <div className="absolute right-0 mt-2 w-48 bg-white text-gray-800 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                    <Link to="/profile" className="block px-4 py-2 hover:bg-gray-100">Profile</Link>
                    <Link to="/orders" className="block px-4 py-2 hover:bg-gray-100">Orders</Link>
                    <button onClick={logout} className="block w-full text-left px-4 py-2 hover:bg-gray-100">Logout</button>
                  </div>
                </div>
              </>
            ) : (
              <button
                onClick={handleGoogleLogin}
                className="bg-white text-purple-600 px-4 py-2 rounded-full font-medium hover:bg-gray-100 transition-colors"
              >
                Login with Google
              </button>
            )}
          </div>
        </div>
        
        <div className="md:hidden mt-4">
          <form onSubmit={handleSearch} className="flex items-center space-x-2 bg-white rounded-full px-4 py-2">
            <input
              type="text"
              placeholder="Search anime, products..."
              className="flex-1 outline-none text-gray-800"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="text-purple-600">🔍</button>
          </form>
        </div>
      </div>
    </header>
  );
};

// Hero Carousel Component
const HeroCarousel = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  
  const slides = [
    {
      image: 'https://images.unsplash.com/photo-1664806443911-fed254a37dab',
      title: 'Welcome to Kawaii Anime Shop',
      subtitle: 'Discover Amazing Anime Merchandise',
      cta: 'Shop Now'
    },
    {
      image: 'https://images.unsplash.com/photo-1610496975819-707150c4c369',
      title: 'Premium Action Figures',
      subtitle: 'Collectible figures from your favorite series',
      cta: 'Explore Figures'
    },
    {
      image: 'https://images.unsplash.com/photo-1571757767119-68b8dbed8c97',
      title: 'Cozy Plushes & T-shirts',
      subtitle: 'Soft merchandise for true fans',
      cta: 'Browse Collection'
    },
    {
      image: 'https://images.pexels.com/photos/6249454/pexels-photo-6249454.jpeg',
      title: 'Latest Anime Series',
      subtitle: 'From Naruto to One Piece and beyond',
      cta: 'Discover More'
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative h-96 md:h-[500px] overflow-hidden">
      {slides.map((slide, index) => (
        <div
          key={index}
          className={`absolute inset-0 transition-transform duration-500 ease-in-out ${
            index === currentSlide ? 'translate-x-0' : 'translate-x-full'
          }`}
        >
          <div
            className="w-full h-full bg-cover bg-center"
            style={{ backgroundImage: `url(${slide.image})` }}
          >
            <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
              <div className="text-center text-white max-w-4xl px-4">
                <h1 className="text-4xl md:text-6xl font-bold mb-4">{slide.title}</h1>
                <p className="text-xl md:text-2xl mb-8">{slide.subtitle}</p>
                <button className="bg-pink-500 hover:bg-pink-600 text-white font-bold py-3 px-8 rounded-full text-lg transition-colors">
                  {slide.cta}
                </button>
              </div>
            </div>
          </div>
        </div>
      ))}
      
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
        {slides.map((_, index) => (
          <button
            key={index}
            className={`w-3 h-3 rounded-full ${
              index === currentSlide ? 'bg-white' : 'bg-white bg-opacity-50'
            }`}
            onClick={() => setCurrentSlide(index)}
          />
        ))}
      </div>
    </div>
  );
};

// Home Component
const Home = () => {
  const navigate = useNavigate();

  const categories = [
    {
      title: 'Plushes',
      image: 'https://images.unsplash.com/photo-1571757767119-68b8dbed8c97',
      description: 'Soft and cuddly anime character plushes',
      path: '/category/plushes'
    },
    {
      title: 'T-shirts',
      image: 'https://images.unsplash.com/photo-1610496975819-707150c4c369',
      description: 'Stylish anime-themed apparel',
      path: '/category/t-shirts'
    },
    {
      title: 'Action Figures',
      image: 'https://images.pexels.com/photos/6249454/pexels-photo-6249454.jpeg',
      description: 'Premium collectible figures',
      path: '/category/action-figures'
    }
  ];

  return (
    <div className="min-h-screen">
      <HeroCarousel />
      
      <div className="container mx-auto px-4 py-16">
        <h2 className="text-4xl font-bold text-center mb-12 text-gray-800">
          Shop by Category
        </h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          {categories.map((category, index) => (
            <div
              key={index}
              className="bg-white rounded-lg shadow-lg overflow-hidden transform hover:scale-105 transition-transform duration-300 cursor-pointer"
              onClick={() => navigate(category.path)}
            >
              <div
                className="h-48 bg-cover bg-center"
                style={{ backgroundImage: `url(${category.image})` }}
              />
              <div className="p-6">
                <h3 className="text-2xl font-bold mb-2 text-gray-800">{category.title}</h3>
                <p className="text-gray-600 mb-4">{category.description}</p>
                <button className="bg-purple-500 hover:bg-purple-600 text-white font-bold py-2 px-6 rounded-full transition-colors">
                  Explore {category.title}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Category Component
const Category = () => {
  const { category } = useParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    subcategory: '',
    anime_series: '',
    sort_by: 'created_at',
    price_min: '',
    price_max: ''
  });
  const navigate = useNavigate();

  useEffect(() => {
    fetchProducts();
  }, [category, filters]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        category: category,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v))
      });
      
      const response = await axios.get(`/api/products?${params}`);
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleActionFiguresClick = () => {
    navigate('/action-figures-selection');
  };

  if (category === 'action-figures') {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-8 text-center">Action Figures</h1>
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <div 
            className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg p-8 text-center cursor-pointer transform hover:scale-105 transition-transform"
            onClick={() => navigate('/category/action-figures?subcategory=premium')}
          >
            <h2 className="text-3xl font-bold mb-4">Premium Collection</h2>
            <p className="text-xl mb-6">High-quality collectible figures with exceptional detail</p>
            <button className="bg-white text-purple-600 font-bold py-3 px-8 rounded-full text-lg hover:bg-gray-100 transition-colors">
              Shop Premium
            </button>
          </div>
          
          <div 
            className="bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg p-8 text-center cursor-pointer transform hover:scale-105 transition-transform"
            onClick={() => navigate('/category/action-figures?subcategory=sustainable')}
          >
            <h2 className="text-3xl font-bold mb-4">Sustainable Collection</h2>
            <p className="text-xl mb-6">Eco-friendly figures made with sustainable materials</p>
            <button className="bg-white text-green-600 font-bold py-3 px-8 rounded-full text-lg hover:bg-gray-100 transition-colors">
              Shop Sustainable
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row gap-8">
        {/* Filters Sidebar */}
        <div className="md:w-1/4">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold mb-4">Filters</h3>
            
            {/* Anime Series Filter */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Anime Series</label>
              <select
                className="w-full p-2 border rounded-lg"
                value={filters.anime_series}
                onChange={(e) => setFilters({...filters, anime_series: e.target.value})}
              >
                <option value="">All Series</option>
                <option value="Naruto">Naruto</option>
                <option value="One Piece">One Piece</option>
                <option value="Dragon Ball">Dragon Ball</option>
                <option value="Attack on Titan">Attack on Titan</option>
                <option value="My Hero Academia">My Hero Academia</option>
                <option value="Demon Slayer">Demon Slayer</option>
                <option value="Jujutsu Kaisen">Jujutsu Kaisen</option>
              </select>
            </div>

            {/* Sort By */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Sort By</label>
              <select
                className="w-full p-2 border rounded-lg"
                value={filters.sort_by}
                onChange={(e) => setFilters({...filters, sort_by: e.target.value})}
              >
                <option value="created_at">Newest</option>
                <option value="popularity">Popularity</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Products Grid */}
        <div className="md:w-3/4">
          <h1 className="text-3xl font-bold mb-6 capitalize">{category.replace('-', ' ')}</h1>
          
          {loading ? (
            <div className="grid md:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-gray-200 animate-pulse rounded-lg h-80" />
              ))}
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-6">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}

          {!loading && products.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 text-xl">No products found in this category.</p>
              <Link to="/" className="text-purple-600 hover:underline mt-4 inline-block">
                Browse other categories
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Product Card Component
const ProductCard = ({ product }) => {
  const navigate = useNavigate();

  return (
    <div 
      className="bg-white rounded-lg shadow-lg overflow-hidden transform hover:scale-105 transition-transform duration-300 cursor-pointer"
      onClick={() => navigate(`/product/${product.id}`)}
    >
      <div
        className="h-48 bg-cover bg-center"
        style={{ 
          backgroundImage: `url(${product.images[0] || 'https://images.unsplash.com/photo-1571757767119-68b8dbed8c97'})` 
        }}
      />
      <div className="p-4">
        <h3 className="font-bold text-lg mb-2 line-clamp-2">{product.name}</h3>
        <p className="text-gray-600 text-sm mb-2 line-clamp-2">{product.description}</p>
        {product.anime_series && (
          <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full mb-2">
            {product.anime_series}
          </span>
        )}
        <div className="flex justify-between items-center">
          <span className="text-2xl font-bold text-purple-600">₹{product.price}</span>
          {product.stock > 0 ? (
            <span className="text-green-600 text-sm">In Stock</span>
          ) : (
            <span className="text-red-600 text-sm">Out of Stock</span>
          )}
        </div>
      </div>
    </div>
  );
};

// Product Detail Component
const ProductDetail = () => {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);
  const [selectedSize, setSelectedSize] = useState('');
  const [selectedColor, setSelectedColor] = useState('');
  const [selectedFit, setSelectedFit] = useState('');
  const [quantity, setQuantity] = useState(1);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchProduct();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const response = await axios.get(`/api/products/${id}`);
      setProduct(response.data);
      if (response.data.sizes.length > 0) setSelectedSize(response.data.sizes[0]);
      if (response.data.colors.length > 0) setSelectedColor(response.data.colors[0]);
      if (response.data.fit_type) setSelectedFit(response.data.fit_type);
    } catch (error) {
      console.error('Error fetching product:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async () => {
    if (!user) {
      navigate('/login');
      return;
    }

    try {
      await axios.post('/api/cart/add', {
        product_id: product.id,
        quantity,
        selected_size: selectedSize,
        selected_color: selectedColor,
        selected_fit: selectedFit
      });
      alert('Product added to cart!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert('Error adding product to cart');
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading...</div>;
  }

  if (!product) {
    return <div className="container mx-auto px-4 py-8">Product not found</div>;
  }

  const images = product.images.length > 0 ? product.images : ['https://images.unsplash.com/photo-1571757767119-68b8dbed8c97'];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid md:grid-cols-2 gap-8">
        {/* Product Images */}
        <div>
          <div className="mb-4">
            <img
              src={images[selectedImage]}
              alt={product.name}
              className="w-full h-96 object-cover rounded-lg"
            />
          </div>
          {images.length > 1 && (
            <div className="flex space-x-2 overflow-x-auto">
              {images.map((image, index) => (
                <img
                  key={index}
                  src={image}
                  alt={`${product.name} ${index + 1}`}
                  className={`w-20 h-20 object-cover rounded cursor-pointer ${
                    selectedImage === index ? 'border-2 border-purple-500' : 'border'
                  }`}
                  onClick={() => setSelectedImage(index)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Product Details */}
        <div>
          <h1 className="text-3xl font-bold mb-4">{product.name}</h1>
          <div className="text-3xl font-bold text-purple-600 mb-4">₹{product.price}</div>
          
          {product.anime_series && (
            <div className="mb-4">
              <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                {product.anime_series}
              </span>
            </div>
          )}

          <p className="text-gray-700 mb-6">{product.description}</p>

          {/* Product Options */}
          {product.category === 't-shirts' && (
            <div className="space-y-4 mb-6">
              {/* Fit Type */}
              {product.fit_type && (
                <div>
                  <label className="block text-sm font-medium mb-2">Fit</label>
                  <select
                    className="w-full p-2 border rounded-lg"
                    value={selectedFit}
                    onChange={(e) => setSelectedFit(e.target.value)}
                  >
                    <option value="regular">Regular</option>
                    <option value="oversized">Oversized</option>
                  </select>
                </div>
              )}

              {/* Sizes */}
              {product.sizes.length > 0 && (
                <div>
                  <label className="block text-sm font-medium mb-2">Size</label>
                  <div className="flex space-x-2">
                    {product.sizes.map((size) => (
                      <button
                        key={size}
                        className={`px-4 py-2 border rounded ${
                          selectedSize === size
                            ? 'bg-purple-500 text-white'
                            : 'bg-white text-gray-800 hover:bg-gray-100'
                        }`}
                        onClick={() => setSelectedSize(size)}
                      >
                        {size}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Colors */}
              {product.colors.length > 0 && (
                <div>
                  <label className="block text-sm font-medium mb-2">Color</label>
                  <div className="flex space-x-2">
                    {product.colors.map((color) => (
                      <button
                        key={color}
                        className={`px-4 py-2 border rounded ${
                          selectedColor === color
                            ? 'bg-purple-500 text-white'
                            : 'bg-white text-gray-800 hover:bg-gray-100'
                        }`}
                        onClick={() => setSelectedColor(color)}
                      >
                        {color}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Quantity */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Quantity</label>
            <div className="flex items-center space-x-2">
              <button
                className="px-3 py-1 border rounded"
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
              >
                -
              </button>
              <span className="px-4 py-1 border rounded">{quantity}</span>
              <button
                className="px-3 py-1 border rounded"
                onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
              >
                +
              </button>
            </div>
          </div>

          {/* Stock Status */}
          <div className="mb-6">
            {product.stock > 0 ? (
              <span className="text-green-600">✅ {product.stock} in stock</span>
            ) : (
              <span className="text-red-600">❌ Out of stock</span>
            )}
          </div>

          {/* Add to Cart Button */}
          <button
            className={`w-full py-3 rounded-lg font-bold text-lg ${
              product.stock > 0 && user
                ? 'bg-purple-500 hover:bg-purple-600 text-white'
                : 'bg-gray-400 text-gray-600 cursor-not-allowed'
            }`}
            onClick={addToCart}
            disabled={product.stock === 0 || !user}
          >
            {!user ? 'Login to Add to Cart' : product.stock === 0 ? 'Out of Stock' : 'Add to Cart'}
          </button>

          {/* Product Specifications */}
          <div className="mt-8 border-t pt-6">
            <h3 className="text-xl font-bold mb-4">Specifications</h3>
            <div className="space-y-2 text-sm">
              {product.material && (
                <div><strong>Material:</strong> {product.material}</div>
              )}
              {product.dimensions && (
                <div><strong>Dimensions:</strong> {product.dimensions}</div>
              )}
              <div><strong>Category:</strong> {product.category}</div>
              {product.subcategory && (
                <div><strong>Type:</strong> {product.subcategory}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Cart Component
const Cart = () => {
  const [cart, setCart] = useState(null);
  const [products, setProducts] = useState({});
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      fetchCart();
    }
  }, [user]);

  const fetchCart = async () => {
    try {
      const response = await axios.get('/api/cart');
      setCart(response.data);
      
      // Fetch product details for each cart item
      const productPromises = response.data.items.map(item => 
        axios.get(`/api/products/${item.product_id}`)
      );
      const productResponses = await Promise.all(productPromises);
      
      const productsData = {};
      productResponses.forEach(res => {
        productsData[res.data.id] = res.data;
      });
      setProducts(productsData);
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (productId) => {
    try {
      await axios.delete(`/api/cart/${productId}`);
      fetchCart();
    } catch (error) {
      console.error('Error removing from cart:', error);
    }
  };

  const getTotalAmount = () => {
    if (!cart) return 0;
    return cart.items.reduce((total, item) => {
      const product = products[item.product_id];
      return total + (product ? product.price * item.quantity : 0);
    }, 0);
  };

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <h1 className="text-3xl font-bold mb-4">Please Login</h1>
        <p className="text-gray-600 mb-8">You need to be logged in to view your cart.</p>
        <button
          onClick={() => navigate('/')}
          className="bg-purple-500 hover:bg-purple-600 text-white font-bold py-2 px-6 rounded-full"
        >
          Go Home
        </button>
      </div>
    );
  }

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading cart...</div>;
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <h1 className="text-3xl font-bold mb-4">Your Cart is Empty</h1>
        <p className="text-gray-600 mb-8">Add some amazing anime merchandise to get started!</p>
        <Link
          to="/"
          className="bg-purple-500 hover:bg-purple-600 text-white font-bold py-2 px-6 rounded-full inline-block"
        >
          Continue Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Shopping Cart</h1>
      
      <div className="grid md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          {cart.items.map((item) => {
            const product = products[item.product_id];
            if (!product) return null;

            return (
              <div key={`${item.product_id}-${item.selected_size}-${item.selected_color}`} className="bg-white rounded-lg shadow-md p-6 mb-4">
                <div className="flex items-center space-x-4">
                  <img
                    src={product.images[0] || 'https://images.unsplash.com/photo-1571757767119-68b8dbed8c97'}
                    alt={product.name}
                    className="w-20 h-20 object-cover rounded"
                  />
                  <div className="flex-1">
                    <h3 className="font-bold text-lg">{product.name}</h3>
                    <p className="text-gray-600">{product.anime_series}</p>
                    {item.selected_size && (
                      <p className="text-sm text-gray-500">Size: {item.selected_size}</p>
                    )}
                    {item.selected_color && (
                      <p className="text-sm text-gray-500">Color: {item.selected_color}</p>
                    )}
                    {item.selected_fit && (
                      <p className="text-sm text-gray-500">Fit: {item.selected_fit}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">₹{product.price}</p>
                    <p className="text-gray-600">Qty: {item.quantity}</p>
                    <p className="font-bold text-purple-600">₹{product.price * item.quantity}</p>
                  </div>
                  <button
                    onClick={() => removeFromCart(item.product_id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Order Summary */}
        <div className="bg-white rounded-lg shadow-md p-6 h-fit">
          <h3 className="text-xl font-bold mb-4">Order Summary</h3>
          <div className="space-y-2 mb-4">
            <div className="flex justify-between">
              <span>Subtotal:</span>
              <span>₹{getTotalAmount()}</span>
            </div>
            <div className="flex justify-between">
              <span>Shipping:</span>
              <span>Free</span>
            </div>
            <div className="border-t pt-2 flex justify-between font-bold">
              <span>Total:</span>
              <span>₹{getTotalAmount()}</span>
            </div>
          </div>
          <button
            onClick={() => navigate('/checkout')}
            className="w-full bg-purple-500 hover:bg-purple-600 text-white font-bold py-3 rounded-lg"
          >
            Proceed to Checkout
          </button>
        </div>
      </div>
    </div>
  );
};

// Search Component
const Search = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const searchQuery = urlParams.get('q');
    if (searchQuery) {
      setQuery(searchQuery);
      searchProducts(searchQuery);
    }
  }, []);

  const searchProducts = async (searchQuery) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/products?search=${encodeURIComponent(searchQuery)}`);
      setProducts(response.data);
    } catch (error) {
      console.error('Error searching products:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Search Results for "{query}"</h1>
      
      {loading ? (
        <div className="grid md:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-gray-200 animate-pulse rounded-lg h-80" />
          ))}
        </div>
      ) : products.length > 0 ? (
        <div className="grid md:grid-cols-3 gap-6">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500 text-xl">No products found for "{query}"</p>
          <Link to="/" className="text-purple-600 hover:underline mt-4 inline-block">
            Browse all categories
          </Link>
        </div>
      )}
    </div>
  );
};

// Footer Component
const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white py-12 mt-16">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-xl font-bold mb-4">Kawaii Shop</h3>
            <p className="text-gray-400">Your one-stop destination for authentic anime merchandise.</p>
          </div>
          <div>
            <h4 className="font-bold mb-4">Categories</h4>
            <ul className="space-y-2 text-gray-400">
              <li><Link to="/category/plushes" className="hover:text-white">Plushes</Link></li>
              <li><Link to="/category/t-shirts" className="hover:text-white">T-shirts</Link></li>
              <li><Link to="/category/action-figures" className="hover:text-white">Action Figures</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold mb-4">Support</h4>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white">FAQ</a></li>
              <li><a href="#" className="hover:text-white">Contact Us</a></li>
              <li><a href="#" className="hover:text-white">Terms & Conditions</a></li>
              <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold mb-4">Follow Us</h4>
            <div className="flex space-x-4">
              <a href="#" className="text-2xl hover:text-purple-400">📱</a>
              <a href="#" className="text-2xl hover:text-purple-400">🐦</a>
              <a href="#" className="text-2xl hover:text-purple-400">📘</a>
              <a href="#" className="text-2xl hover:text-purple-400">📷</a>
            </div>
          </div>
        </div>
        <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2024 Kawaii Anime Shop. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App min-h-screen bg-gray-50">
          <Header />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/category/:category" element={<Category />} />
              <Route path="/product/:id" element={<ProductDetail />} />
              <Route path="/cart" element={<Cart />} />
              <Route path="/search" element={<Search />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;