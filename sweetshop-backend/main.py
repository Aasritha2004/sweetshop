# main.py - Complete Sweet Shop Backend with FastAPI
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import sqlite3
from contextlib import contextmanager
import logging

# Configuration
SECRET_KEY = "your-secret-key-change-this-in-production-use-env-variable"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Initialize FastAPI
app = FastAPI(
    title="Sweet Shop Management System",
    description="A comprehensive sweet shop management API with authentication and inventory",
    version="1.0.0"
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database setup
DATABASE = "sweetshop.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database with all required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                mobile TEXT NOT NULL,
                address TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sweets table with comprehensive fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                description TEXT,
                img TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Purchase history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sweet_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (sweet_id) REFERENCES sweets (id)
            )
        """)
        
        # Restock history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS restock_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sweet_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                quantity_added INTEGER NOT NULL,
                restock_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sweet_id) REFERENCES sweets (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        
        # Insert default admin user if not exists
        cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@sweetshop.com",))
        if not cursor.fetchone():
            hashed_password = pwd_context.hash("admin123")
            cursor.execute(
                "INSERT INTO users (username, email, password, mobile, address, role) VALUES (?, ?, ?, ?, ?, ?)",
                ("Admin", "admin@sweetshop.com", hashed_password, "9999999999", "Admin Address", "admin")
            )
            conn.commit()
            logger.info("Default admin user created")
        
        # Insert default sweets if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM sweets")
        if cursor.fetchone()["count"] == 0:
            default_sweets = [
                ("Soan Papdi", "Barfi", 50, 10, "Traditional flaky sweet made from gram flour", "assets/Images/soan_papdi.jpg"),
                ("Motichur Laddu", "Laddoo", 30, 15, "Sweet balls made from gram flour and sugar", "assets/Images/motichur_laddu.jpg"),
                ("Mysorepak", "Barfi", 80, 8, "Rich sweet from Mysore made with ghee", "assets/Images/mysore_pak.jpg"),
                ("Gulab Jamun", "Laddoo", 55, 12, "Soft milk-solid balls soaked in sugar syrup", "assets/Images/gulab_jamun.jpg"),
                ("Kaju Barfi", "Barfi", 120, 5, "Premium cashew fudge", "assets/Images/kaju_katli.jpg"),
                ("Rasgulla", "Laddoo", 45, 20, "Spongy cottage cheese balls in sugar syrup", "assets/Images/rasmalai.jpg"),
                ("Suji Halwa", "Halwa", 60, 7, "Semolina pudding with ghee and dry fruits", "assets/Images/suji_ka_halwa.jpg"),
                ("Peda", "Laddoo", 35, 25, "Milk-based sweet flavored with cardamom", "assets/Images/peda.jpg"),
                ("Jalebi", "Farsan", 40, 18, "Crispy spiral sweet soaked in sugar syrup", "assets/Images/jalebi.jpg"),
                ("Ghevar", "Farsan", 65, 6, "Honeycomb-shaped Rajasthani sweet", "assets/Images/Ghevar.jpg")
            ]
            cursor.executemany(
                "INSERT INTO sweets (name, category, price, quantity, description, img) VALUES (?, ?, ?, ?, ?, ?)",
                default_sweets
            )
            conn.commit()
            logger.info("Default sweets data populated")

# ==================== PYDANTIC MODELS ====================

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    mobile: str = Field(..., min_length=10, max_length=15)
    address: str = Field(..., min_length=5)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    mobile: str
    address: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class SweetCreate(BaseModel):
    name: str = Field(..., min_length=2)
    category: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)
    description: Optional[str] = None
    img: str

class SweetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    img: Optional[str] = None

class SweetResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    quantity: int
    description: Optional[str]
    img: str
    created_at: str
    updated_at: str

class PurchaseRequest(BaseModel):
    quantity: int = Field(..., gt=0)

class RestockRequest(BaseModel):
    quantity: int = Field(..., gt=0)

class SearchParams(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

# ==================== HELPER FUNCTIONS ====================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or token has expired")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return dict(user)

def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ==================== API ROUTES ====================

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Sweet Shop Management System API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
    """Register a new user"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create user
        hashed_password = get_password_hash(user.password)
        cursor.execute(
            "INSERT INTO users (username, email, password, mobile, address) VALUES (?, ?, ?, ?, ?)",
            (user.username, user.email, hashed_password, user.mobile, user.address)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        new_user = cursor.fetchone()
        
        logger.info(f"New user registered: {user.email}")
        return UserResponse(**dict(new_user))

@app.post("/api/auth/login", response_model=Token)
def login(user: UserLogin):
    """Login user and return JWT token"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
        db_user = cursor.fetchone()
        
        if not db_user or not verify_password(user.password, db_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        access_token = create_access_token(data={"sub": str(db_user["id"])})
        logger.info(f"User logged in: {user.email}")
        return Token(access_token=access_token, token_type="bearer", role=db_user["role"])

@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user)

# ==================== SWEETS ENDPOINTS ====================

@app.get("/api/sweets", response_model=List[SweetResponse])
def get_sweets():
    """Get all sweets"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sweets ORDER BY created_at DESC")
        sweets = cursor.fetchall()
        return [SweetResponse(**dict(sweet)) for sweet in sweets]

@app.get("/api/sweets/search", response_model=List[SweetResponse])
def search_sweets(
    name: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    """Search sweets by name, category, or price range"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM sweets WHERE 1=1"
        params = []
        
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        sweets = cursor.fetchall()
        return [SweetResponse(**dict(sweet)) for sweet in sweets]

@app.get("/api/sweets/{sweet_id}", response_model=SweetResponse)
def get_sweet(sweet_id: int):
    """Get a specific sweet by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sweets WHERE id = ?", (sweet_id,))
        sweet = cursor.fetchone()
        
        if not sweet:
            raise HTTPException(status_code=404, detail="Sweet not found")
        
        return SweetResponse(**dict(sweet))

@app.post("/api/sweets", response_model=SweetResponse, status_code=status.HTTP_201_CREATED)
def create_sweet(sweet: SweetCreate, admin: dict = Depends(get_admin_user)):
    """Create a new sweet (Admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO sweets (name, category, price, quantity, description, img) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sweet.name, sweet.category, sweet.price, sweet.quantity, sweet.description, sweet.img)
        )
        conn.commit()
        sweet_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM sweets WHERE id = ?", (sweet_id,))
        new_sweet = cursor.fetchone()
        
        logger.info(f"New sweet created: {sweet.name} by admin {admin['username']}")
        return SweetResponse(**dict(new_sweet))

@app.put("/api/sweets/{sweet_id}", response_model=SweetResponse)
def update_sweet(sweet_id: int, sweet: SweetUpdate, admin: dict = Depends(get_admin_user)):
    """Update sweet details (Admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sweets WHERE id = ?", (sweet_id,))
        existing_sweet = cursor.fetchone()
        
        if not existing_sweet:
            raise HTTPException(status_code=404, detail="Sweet not found")
        
        update_data = sweet.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
            values = list(update_data.values()) + [sweet_id]
            cursor.execute(f"UPDATE sweets SET {set_clause} WHERE id = ?", values)
            conn.commit()
        
        cursor.execute("SELECT * FROM sweets WHERE id = ?", (sweet_id,))
        updated_sweet = cursor.fetchone()
        
        logger.info(f"Sweet updated: {sweet_id} by admin {admin['username']}")
        return SweetResponse(**dict(updated_sweet))

@app.delete("/api/sweets/{sweet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sweet(sweet_id: int, admin: dict = Depends(get_admin_user)):
    """Delete a sweet (Admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sweets WHERE id = ?", (sweet_id,))
        sweet = cursor.fetchone()
        
        if not sweet:
            raise HTTPException(status_code=404, detail="Sweet not found")
        
        cursor.execute("DELETE FROM sweets WHERE id = ?", (sweet_id,))
        conn.commit()
        
        logger.info(f"Sweet deleted: {sweet_id} by admin {admin['username']}")

# ==================== INVENTORY ENDPOINTS ====================

@app.post("/api/sweets/{sweet_id}/purchase")
def purchase_sweet(sweet_id: int, purchase: PurchaseRequest, current_user: dict = Depends(get_current_user)):
    """Purchase a sweet, decreasing its quantity"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sweets WHERE id = ?", (sweet_id,))
        sweet = cursor.fetchone()
        
        if not sweet:
            raise HTTPException(status_code=404, detail="Sweet not found")
        
        if sweet["quantity"] < purchase.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock. Only {sweet['quantity']} available")
        
        # Update stock
        new_quantity = sweet["quantity"] - purchase.quantity
        cursor.execute("UPDATE sweets SET quantity = ?, updated_at = ? WHERE id = ?", 
                      (new_quantity, datetime.utcnow().isoformat(), sweet_id))
        
        # Record purchase
        total_price = sweet["price"] * purchase.quantity
        cursor.execute(
            """INSERT INTO purchases (user_id, sweet_id, quantity, total_price) 
               VALUES (?, ?, ?, ?)""",
            (current_user["id"], sweet_id, purchase.quantity, total_price)
        )
        conn.commit()
        
        logger.info(f"Purchase made: {purchase.quantity}x {sweet['name']} by {current_user['username']}")
        
        return {
            "message": "Purchase successful",
            "sweet_name": sweet["name"],
            "quantity_purchased": purchase.quantity,
            "total_price": total_price,
            "remaining_stock": new_quantity
        }

@app.post("/api/sweets/{sweet_id}/restock")
def restock_sweet(sweet_id: int, restock: RestockRequest, admin: dict = Depends(get_admin_user)):
    """Restock a sweet, increasing its quantity (Admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sweets WHERE id = ?", (sweet_id,))
        sweet = cursor.fetchone()
        
        if not sweet:
            raise HTTPException(status_code=404, detail="Sweet not found")
        
        # Update stock
        new_quantity = sweet["quantity"] + restock.quantity
        cursor.execute("UPDATE sweets SET quantity = ?, updated_at = ? WHERE id = ?", 
                      (new_quantity, datetime.utcnow().isoformat(), sweet_id))
        
        # Record restock
        cursor.execute(
            """INSERT INTO restock_history (sweet_id, admin_id, quantity_added) 
               VALUES (?, ?, ?)""",
            (sweet_id, admin["id"], restock.quantity)
        )
        conn.commit()
        
        logger.info(f"Restock: {restock.quantity}x {sweet['name']} by admin {admin['username']}")
        
        return {
            "message": "Restock successful",
            "sweet_name": sweet["name"],
            "quantity_added": restock.quantity,
            "new_stock": new_quantity
        }

# ==================== REPORTING ENDPOINTS ====================

@app.get("/api/purchases/history")
def get_purchase_history(current_user: dict = Depends(get_current_user)):
    """Get purchase history for current user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, s.name as sweet_name, s.category, s.img 
            FROM purchases p
            JOIN sweets s ON p.sweet_id = s.id
            WHERE p.user_id = ?
            ORDER BY p.purchase_date DESC
        """, (current_user["id"],))
        purchases = cursor.fetchall()
        return [dict(purchase) for purchase in purchases]

@app.get("/api/admin/restock-history")
def get_restock_history(admin: dict = Depends(get_admin_user)):
    """Get restock history (Admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, s.name as sweet_name, u.username as admin_name
            FROM restock_history r
            JOIN sweets s ON r.sweet_id = s.id
            JOIN users u ON r.admin_id = u.id
            ORDER BY r.restock_date DESC
        """)
        restocks = cursor.fetchall()
        return [dict(restock) for restock in restocks]

# ==================== STARTUP EVENT ====================

@app.on_event("startup")
def startup_event():
    init_db()
    logger.info("Sweet Shop Management System started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)