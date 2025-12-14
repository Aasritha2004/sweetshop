# test_main.py - Comprehensive Test Suite for Sweet Shop Backend
import pytest
from fastapi.testclient import TestClient
from main import app, get_db, init_db
import sqlite3
import os

# Test client
client = TestClient(app)

# Test database
TEST_DATABASE = "test_sweetshop.db"

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup and teardown test database for each test"""
    # Use test database
    import main
    main.DATABASE = TEST_DATABASE
    
    # Initialize database
    init_db()
    
    yield
    
    # Cleanup
    if os.path.exists(TEST_DATABASE):
        os.remove(TEST_DATABASE)

# ==================== AUTHENTICATION TESTS ====================

class TestAuthentication:
    """Test suite for authentication endpoints"""
    
    def test_register_new_user(self):
        """Test successful user registration"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        user_data = {
            "username": "testuser1",
            "email": "duplicate@example.com",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Try to register again with same email
        user_data["username"] = "testuser2"
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username"""
        user_data = {
            "username": "duplicateuser",
            "email": "user1@example.com",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Try to register again with same username
        user_data["email"] = "user2@example.com"
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self):
        """Test registration with invalid email format"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self):
        """Test registration with password less than 6 characters"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345",  # Only 5 characters
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        assert response.status_code == 422
    
    def test_login_success(self):
        """Test successful login"""
        # First register
        client.post("/api/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        
        # Then login
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "user"
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        # Register user
        client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "correctpassword",
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        
        # Try login with wrong password
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test getting current user information"""
        # Register and login
        client.post("/api/auth/register", json={
            "username": "currentuser",
            "email": "current@example.com",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "current@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Get user info
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"
        assert data["email"] == "current@example.com"
    
    def test_get_current_user_no_token(self):
        """Test getting current user without token"""
        response = client.get("/api/auth/me")
        assert response.status_code == 403  # Forbidden

# ==================== SWEETS CRUD TESTS ====================

class TestSweets:
    """Test suite for sweets endpoints"""
    
    def get_admin_token(self):
        """Helper to get admin token"""
        response = client.post("/api/auth/login", json={
            "email": "admin@sweetshop.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def get_user_token(self):
        """Helper to get regular user token"""
        client.post("/api/auth/register", json={
            "username": "regularuser",
            "email": "user@example.com",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "password123"
        })
        return response.json()["access_token"]
    
    def test_get_all_sweets(self):
        """Test retrieving all sweets"""
        response = client.get("/api/sweets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # Default sweets
    
    def test_get_sweet_by_id(self):
        """Test retrieving a specific sweet"""
        response = client.get("/api/sweets/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
    
    def test_get_nonexistent_sweet(self):
        """Test retrieving non-existent sweet"""
        response = client.get("/api/sweets/9999")
        assert response.status_code == 404
    
    def test_create_sweet_as_admin(self):
        """Test creating sweet as admin"""
        token = self.get_admin_token()
        response = client.post("/api/sweets", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New Sweet",
                "category": "Barfi",
                "price": 100,
                "quantity": 10,
                "description": "A new delicious sweet",
                "img": "assets/Images/new_sweet.jpg"
            })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Sweet"
        assert data["price"] == 100
    
    def test_create_sweet_as_user(self):
        """Test creating sweet as regular user (should fail)"""
        token = self.get_user_token()
        response = client.post("/api/sweets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Unauthorized Sweet",
                "category": "Barfi",
                "price": 50,
                "quantity": 5,
                "img": "assets/Images/sweet.jpg"
            })
        assert response.status_code == 403
    
    def test_create_sweet_invalid_price(self):
        """Test creating sweet with invalid price"""
        token = self.get_admin_token()
        response = client.post("/api/sweets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Invalid Sweet",
                "category": "Barfi",
                "price": -10,  # Negative price
                "quantity": 5,
                "img": "assets/Images/sweet.jpg"
            })
        assert response.status_code == 422
    
    def test_update_sweet_as_admin(self):
        """Test updating sweet as admin"""
        token = self.get_admin_token()
        response = client.put("/api/sweets/1",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "price": 60,
                "quantity": 15
            })
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 60
        assert data["quantity"] == 15
    
    def test_update_sweet_as_user(self):
        """Test updating sweet as regular user (should fail)"""
        token = self.get_user_token()
        response = client.put("/api/sweets/1",
            headers={"Authorization": f"Bearer {token}"},
            json={"price": 100})
        assert response.status_code == 403
    
    def test_delete_sweet_as_admin(self):
        """Test deleting sweet as admin"""
        token = self.get_admin_token()
        response = client.delete("/api/sweets/10",
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 204
        
        # Verify it's deleted
        response = client.get("/api/sweets/10")
        assert response.status_code == 404
    
    def test_delete_sweet_as_user(self):
        """Test deleting sweet as regular user (should fail)"""
        token = self.get_user_token()
        response = client.delete("/api/sweets/1",
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

# ==================== SEARCH TESTS ====================

class TestSearch:
    """Test suite for search functionality"""
    
    def test_search_by_name(self):
        """Test searching sweets by name"""
        response = client.get("/api/sweets/search?name=Laddu")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("laddu" in sweet["name"].lower() for sweet in data)
    
    def test_search_by_category(self):
        """Test searching sweets by category"""
        response = client.get("/api/sweets/search?category=Barfi")
        assert response.status_code == 200
        data = response.json()
        assert all(sweet["category"] == "Barfi" for sweet in data)
    
    def test_search_by_price_range(self):
        """Test searching sweets by price range"""
        response = client.get("/api/sweets/search?min_price=50&max_price=100")
        assert response.status_code == 200
        data = response.json()
        assert all(50 <= sweet["price"] <= 100 for sweet in data)
    
    def test_search_combined_filters(self):
        """Test searching with multiple filters"""
        response = client.get("/api/sweets/search?category=Laddoo&min_price=30&max_price=60")
        assert response.status_code == 200
        data = response.json()
        for sweet in data:
            assert sweet["category"] == "Laddoo"
            assert 30 <= sweet["price"] <= 60
    
    def test_search_no_results(self):
        """Test search with no matching results"""
        response = client.get("/api/sweets/search?name=NonexistentSweet")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

# ==================== INVENTORY TESTS ====================

class TestInventory:
    """Test suite for inventory management"""
    
    def get_user_token(self):
        """Helper to get user token"""
        client.post("/api/auth/register", json={
            "username": "buyer",
            "email": "buyer@example.com",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        response = client.post("/api/auth/login", json={
            "email": "buyer@example.com",
            "password": "password123"
        })
        return response.json()["access_token"]
    
    def get_admin_token(self):
        """Helper to get admin token"""
        response = client.post("/api/auth/login", json={
            "email": "admin@sweetshop.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_purchase_sweet_success(self):
        """Test successful sweet purchase"""
        token = self.get_user_token()
        
        # Get initial quantity
        initial_response = client.get("/api/sweets/1")
        initial_quantity = initial_response.json()["quantity"]
        
        # Purchase
        response = client.post("/api/sweets/1/purchase",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 2})
        assert response.status_code == 200
        data = response.json()
        assert data["quantity_purchased"] == 2
        assert data["remaining_stock"] == initial_quantity - 2
    
    def test_purchase_insufficient_stock(self):
        """Test purchasing more than available stock"""
        token = self.get_user_token()
        response = client.post("/api/sweets/1/purchase",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 1000})
        assert response.status_code == 400
        assert "insufficient stock" in response.json()["detail"].lower()
    
    def test_purchase_zero_quantity(self):
        """Test purchasing zero quantity"""
        token = self.get_user_token()
        response = client.post("/api/sweets/1/purchase",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 0})
        assert response.status_code == 422
    
    def test_purchase_without_auth(self):
        """Test purchasing without authentication"""
        response = client.post("/api/sweets/1/purchase",
            json={"quantity": 1})
        assert response.status_code == 403
    
    def test_restock_as_admin(self):
        """Test restocking sweet as admin"""
        token = self.get_admin_token()
        
        # Get initial quantity
        initial_response = client.get("/api/sweets/1")
        initial_quantity = initial_response.json()["quantity"]
        
        # Restock
        response = client.post("/api/sweets/1/restock",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 20})
        assert response.status_code == 200
        data = response.json()
        assert data["quantity_added"] == 20
        assert data["new_stock"] == initial_quantity + 20
    
    def test_restock_as_user(self):
        """Test restocking as regular user (should fail)"""
        token = self.get_user_token()
        response = client.post("/api/sweets/1/restock",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 10})
        assert response.status_code == 403
    
    def test_restock_nonexistent_sweet(self):
        """Test restocking non-existent sweet"""
        token = self.get_admin_token()
        response = client.post("/api/sweets/9999/restock",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 10})
        assert response.status_code == 404

# ==================== REPORTING TESTS ====================

class TestReporting:
    """Test suite for purchase and restock history"""
    
    def get_user_token(self):
        """Helper to get user token"""
        client.post("/api/auth/register", json={
            "username": "historyuser",
            "email": "history@example.com",
            "password": "password123",
            "mobile": "1234567890",
            "address": "123 Test Street"
        })
        response = client.post("/api/auth/login", json={
            "email": "history@example.com",
            "password": "password123"
        })
        return response.json()["access_token"]
    
    def get_admin_token(self):
        """Helper to get admin token"""
        response = client.post("/api/auth/login", json={
            "email": "admin@sweetshop.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_get_purchase_history(self):
        """Test retrieving purchase history"""
        token = self.get_user_token()
        
        # Make a purchase
        client.post("/api/sweets/1/purchase",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 2})
        
        # Get history
        response = client.get("/api/purchases/history",
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "sweet_name" in data[0]
    
    def test_get_restock_history_as_admin(self):
        """Test retrieving restock history as admin"""
        token = self.get_admin_token()
        
        # Make a restock
        client.post("/api/sweets/1/restock",
            headers={"Authorization": f"Bearer {token}"},
            json={"quantity": 10})
        
        # Get history
        response = client.get("/api/admin/restock-history",
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
    
    def test_get_restock_history_as_user(self):
        """Test retrieving restock history as user (should fail)"""
        token = self.get_user_token()
        response = client.get("/api/admin/restock-history",
            headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

# Run tests with: pytest test_main.py -v --cov=main --cov-report=html