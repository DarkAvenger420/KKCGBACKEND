from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import os
import random
from dotenv import load_dotenv
import jwt
import hashlib

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/kkcg_analytics")

# Create FastAPI app
app = FastAPI(
    title="KKCG Analytics API",
    description="Real-time analytics API for Kodi Kura Chitti Gaare restaurant chain",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your Streamlit app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Outlet(Base):
    __tablename__ = "outlets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Dish(Base):
    __tablename__ = "dishes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
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

class Forecast(Base):
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("outlets.id"))
    dish_id = Column(Integer, ForeignKey("dishes.id"))
    forecast_date = Column(DateTime, index=True)
    predicted_demand = Column(Integer)
    confidence_score = Column(Float)
    model_version = Column(String, default="v1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    outlet = relationship("Outlet")
    dish = relationship("Dish")

# Create tables
Base.metadata.create_all(bind=engine)

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

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class OutletCreate(BaseModel):
    name: str
    location: str

class OutletResponse(BaseModel):
    id: int
    name: str
    location: str
    is_active: int

class DishCreate(BaseModel):
    name: str
    category: str
    price: float

class DishResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    is_active: int

class DemandDataCreate(BaseModel):
    outlet_id: int
    dish_id: int
    date: datetime
    actual_demand: Optional[int] = None
    predicted_demand: int
    weather_factor: float = 1.0

class DemandDataResponse(BaseModel):
    id: int
    outlet_name: str
    dish_name: str
    date: datetime
    actual_demand: Optional[int]
    predicted_demand: int
    weather_factor: float

class ForecastCreate(BaseModel):
    outlet_id: int
    dish_id: int
    forecast_date: datetime
    predicted_demand: int
    confidence_score: float

class ForecastResponse(BaseModel):
    id: int
    outlet_name: str
    dish_name: str
    forecast_date: datetime
    predicted_demand: int
    confidence_score: float
    model_version: str

# Dependency
def get_db():
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

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "KKCG Analytics API is running!",
        "version": "1.0.0",
        "status": "active"
    }

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
    
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

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/outlets", response_model=List[OutletResponse])
async def get_outlets(db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    outlets = db.query(Outlet).filter(Outlet.is_active == 1).all()
    return outlets

@app.post("/outlets", response_model=OutletResponse)
async def create_outlet(outlet: OutletCreate, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    db_outlet = Outlet(**outlet.dict())
    db.add(db_outlet)
    db.commit()
    db.refresh(db_outlet)
    return db_outlet

@app.get("/dishes", response_model=List[DishResponse])
async def get_dishes(db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    dishes = db.query(Dish).filter(Dish.is_active == 1).all()
    return dishes

@app.post("/dishes", response_model=DishResponse)
async def create_dish(dish: DishCreate, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    db_dish = Dish(**dish.dict())
    db.add(db_dish)
    db.commit()
    db.refresh(db_dish)
    return db_dish

@app.get("/demand-data", response_model=List[DemandDataResponse])
async def get_demand_data(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    outlet_id: Optional[int] = None,
    dish_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
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

@app.post("/demand-data", response_model=DemandDataResponse)
async def create_demand_data(
    demand_data: DemandDataCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    db_demand = DemandData(**demand_data.dict())
    db.add(db_demand)
    db.commit()
    db.refresh(db_demand)
    
    # Get outlet and dish names for response
    outlet = db.query(Outlet).filter(Outlet.id == demand_data.outlet_id).first()
    dish = db.query(Dish).filter(Dish.id == demand_data.dish_id).first()
    
    return DemandDataResponse(
        id=db_demand.id,
        outlet_name=outlet.name,
        dish_name=dish.name,
        date=db_demand.date,
        actual_demand=db_demand.actual_demand,
        predicted_demand=db_demand.predicted_demand,
        weather_factor=db_demand.weather_factor
    )

@app.get("/forecasts", response_model=List[ForecastResponse])
async def get_forecasts(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    outlet_id: Optional[int] = None,
    dish_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    query = db.query(
        Forecast.id,
        Outlet.name.label("outlet_name"),
        Dish.name.label("dish_name"),
        Forecast.forecast_date,
        Forecast.predicted_demand,
        Forecast.confidence_score,
        Forecast.model_version
    ).join(Outlet).join(Dish)
    
    if start_date:
        query = query.filter(Forecast.forecast_date >= start_date)
    if end_date:
        query = query.filter(Forecast.forecast_date <= end_date)
    if outlet_id:
        query = query.filter(Forecast.outlet_id == outlet_id)
    if dish_id:
        query = query.filter(Forecast.dish_id == dish_id)
    
    results = query.all()
    
    return [
        ForecastResponse(
            id=row.id,
            outlet_name=row.outlet_name,
            dish_name=row.dish_name,
            forecast_date=row.forecast_date,
            predicted_demand=row.predicted_demand,
            confidence_score=row.confidence_score,
            model_version=row.model_version
        )
        for row in results
    ]

@app.post("/forecasts", response_model=ForecastResponse)
async def create_forecast(
    forecast: ForecastCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    db_forecast = Forecast(**forecast.dict())
    db.add(db_forecast)
    db.commit()
    db.refresh(db_forecast)
    
    # Get outlet and dish names for response
    outlet = db.query(Outlet).filter(Outlet.id == forecast.outlet_id).first()
    dish = db.query(Dish).filter(Dish.id == forecast.dish_id).first()
    
    return ForecastResponse(
        id=db_forecast.id,
        outlet_name=outlet.name,
        dish_name=dish.name,
        forecast_date=db_forecast.forecast_date,
        predicted_demand=db_forecast.predicted_demand,
        confidence_score=db_forecast.confidence_score,
        model_version=db_forecast.model_version
    )

@app.get("/analytics/summary")
async def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get summary analytics for the dashboard"""
    
    # Get basic counts
    total_outlets = db.query(Outlet).filter(Outlet.is_active == 1).count()
    total_dishes = db.query(Dish).filter(Dish.is_active == 1).count()
    total_records = db.query(DemandData).count()
    
    # Get recent demand data
    recent_data = db.query(DemandData).order_by(DemandData.date.desc()).limit(1000).all()
    
    if not recent_data:
        return {
            "total_outlets": total_outlets,
            "total_dishes": total_dishes,
            "total_records": total_records,
            "avg_daily_demand": 0,
            "peak_demand": 0,
            "total_weekly_demand": 0
        }
    
    # Calculate analytics
    demands = [record.predicted_demand for record in recent_data]
    avg_daily_demand = sum(demands) / len(demands) if demands else 0
    peak_demand = max(demands) if demands else 0
    total_weekly_demand = sum(demands)
    
    return {
        "total_outlets": total_outlets,
        "total_dishes": total_dishes,
        "total_records": total_records,
        "avg_daily_demand": round(avg_daily_demand, 1),
        "peak_demand": peak_demand,
        "total_weekly_demand": total_weekly_demand
    }

@app.post("/seed-data")
async def seed_database(db: Session = Depends(get_db)):
    """Seed the database with sample data (for demo purposes)"""
    
    # South Indian dishes
    dishes_data = [
        {"name": "Masala Dosa", "category": "Main Course", "price": 120.0},
        {"name": "Idli Sambar", "category": "Breakfast", "price": 80.0},
        {"name": "Chicken Biryani", "category": "Main Course", "price": 250.0},
        {"name": "Uttapam", "category": "Breakfast", "price": 100.0},
        {"name": "Rasam Rice", "category": "Main Course", "price": 140.0},
        {"name": "Vada Sambar", "category": "Snacks", "price": 60.0},
        {"name": "Paneer Butter Masala", "category": "Main Course", "price": 180.0},
        {"name": "Filter Coffee", "category": "Beverages", "price": 40.0},
        {"name": "Coconut Chutney", "category": "Sides", "price": 30.0},
        {"name": "Hyderabadi Biryani", "category": "Main Course", "price": 280.0}
    ]
    
    # Outlets data
    outlets_data = [
        {"name": "Chennai Central", "location": "Chennai, Tamil Nadu"},
        {"name": "Jubilee Hills", "location": "Hyderabad, Telangana"},
        {"name": "Koramangala", "location": "Bangalore, Karnataka"},
        {"name": "Kochi Marine Drive", "location": "Kochi, Kerala"},
        {"name": "Coimbatore RS Puram", "location": "Coimbatore, Tamil Nadu"}
    ]
    
    # Create dishes
    for dish_data in dishes_data:
        existing_dish = db.query(Dish).filter(Dish.name == dish_data["name"]).first()
        if not existing_dish:
            db_dish = Dish(**dish_data)
            db.add(db_dish)
    
    # Create outlets
    for outlet_data in outlets_data:
        existing_outlet = db.query(Outlet).filter(Outlet.name == outlet_data["name"]).first()
        if not existing_outlet:
            db_outlet = Outlet(**outlet_data)
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
                # Generate realistic demand based on dish popularity
                base_demand = random.randint(50, 200)
                if dish.name in ["Chicken Biryani", "Masala Dosa", "Hyderabadi Biryani"]:
                    base_demand = random.randint(100, 300)
                elif dish.name in ["Filter Coffee", "Coconut Chutney"]:
                    base_demand = random.randint(20, 80)
                
                # Add some randomness
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
    
    return {"message": "Database seeded successfully with sample data"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 