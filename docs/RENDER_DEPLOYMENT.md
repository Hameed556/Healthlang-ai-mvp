# Render Deployment Guide

This guide walks you through deploying HealthLang AI MVP on Render with optimized settings for fast, accurate responses.

## 🚀 **Deployment Overview**

### **What We're Deploying**
- **Bilingual Medical Q&A System** (Yoruba ↔ English)
- **Language-Matching Responses** (default behavior)
- **Optional Translation** (when requested)
- **Optimized for Speed** (1.8-2.2s response times)
- **Production-Ready** with monitoring and caching

### **Performance Optimizations**
- **Reduced token limits** (2048 tokens)
- **Fewer RAG documents** (3 documents)
- **Enhanced caching** (2-hour TTL, 2000 entries)
- **Higher similarity threshold** (0.75)
- **Increased rate limits** (120/min, 2000/hour)

## 📋 **Prerequisites**

### **1. Render Account**
- Sign up at [render.com](https://render.com)
- Choose a plan (Starter recommended for MVP)

### **2. API Keys**
- **Groq API Key** (required)
- **OpenAI API Key** (optional backup)
- **Anthropic API Key** (optional backup)

### **3. Repository**
- Push your code to GitHub/GitLab
- Ensure `render.yaml` is in the root directory

## 🔧 **Deployment Steps**

### **Step 1: Connect Repository**

1. **Log into Render Dashboard**
2. **Click "New +"** → **"Web Service"**
3. **Connect your repository** (GitHub/GitLab)
4. **Select the repository** containing HealthLang AI MVP

### **Step 2: Configure Service**

1. **Service Name**: `healthlang-ai-mvp`
2. **Environment**: `Python 3`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`

### **Step 3: Set Environment Variables**

In the Render dashboard, add these environment variables:

#### **Required Variables**
```bash
GROQ_API_KEY=your_groq_api_key_here
```

#### **Optional Variables**
```bash
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### **Performance Variables** (already set in render.yaml)
```bash
ENVIRONMENT=production
DEBUG=false
MAX_TOKENS=2048
MAX_RETRIEVAL_DOCS=3
SIMILARITY_THRESHOLD=0.75
CACHE_TTL=7200
CACHE_MAX_SIZE=2000
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_PER_HOUR=2000
```

### **Step 4: Configure Resources**

1. **Plan**: Starter (recommended for MVP)
2. **Instance Type**: Standard
3. **Auto-Deploy**: Enabled
4. **Health Check Path**: `/health`

### **Step 5: Deploy**

1. **Click "Create Web Service"**
2. **Wait for build** (5-10 minutes)
3. **Monitor logs** for any issues
4. **Test the deployment**

## 🧪 **Testing Your Deployment**

### **1. Health Check**
```bash
curl https://your-app-name.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0",
  "services": {
    "translation": "healthy",
    "medical_analysis": "healthy",
    "rag": "healthy"
  }
}
```

### **2. Language Matching Test**

#### **English Query → English Response**
```bash
curl -X POST "https://your-app-name.onrender.com/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What are the symptoms of diabetes?",
    "source_language": "en"
  }'
```

**Expected Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_query": "What are the symptoms of diabetes?",
  "source_language": "en",
  "target_language": "en",
  "translated_query": null,
  "response": "The symptoms of diabetes include: 1) Increased thirst and frequent urination...",
  "processing_time": 1.8,
  "metadata": {
    "rag_enabled": true,
    "documents_retrieved": 3,
    "model_used": "llama-3-8b-8192",
    "translation_used": false
  }
}
```

#### **Yoruba Query → Yoruba Response**
```bash
curl -X POST "https://your-app-name.onrender.com/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Kini awọn aami diabetes?",
    "source_language": "yo"
  }'
```

**Expected Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "original_query": "Kini awọn aami diabetes?",
  "source_language": "yo",
  "target_language": "yo",
  "translated_query": null,
  "response": "Awọn aami diabetes ni: 1) Igbẹ ti o pọ si ati igbẹ ti o ma n ṣe...",
  "processing_time": 1.9,
  "metadata": {
    "rag_enabled": true,
    "documents_retrieved": 3,
    "model_used": "llama-3-8b-8192",
    "translation_used": false
  }
}
```

### **3. Optional Translation Test**
```bash
curl -X POST "https://your-app-name.onrender.com/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What are the symptoms of diabetes?",
    "source_language": "en",
    "target_language": "yo",
    "translate_response": true
  }'
```

**Expected Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440002",
  "original_query": "What are the symptoms of diabetes?",
  "source_language": "en",
  "target_language": "yo",
  "translated_query": "Kini awọn aami diabetes?",
  "response": "Awọn aami diabetes ni: 1) Igbẹ ti o pọ si ati igbẹ ti o ma n ṣe...",
  "processing_time": 2.2,
  "metadata": {
    "rag_enabled": true,
    "documents_retrieved": 3,
    "model_used": "llama-3-8b-8192",
    "translation_used": true
  }
}
```

## 📊 **Performance Monitoring**

### **1. Render Dashboard**
- **Logs**: Real-time application logs
- **Metrics**: Response times, errors, usage
- **Health**: Service status and uptime

### **2. Application Metrics**
```bash
# Get application metrics
curl https://your-app-name.onrender.com/metrics

# Get query statistics
curl https://your-app-name.onrender.com/api/v1/query-stats
```

### **3. API Documentation**
- **Swagger UI**: `https://your-app-name.onrender.com/docs`
- **ReDoc**: `https://your-app-name.onrender.com/redoc`

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Build Failures**
```bash
# Check requirements.txt
pip install -r requirements.txt

# Verify Python version
python --version  # Should be 3.11+
```

#### **2. API Key Issues**
```bash
# Verify environment variables in Render dashboard
GROQ_API_KEY=your_actual_api_key_here
```

#### **3. Memory Issues**
- **Upgrade to Professional plan** for more resources
- **Reduce MAX_TOKENS** to 1024
- **Disable RAG** temporarily: `RAG_ENABLED=false`

#### **4. Slow Responses**
- **Check Groq API status**: [status.groq.com](https://status.groq.com)
- **Verify network connectivity**
- **Monitor Render logs** for bottlenecks

### **Debug Mode**
```bash
# Enable debug mode temporarily
DEBUG=true
LOG_LEVEL=DEBUG
```

## 📈 **Scaling Considerations**

### **Starter Plan Limitations**
- **512MB RAM**
- **0.1 CPU cores**
- **750 hours/month**
- **Sleep after 15 minutes of inactivity**

### **Professional Plan Benefits**
- **2GB RAM**
- **1 CPU core**
- **Unlimited hours**
- **Always on**
- **Custom domains**

### **When to Upgrade**
- **Response times > 5 seconds**
- **Memory usage > 80%**
- **High error rates**
- **Production traffic**

## 🔒 **Security Best Practices**

### **1. Environment Variables**
- **Never commit API keys** to repository
- **Use Render's secure environment variables**
- **Rotate API keys regularly**

### **2. CORS Configuration**
```bash
# For production, restrict CORS origins
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
```

### **3. Rate Limiting**
- **Monitor rate limit usage**
- **Adjust limits based on traffic**
- **Implement user authentication if needed**

## 🎯 **Production Checklist**

- [ ] **API Keys configured**
- [ ] **Health check passing**
- [ ] **Language matching working**
- [ ] **Optional translation working**
- [ ] **Response times < 3 seconds**
- [ ] **Error rate < 1%**
- [ ] **Monitoring enabled**
- [ ] **Backup API keys configured**
- [ ] **CORS properly configured**
- [ ] **Rate limits appropriate**

## 🚀 **Next Steps**

### **1. Custom Domain**
- **Add custom domain** in Render dashboard
- **Configure SSL certificate**
- **Update CORS origins**

### **2. Monitoring Setup**
- **Set up alerts** for downtime
- **Monitor response times**
- **Track usage metrics**

### **3. Performance Optimization**
- **Enable caching** for frequently asked questions
- **Optimize RAG retrieval**
- **Fine-tune LLM parameters**

Your HealthLang AI MVP is now deployed and optimized for fast, accurate responses with language-matching behavior! 🎉 