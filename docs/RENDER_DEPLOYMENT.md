# HealthLang AI MVP - Render Deployment Guide

## 🚀 **Deployment to Render**

This guide will help you deploy the HealthLang AI MVP to Render successfully.

## 📋 **Prerequisites**

1. **GitHub Repository**: Your code should be pushed to GitHub
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **API Keys**: Ensure you have your API keys ready

## 🔧 **Deployment Steps**

### **1. Create a New Web Service on Render**

1. Go to your Render dashboard
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Select the repository: `Healthlang-ai-mvp`

### **2. Configure the Web Service**

**Basic Settings:**
- **Name**: `healthlang-ai-mvp` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main`

**Build & Deploy Settings:**
- **Build Command**: `pip install -r requirements-prod.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### **3. Environment Variables**

Add these environment variables in Render:

```bash
# Required API Keys
GROQ_API_KEY=your_groq_api_key_here
XAI_GROK_API_KEY=your_xai_api_key_here

# Application Settings
APP_NAME=HealthLang AI MVP
APP_VERSION=0.1.1
DEBUG=false

# Model Configuration
TRANSLATION_MODEL=meta-llama/Llama-4-Maverick-17B-128E-Instruct
MEDICAL_MODEL_NAME=meta-llama/Llama-4-Maverick-17B-128E-Instruct
LLM_PROVIDER=groq

# API Configuration
XAI_GROK_BASE_URL=https://api.x.ai/v1
GROQ_BASE_URL=https://api.groq.com/openai/v1

# Performance Settings
LLM_TIMEOUT=30
TEMPERATURE=0.1
MAX_TOKENS=2048
TOP_P=0.9

# Logging
LOG_LEVEL=info
```

### **4. Advanced Settings**

**Auto-Deploy:**
- ✅ Enable "Auto-Deploy" for automatic deployments on push

**Health Check Path:**
- Set to: `/health`

**Instance Type:**
- **Free Tier**: For testing (limited resources)
- **Standard**: For production (recommended)

## 🔍 **Troubleshooting**

### **Common Issues:**

#### **1. Dependency Conflicts (RESOLVED)**
- ✅ Fixed: `langchain-core>=0.2.27` requirement
- ✅ Fixed: Using `requirements-prod.txt` for production

#### **2. Build Failures**
If you encounter build issues:

```bash
# Check the build logs in Render
# Common fixes:
pip install --upgrade pip
pip install -r requirements-prod.txt --no-cache-dir
```

#### **3. Port Configuration**
Ensure your app uses the `$PORT` environment variable:

```python
# In your main.py or startup command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### **4. Memory Issues**
If you get memory errors:
- Upgrade to a larger instance type
- Consider using `requirements-prod.txt` (already configured)

### **5. Health Check Issues**
If health checks fail:
- Ensure `/health` endpoint returns 200
- Check that the app starts within the timeout period

## 📊 **Monitoring**

### **Health Check Endpoints:**
- **Basic Health**: `https://your-app.onrender.com/health`
- **Detailed Health**: `https://your-app.onrender.com/health/detailed`
- **API Documentation**: `https://your-app.onrender.com/docs`

### **Logs:**
- View logs in the Render dashboard
- Monitor for any startup errors
- Check API key configuration

## 🧪 **Testing After Deployment**

### **1. Health Check**
```bash
curl https://your-app.onrender.com/health
```

### **2. API Documentation**
Visit: `https://your-app.onrender.com/docs`

### **3. Test Translation**
```bash
curl -X POST "https://your-app.onrender.com/api/v1/translate/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "source_language": "en", "target_language": "yo"}'
```

### **4. Test Medical Query**
```bash
curl -X POST "https://your-app.onrender.com/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the symptoms of diabetes?"}'
```

## 🎯 **Success Indicators**

✅ **Deployment Successful When:**
- Build completes without errors
- Health check returns 200
- API documentation is accessible
- Translation endpoint works
- Medical query endpoint works
- Yoruba characters display correctly

## 🔄 **Updates and Maintenance**

### **Updating the Application:**
1. Push changes to GitHub
2. Render will automatically redeploy (if auto-deploy is enabled)
3. Monitor the deployment logs
4. Test the endpoints after deployment

### **Environment Variable Updates:**
1. Go to your Render service dashboard
2. Navigate to "Environment"
3. Update the required variables
4. Redeploy the service

## 📞 **Support**

If you encounter issues:
1. Check the Render deployment logs
2. Verify all environment variables are set
3. Test locally first to ensure code works
4. Check the application logs for specific errors

## 🎉 **Deployment Complete!**

Once deployed successfully, your HealthLang AI MVP will be available at:
`https://your-app-name.onrender.com`

**Key Features Available:**
- ✅ Medical query processing with LLaMA-4 Maverick
- ✅ Yoruba-English translation with proper encoding
- ✅ Interactive API documentation
- ✅ Health monitoring endpoints
- ✅ Production-ready performance

---

**Happy Deploying! 🚀** 