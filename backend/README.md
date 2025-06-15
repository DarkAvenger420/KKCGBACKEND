# KKCG Analytics Backend API

Real-time analytics API for **Kodi Kura Chitti Gaare** restaurant chain built with FastAPI and PostgreSQL.

## 🚀 Features

- **RESTful API** with FastAPI
- **PostgreSQL Database** with SQLAlchemy ORM
- **JWT Authentication** for secure access
- **Real-time Analytics** endpoints
- **Docker Support** for easy deployment
- **Auto-generated API Documentation**

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker (optional)
- Git

## 🛠️ Local Development Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd kkcg-analytics/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

#### Option A: Using Docker Compose (Recommended)

```bash
# Start PostgreSQL and pgAdmin
docker-compose up postgres pgadmin -d

# Database will be available at:
# - Host: localhost
# - Port: 5432
# - Database: kkcg_analytics
# - Username: kkcg_user
# - Password: kkcg_password

# pgAdmin will be available at http://localhost:5050
# Email: admin@kkcg.com
# Password: admin123
```

#### Option B: Manual PostgreSQL Setup

```bash
# Install PostgreSQL and create database
createdb kkcg_analytics

# Update DATABASE_URL in your .env file
```

### 3. Environment Configuration

```bash
# Copy environment template
cp env_template.txt .env

# Edit .env file with your settings:
DATABASE_URL=postgresql://kkcg_user:kkcg_password@localhost:5432/kkcg_analytics
SECRET_KEY=your-super-secret-jwt-key-here
```

### 4. Run the Application

```bash
# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API will be available at:
# - Main API: http://localhost:8000
# - Documentation: http://localhost:8000/docs
# - Alternative docs: http://localhost:8000/redoc
```

### 5. Seed Database with Sample Data

```bash
# Using curl
curl -X POST http://localhost:8000/seed-data

# Or visit: http://localhost:8000/docs and use the /seed-data endpoint
```

## 🐳 Docker Deployment

### Complete Stack with Docker Compose

```bash
# Start all services (database, backend, pgAdmin)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

### Backend Only

```bash
# Build Docker image
docker build -t kkcg-backend .

# Run container
docker run -p 8000:8000 -e DATABASE_URL="your-db-url" kkcg-backend
```

## 📖 API Documentation

### Authentication Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token

### Data Endpoints

- `GET /outlets` - Get all outlets
- `GET /dishes` - Get all dishes
- `GET /demand-data` - Get demand data with filters
- `GET /analytics/summary` - Get analytics summary

### Example API Usage

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "admin", "password": "password"}
)
token = response.json()["access_token"]

# Get demand data
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/demand-data",
    headers=headers
)
data = response.json()
```

## 🔗 Connect to Streamlit App

### Update Streamlit App

1. **Set Environment Variable**
   ```bash
   # In your Streamlit app environment
   export API_BASE_URL="https://your-deployed-api-url.com"
   ```

2. **Use API Client in Streamlit**
   ```python
   from utils.api_client import get_api_client, show_backend_status
   
   # Check backend status
   backend_online = show_backend_status()
   
   if backend_online:
       # Use real backend data
       client = get_api_client()
       data = client.get_demand_data()
   else:
       # Fallback to demo data
       data = generate_demo_data()
   ```

## 🛡️ Security Considerations

### Production Deployment

1. **Change Default Secrets**
   ```bash
   # Generate secure secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use Environment Variables**
   - Never commit `.env` files
   - Use secure secret management
   - Enable HTTPS in production

3. **Database Security**
   - Use connection pooling
   - Enable SSL for database connections
   - Regular backups

### Rate Limiting

```python
# Add to main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.get("/demand-data")
@limiter.limit("100/minute")
async def get_demand_data(request: Request, ...):
    ...
```

## 📊 Monitoring & Logging

### Add Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response
```

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Ensure PostgreSQL is running
   - Verify network connectivity

2. **Authentication Errors**
   - Check SECRET_KEY configuration
   - Verify JWT token format
   - Check token expiration

3. **CORS Issues**
   - Update `allow_origins` in CORS middleware
   - Add your Streamlit app URL

### Debug Mode

```bash
# Enable debug logging
export DEBUG=True
uvicorn main:app --reload --log-level debug
```

## 📞 Support

For issues and questions:
- Check API documentation at `/docs`
- Review logs for error details
- Test endpoints with Postman/curl

## 🔄 Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-endpoint

# 2. Make changes and test
uvicorn main:app --reload

# 3. Test with Streamlit app
cd .. && streamlit run Home.py

# 4. Commit and push
git add .
git commit -m "Add new analytics endpoint"
git push origin feature/new-endpoint

# 5. Deploy to staging/production
railway up  # or your deployment method
```

---

**🎯 Your KKCG Analytics Backend is ready for production!** 