from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
import random
import hashlib
import jwt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="KKCG Analytics API",
    description="Restaurant Analytics API for Kodi Kura Chitti Gaare",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration with fallback
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-for-development")

# Handle Railway PostgreSQL URL format
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback to SQLite if no DATABASE_URL
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./kkcg_analytics.db"
    logger.warning("No DATABASE_URL found, using SQLite fallback")

logger.info(f"Connecting to database: {DATABASE_URL.split('@')[0]}...")

# Database setup with error handling
try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    # Test database connection
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    logger.info("Database connection successful!")
    
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    # Create a dummy engine for development
    engine = None
    SessionLocal = None
    Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Outlet(Base):
    __tablename__ = "outlets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    location = Column(String(200))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Dish(Base):
    __tablename__ = "dishes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    category = Column(String(50))
    price = Column(Float)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class DemandData(Base):
    __tablename__ = "demand_data"
    
    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("outlets.id"))
    dish_id = Column(Integer, ForeignKey("dishes.id"))
    date = Column(DateTime, index=True)
    actual_demand = Column(Integer, nullable=True)
    predicted_demand = Column(Integer)
    weather_factor = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    outlet = relationship("Outlet")
    dish = relationship("Dish")

# Create tables only if database is available
if engine:
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class OutletResponse(BaseModel):
    id: int
    name: str
    location: str
    is_active: int
    
    class Config:
        from_attributes = True

class DishResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    is_active: int
    
    class Config:
        from_attributes = True

class DemandDataResponse(BaseModel):
    id: int
    outlet_name: str
    dish_name: str
    date: datetime
    actual_demand: Optional[int]
    predicted_demand: int
    weather_factor: float

# Database dependency
def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not available")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# Sample data for demo mode
SAMPLE_OUTLETS = [
    {"id": 1, "name": "Chennai Central", "location": "Chennai, Tamil Nadu", "is_active": 1},
    {"id": 2, "name": "Jubilee Hills", "location": "Hyderabad, Telangana", "is_active": 1},
    {"id": 3, "name": "Koramangala", "location": "Bangalore, Karnataka", "is_active": 1},
    {"id": 4, "name": "Kochi Marine Drive", "location": "Kochi, Kerala", "is_active": 1},
    {"id": 5, "name": "Coimbatore RS Puram", "location": "Coimbatore, Tamil Nadu", "is_active": 1}
]

SAMPLE_DISHES = [
    {"id": 1, "name": "Masala Dosa", "category": "Main Course", "price": 120.0, "is_active": 1},
    {"id": 2, "name": "Idli Sambar", "category": "Breakfast", "price": 80.0, "is_active": 1},
    {"id": 3, "name": "Chicken Biryani", "category": "Main Course", "price": 250.0, "is_active": 1},
    {"id": 4, "name": "Uttapam", "category": "Breakfast", "price": 100.0, "is_active": 1},
    {"id": 5, "name": "Rasam Rice", "category": "Main Course", "price": 140.0, "is_active": 1},
    {"id": 6, "name": "Vada Sambar", "category": "Snacks", "price": 60.0, "is_active": 1},
    {"id": 7, "name": "Paneer Butter Masala", "category": "Main Course", "price": 180.0, "is_active": 1},
    {"id": 8, "name": "Filter Coffee", "category": "Beverages", "price": 40.0, "is_active": 1},
    {"id": 9, "name": "Coconut Chutney", "category": "Sides", "price": 30.0, "is_active": 1},
    {"id": 10, "name": "Hyderabadi Biryani", "category": "Main Course", "price": 280.0, "is_active": 1}
]

def generate_sample_demand_data():
    """Generate sample demand data for demo mode"""
    data = []
    for i in range(7):  # 7 days
        date = datetime.now() - timedelta(days=i)
        for outlet in SAMPLE_OUTLETS:
            for dish in SAMPLE_DISHES:
                base_demand = random.randint(50, 200)
                if dish["name"] in ["Chicken Biryani", "Masala Dosa", "Hyderabadi Biryani"]:
                    base_demand = random.randint(100, 300)
                elif dish["name"] in ["Filter Coffee", "Coconut Chutney"]:
                    base_demand = random.randint(20, 80)
                
                predicted_demand = int(base_demand * random.uniform(0.8, 1.2))
                weather_factor = random.uniform(0.9, 1.1)
                
                data.append({
                    "id": len(data) + 1,
                    "outlet_name": outlet["name"],
                    "dish_name": dish["name"],
                    "date": date,
                    "actual_demand": None,
                    "predicted_demand": predicted_demand,
                    "weather_factor": weather_factor
                })
    return data

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "KKCG Analytics API is running!",
        "version": "1.0.0",
        "status": "active",
        "database": "connected" if engine else "demo_mode"
    }

@app.get("/health")
async def health_check():
    db_status = "connected" if engine else "demo_mode"
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": db_status,
        "version": "1.0.0"
    }

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.username == user.username) | (User.email == user.email)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already registered")
        
        # Create new user
        hashed_password = hash_password(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    except Exception as e:
        logger.error(f"Registration error: {e}")
        if "already registered" in str(e):
            raise e
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    # Demo user for testing
    if login_data.username == "demo" and login_data.password == "demo":
        access_token = create_access_token(data={"sub": "demo", "user_id": 1})
        return {"access_token": access_token, "token_type": "bearer"}
    
    # If database is available, try real login
    if engine:
        try:
            db = SessionLocal()
            user = db.query(User).filter(User.username == login_data.username).first()
            db.close()
            
            if user and verify_password(login_data.password, user.hashed_password):
                access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
                return {"access_token": access_token, "token_type": "bearer"}
        except Exception as e:
            logger.error(f"Login error: {e}")
    
    raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/outlets", response_model=List[OutletResponse])
async def get_outlets():
    if not engine:
        # Return sample data if no database
        return [OutletResponse(**outlet) for outlet in SAMPLE_OUTLETS]
    
    try:
        db = SessionLocal()
        outlets = db.query(Outlet).filter(Outlet.is_active == 1).all()
        db.close()
        return outlets
    except Exception as e:
        logger.error(f"Error fetching outlets: {e}")
        # Fallback to sample data
        return [OutletResponse(**outlet) for outlet in SAMPLE_OUTLETS]

@app.get("/dishes", response_model=List[DishResponse])
async def get_dishes():
    if not engine:
        # Return sample data if no database
        return [DishResponse(**dish) for dish in SAMPLE_DISHES]
    
    try:
        db = SessionLocal()
        dishes = db.query(Dish).filter(Dish.is_active == 1).all()
        db.close()
        return dishes
    except Exception as e:
        logger.error(f"Error fetching dishes: {e}")
        # Fallback to sample data
        return [DishResponse(**dish) for dish in SAMPLE_DISHES]

@app.get("/demand-data", response_model=List[DemandDataResponse])
async def get_demand_data(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    outlet_id: Optional[int] = None,
    dish_id: Optional[int] = None
):
    if not engine:
        # Return sample data if no database
        sample_data = generate_sample_demand_data()
        return [DemandDataResponse(**item) for item in sample_data]
    
    try:
        db = SessionLocal()
        query = db.query(
            DemandData.id,
            Outlet.name.label("outlet_name"),
            Dish.name.label("dish_name"),
            DemandData.date,
            DemandData.actual_demand,
            DemandData.predicted_demand,
            DemandData.weather_factor
        ).join(Outlet).join(Dish)
        
        if start_date:
            query = query.filter(DemandData.date >= start_date)
        if end_date:
            query = query.filter(DemandData.date <= end_date)
        if outlet_id:
            query = query.filter(DemandData.outlet_id == outlet_id)
        if dish_id:
            query = query.filter(DemandData.dish_id == dish_id)
        
        results = query.all()
        db.close()
        
        return [
            DemandDataResponse(
                id=row.id,
                outlet_name=row.outlet_name,
                dish_name=row.dish_name,
                date=row.date,
                actual_demand=row.actual_demand,
                predicted_demand=row.predicted_demand,
                weather_factor=row.weather_factor
            )
            for row in results
        ]
    except Exception as e:
        logger.error(f"Error fetching demand data: {e}")
        # Fallback to sample data
        sample_data = generate_sample_demand_data()
        return [DemandDataResponse(**item) for item in sample_data]

@app.get("/analytics/summary")
async def get_analytics_summary():
    """Get summary analytics for the dashboard"""
    
    if not engine:
        # Return sample analytics if no database
        return {
            "total_outlets": 5,
            "total_dishes": 10,
            "total_records": 350,
            "avg_daily_demand": 125.5,
            "peak_demand": 295,
            "total_weekly_demand": 43925
        }
    
    try:
        db = SessionLocal()
        
        total_outlets = db.query(Outlet).filter(Outlet.is_active == 1).count()
        total_dishes = db.query(Dish).filter(Dish.is_active == 1).count()
        total_records = db.query(DemandData).count()
        
        # Get recent demand data
        recent_data = db.query(DemandData).order_by(DemandData.date.desc()).limit(1000).all()
        
        if recent_data:
            demands = [record.predicted_demand for record in recent_data]
            avg_daily_demand = sum(demands) / len(demands)
            peak_demand = max(demands)
            total_weekly_demand = sum(demands)
        else:
            avg_daily_demand = 0
            peak_demand = 0
            total_weekly_demand = 0
        
        db.close()
        
        return {
            "total_outlets": total_outlets,
            "total_dishes": total_dishes,
            "total_records": total_records,
            "avg_daily_demand": round(avg_daily_demand, 1),
            "peak_demand": peak_demand,
            "total_weekly_demand": total_weekly_demand
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        # Fallback to sample analytics
        return {
            "total_outlets": 5,
            "total_dishes": 10,
            "total_records": 350,
            "avg_daily_demand": 125.5,
            "peak_demand": 295,
            "total_weekly_demand": 43925
        }

@app.post("/seed-data")
async def seed_database():
    """Seed the database with sample data"""
    
    if not engine:
        return {"message": "Running in demo mode - no database to seed"}
    
    try:
        db = SessionLocal()
        
        # Create dishes if they don't exist
        for dish_data in SAMPLE_DISHES:
            existing_dish = db.query(Dish).filter(Dish.name == dish_data["name"]).first()
            if not existing_dish:
                db_dish = Dish(
                    name=dish_data["name"],
                    category=dish_data["category"],
                    price=dish_data["price"]
                )
                db.add(db_dish)
        
        # Create outlets if they don't exist
        for outlet_data in SAMPLE_OUTLETS:
            existing_outlet = db.query(Outlet).filter(Outlet.name == outlet_data["name"]).first()
            if not existing_outlet:
                db_outlet = Outlet(
                    name=outlet_data["name"],
                    location=outlet_data["location"]
                )
                db.add(db_outlet)
        
        db.commit()
        
        # Generate sample demand data
        outlets = db.query(Outlet).all()
        dishes = db.query(Dish).all()
        
        # Clear existing demand data
        db.query(DemandData).delete()
        
        # Generate 7 days of data
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            
            for outlet in outlets:
                for dish in dishes:
                    base_demand = random.randint(50, 200)
                    if dish.name in ["Chicken Biryani", "Masala Dosa", "Hyderabadi Biryani"]:
                        base_demand = random.randint(100, 300)
                    elif dish.name in ["Filter Coffee", "Coconut Chutney"]:
                        base_demand = random.randint(20, 80)
                    
                    predicted_demand = int(base_demand * random.uniform(0.8, 1.2))
                    weather_factor = random.uniform(0.9, 1.1)
                    
                    db_demand = DemandData(
                        outlet_id=outlet.id,
                        dish_id=dish.id,
                        date=date,
                        predicted_demand=predicted_demand,
                        weather_factor=weather_factor
                    )
                    db.add(db_demand)
        
        db.commit()
        db.close()
        
        return {"message": "Database seeded successfully with sample data"}
    
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        return {"message": f"Database seeding failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 