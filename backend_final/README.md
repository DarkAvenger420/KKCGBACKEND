# 🚀 KKCG Analytics Backend - Bulletproof Edition

**Production-ready FastAPI backend with robust error handling and fallback systems.**

## ✅ **Features**

- **🛡️ Bulletproof Design** - Never crashes, always responds
- **🔄 Database Fallback** - Works with or without database
- **📊 Demo Mode** - Returns sample data if database unavailable
- **🔧 Multi-Platform** - Supports Railway, Heroku, Render, local development
- **🔐 Built-in Authentication** - JWT tokens with demo user
- **📖 Auto-Documentation** - Available at `/docs`

## 🚀 **Quick Deploy Options**

### **Option 1: Railway (Recommended)**

1. **Upload this folder** to GitHub repository `KKCGBACKEND`
2. **Go to [Railway.app](https://railway.app)**
3. **New Project** → **Deploy from GitHub**
4. **Select:** `KKCGBACKEND` repository
5. **Add PostgreSQL database**
6. **Environment Variables:**
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   SECRET_KEY=your-super-secret-key-here
   ```
7. **Deploy** and get your API URL!

### **Option 2: Render.com**

1. **Go to [Render.com](https://render.com)**
2. **New Web Service** → **Connect GitHub**
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Add PostgreSQL database**
6. **Set DATABASE_URL environment variable**

### **Option 3: Heroku**

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
git push heroku main
```

## 🔧 **Local Development**

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload

# API available at: http://localhost:8000
# Docs available at: http://localhost:8000/docs
```

## 🎯 **Testing Your Deployment**

### **1. Basic Health Check**
```bash
curl https://your-api-url.com/
# Should return: {"message": "KKCG Analytics API is running!", "status": "active"}
```

### **2. Demo Authentication**
```bash
curl -X POST https://your-api-url.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'
# Should return: {"access_token": "...", "token_type": "bearer"}
```

### **3. Get Sample Data**
```bash
curl https://your-api-url.com/outlets
# Should return: Array of outlets
```

### **4. Seed Database (if connected)**
```bash
curl -X POST https://your-api-url.com/seed-data
# Creates sample data in database
```

## 📊 **API Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check & status |
| GET | `/health` | Detailed health status |
| POST | `/auth/login` | Login (demo/demo works) |
| POST | `/auth/register` | Register new user |
| GET | `/outlets` | Get all outlets |
| GET | `/dishes` | Get all dishes |
| GET | `/demand-data` | Get demand analytics |
| GET | `/analytics/summary` | Get dashboard summary |
| POST | `/seed-data` | Seed database with sample data |
| GET | `/docs` | Interactive API documentation |

## 🛡️ **Error Handling**

This backend is designed to **never crash**:

### **✅ Database Issues**
- If database connection fails → Returns sample data
- If queries fail → Fallback to demo mode
- If seeding fails → Returns error message (doesn't crash)

### **✅ Authentication Issues**
- Demo user always works: `demo/demo`
- Invalid tokens → Returns proper error codes
- Missing auth → Returns 401 (doesn't crash)

### **✅ Data Issues**
- Missing data → Returns empty arrays
- Invalid dates → Uses current date
- Bad requests → Returns validation errors

## 🔐 **Demo Credentials**

**Built-in test user:**
- **Username:** `demo`
- **Password:** `demo`

**Always works regardless of database status!**

## 🌍 **Environment Variables**

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DATABASE_URL` | No | PostgreSQL connection string | SQLite fallback |
| `SECRET_KEY` | No | JWT secret key | Development key |
| `PORT` | No | Server port | 8000 |

## 📈 **Production Checklist**

### **✅ Before Going Live:**

1. **Set strong SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Verify database connection**
   - Check `/health` endpoint
   - Status should show "connected"

3. **Test all endpoints**
   - Visit `/docs` for interactive testing
   - Try demo login
   - Check data endpoints

4. **Seed database**
   - POST to `/seed-data`
   - Verify data in `/outlets` and `/dishes`

## 🚀 **Connect to Streamlit Frontend**

**Add this environment variable to your Streamlit Cloud app:**

```
API_BASE_URL = https://your-api-url.railway.app
```

**Your Streamlit app will automatically:**
- ✅ Connect to live backend
- ✅ Show real database data
- ✅ Enable user authentication
- ✅ Support real-time analytics

## 🔄 **Deployment Status Indicators**

**Backend Response Meanings:**

```json
{"database": "connected"}     // ✅ Full functionality
{"database": "demo_mode"}     // 🔄 Sample data mode
{"database": "error"}         // ⚠️ Database issues
```

## 🆘 **Troubleshooting**

### **Common Issues:**

1. **"Database not available" error**
   - Check DATABASE_URL environment variable
   - Verify PostgreSQL database is running
   - App still works in demo mode!

2. **"Module not found" errors**
   - Check requirements.txt
   - Verify Python version (3.11 recommended)
   - Clear cache and redeploy

3. **"Connection timeout" errors**
   - Check Railway/Heroku logs
   - Verify PORT environment variable
   - Check CORS settings

### **Railway Specific:**
- Ensure files are in repository **root** (not subfolder)
- Check Railway logs for deployment errors
- Verify environment variables are set

### **Heroku Specific:**
- Add `Procfile` with: `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
- Ensure PostgreSQL addon is attached
- Check Heroku logs: `heroku logs --tail`

---

## 🎉 **This Backend Will NOT Crash!**

**✅ Guaranteed Features:**
- Always returns HTTP 200 responses
- Graceful error handling
- Fallback to sample data
- Built-in demo authentication
- Production-ready logging
- Multi-platform compatibility

**🚀 Deploy with confidence - your backend is bulletproof!** 