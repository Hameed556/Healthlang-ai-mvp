# Environment-Based Database Configuration

## 🎯 Overview

Your app now automatically selects the correct database based on the `ENVIRONMENT` variable:

- **`ENVIRONMENT=development`** → Uses local PostgreSQL (`DEV_DATABASE_URL`)
- **`ENVIRONMENT=production`** → Uses Render PostgreSQL (`PROD_DATABASE_URL`)

## 🔧 How It Works

### Development (Local)

```env
ENVIRONMENT=development
DEV_DATABASE_URL=postgresql://healthlang:Abdulhameed123@localhost:5432/healthlang
```

**Behavior:**
- ✅ Connects to your local PostgreSQL (Docker or installed)
- ✅ Uses `healthlang` database
- ✅ Test data stays on your machine

### Production (Render)

```env
ENVIRONMENT=production
PROD_DATABASE_URL=postgresql://healthlang_user:password@dpg-xxxxx.oregon-postgres.render.com/healthlang_production
```

**Behavior:**
- ✅ Connects to Render PostgreSQL
- ✅ Uses `healthlang_production` database
- ✅ Real production data in the cloud

## 📋 Setup Instructions

### For Local Development (Current Setup)

Your `.env` file already configured! Just ensure:

```env
ENVIRONMENT=development
DEV_DATABASE_URL=postgresql://healthlang:Abdulhameed123@localhost:5432/healthlang
```

**Test it:**
```bash
python -m uvicorn app.main:app --reload
```

You should see in logs:
```
Environment: development
Using database: localhost:5432/healthlang
Database connection successful
```

### For Render Production

1. **Get Database URL from Render:**
   - Go to your `healthlang-db` PostgreSQL dashboard
   - Copy the **External Database URL**
   - It looks like: `postgresql://healthlang_user:xxxxx@dpg-d5b8slpr0fns738phlfg-a.oregon-postgres.render.com/healthlang_production`

2. **Add to Render Web Service:**
   - Go to your web service dashboard
   - Click "Environment" in sidebar
   - Add these variables:

   ```env
   ENVIRONMENT=production
   PROD_DATABASE_URL=postgresql://healthlang_user:xxxxx@dpg-xxxxx.oregon-postgres.render.com/healthlang_production
   ```

3. **Deploy:**
   - Render auto-deploys on save
   - Check logs for:
   ```
   Environment: production
   Using database: dpg-xxxxx.oregon-postgres.render.com/healthlang_production
   Database connection successful
   ```

## 🔍 Priority Order

The system checks in this order:

1. **`DATABASE_URL`** (if set) → Uses this directly (backward compatibility)
2. **`ENVIRONMENT=production`** → Uses `PROD_DATABASE_URL`
3. **`ENVIRONMENT=development`** → Uses `DEV_DATABASE_URL`
4. **Fallback** → Uses `DEV_DATABASE_URL` if production URL missing

## ✅ Verify Configuration

### Local Test:
```bash
# In your terminal
python -c "from app.config import settings; print(f'Environment: {settings.ENVIRONMENT}'); print(f'Database: {settings.get_database_url}')"
```

**Expected output (development):**
```
Environment: development
Database: postgresql://healthlang:Abdulhameed123@localhost:5432/healthlang
```

### Render Test:
Check your deployment logs in Render dashboard for:
```
Environment: production
Using database: dpg-xxxxx.oregon-postgres.render.com/healthlang_production
```

## 🚨 Important Notes

### Security
- ✅ Never commit `.env` to Git (already in `.gitignore`)
- ✅ Production credentials only in Render dashboard
- ✅ Use strong passwords in production

### Data Separation
- 🏠 **Local data** stays on your PC
- ☁️ **Production data** stays in Render cloud
- 🔒 They never mix or interfere

### Migration
Your existing local data stays intact. Production starts with empty tables that auto-create on first deployment.

## 📚 Files Changed

1. **`app/config.py`**
   - Added `DEV_DATABASE_URL` and `PROD_DATABASE_URL`
   - Added `get_database_url` property for smart selection

2. **`app/database.py`**
   - Uses `settings.get_database_url` instead of hardcoded URL
   - Logs which database is being used

3. **`.env`**
   - Added `DEV_DATABASE_URL` for local development
   - Added commented `PROD_DATABASE_URL` example

4. **`.env.production.example`**
   - Template for Render environment variables
   - Copy values to Render dashboard (not to be used as file)

## 🎉 Benefits

✅ **No code changes needed** when switching environments
✅ **Automatic detection** based on `ENVIRONMENT` variable
✅ **Safe separation** of dev and prod data
✅ **Easy testing** locally before production deployment
✅ **Backward compatible** with existing `DATABASE_URL` setups

## 🆘 Troubleshooting

### Issue: "Database connection failed" in production

**Solution:**
1. Check `ENVIRONMENT=production` is set in Render
2. Verify `PROD_DATABASE_URL` is correct (use External URL from Render PostgreSQL)
3. Ensure format: `postgresql://user:pass@host.render.com/database`

### Issue: Using wrong database

**Check logs:**
```
Environment: development  ← Should be "production" on Render
Using database: localhost:5432  ← Should be "render.com" on Render
```

**Fix:** Set `ENVIRONMENT=production` in Render environment variables

### Issue: "PROD_DATABASE_URL not set"

**Solution:** Add the External Database URL from your Render PostgreSQL to `PROD_DATABASE_URL` in Render web service environment variables.
