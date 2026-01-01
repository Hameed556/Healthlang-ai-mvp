# PostgreSQL Setup Without Docker

## Why You Can't Find Docker Files

**Docker is not installed on your system.** That's why:
- `docker` and `docker compose` commands don't work
- No PostgreSQL container is running
- No Docker volumes exist in ProgramData

## Solution: Install PostgreSQL Directly on Windows

### Option A: PostgreSQL Native Installation (Recommended for Development)

#### Step 1: Download PostgreSQL
1. Go to: https://www.postgresql.org/download/windows/
2. Download the Windows installer (latest version, e.g., PostgreSQL 15 or 16)
3. Run the installer

#### Step 2: Install PostgreSQL
1. **Installation Directory**: `C:\Program Files\PostgreSQL\15\`
2. **Port**: `5432` (default)
3. **Password**: Set a password for the `postgres` superuser (remember this!)
4. **Locale**: Default
5. **Components**: Install all (PostgreSQL Server, pgAdmin, Command Line Tools)

#### Step 3: Create Database and User

Open **pgAdmin** (installed with PostgreSQL) or use **SQL Shell (psql)**:

```sql
-- Connect as postgres superuser
-- Password: [the one you set during installation]

-- Create database
CREATE DATABASE healthlang;

-- Create user
CREATE USER healthlang WITH PASSWORD 'healthlang_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE healthlang TO healthlang;

-- Connect to healthlang database
\c healthlang

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO healthlang;
```

#### Step 4: Update Your .env File

```env
# Change from Docker connection to local Windows connection
DATABASE_URL=postgresql://healthlang:healthlang_password@localhost:5432/healthlang

POSTGRES_DB=healthlang
POSTGRES_USER=healthlang
POSTGRES_PASSWORD=healthlang_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

#### Step 5: Verify Connection

```bash
# In PowerShell
cd C:\Users\user\Documents\Healthlang-ai-mvp
.\.venv\Scripts\Activate.ps1

# Test database connection
python -c "from app.database import check_database_connection; import asyncio; asyncio.run(check_database_connection())"
```

#### Step 6: Start Your Application

```bash
# Run the FastAPI app
python -m uvicorn app.main:app --reload
```

The application will automatically create the database tables on startup!

---

### Option B: Use SQLite (Simplest - No Installation Required)

If you just want to test without installing anything:

#### Update .env to use SQLite

```env
# Use SQLite instead of PostgreSQL
DATABASE_URL=sqlite:///./healthlang.db

# Comment out PostgreSQL settings
# POSTGRES_DB=healthlang
# POSTGRES_USER=healthlang
# POSTGRES_PASSWORD=healthlang_password
```

#### SQLite Data Location

Your chat data will be saved in:
```
C:\Users\user\Documents\Healthlang-ai-mvp\healthlang.db
```

This is a **single file** you can:
- Open with [DB Browser for SQLite](https://sqlitebrowser.org/)
- Copy/backup easily
- View tables and data directly

---

## Comparison: PostgreSQL vs SQLite vs Docker

| Feature | Docker + PostgreSQL | Native PostgreSQL | SQLite |
|---------|-------------------|------------------|--------|
| Installation | Complex (needs Docker Desktop) | Medium (PostgreSQL installer) | **Easy (already works!)** |
| Performance | ⭐⭐⭐⭐⭐ Production-ready | ⭐⭐⭐⭐⭐ Production-ready | ⭐⭐⭐ Good for dev |
| Multi-user | ✅ Yes | ✅ Yes | ❌ Limited |
| Data Location | Docker volume (hidden) | `C:\Program Files\PostgreSQL\` | **Single .db file** |
| Portability | Container portable | Server installation | **Very portable** |
| Backup | Volume backup | Database dump | **Copy .db file** |
| Tools | pgAdmin in container | **pgAdmin included** | **DB Browser** |
| Best For | Production deployment | Development + Production | **Quick testing** |

---

## Quick Start: Use SQLite (No Installation)

**Your app already supports SQLite!** Just update `.env`:

1. Open `.env` file
2. Change:
   ```env
   DATABASE_URL=sqlite:///./healthlang.db
   ```

3. Run app:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

4. Your data will be in `healthlang.db` file

5. View data with [DB Browser for SQLite](https://sqlitebrowser.org/):
   - Download and install DB Browser
   - Open `healthlang.db`
   - Click "Browse Data" tab
   - Select "users" or "queries" table
   - See all your chat data! ✅

---

## Where is Data Stored? (Summary)

### With Docker (Not Installed Yet)
```
Location: Hidden in Docker volume
Access: docker exec -it container psql
```

### With Native PostgreSQL
```
Location: C:\Program Files\PostgreSQL\15\data\
Access: pgAdmin or psql command
```

### With SQLite ⭐ EASIEST
```
Location: C:\Users\user\Documents\Healthlang-ai-mvp\healthlang.db
Access: Open file with DB Browser for SQLite
Can see tables, data, everything!
```

---

## My Recommendation for You

Since Docker is not installed, I recommend:

### For Testing (Right Now):
**Use SQLite** - It's already configured and working! Just need to update `.env`.

### For Production (Later):
**Install Docker Desktop** and use the docker-compose.yml setup.

OR

**Install PostgreSQL natively** on Windows for a more robust solution without Docker complexity.

---

## Next Steps

1. **Choose your option** above
2. **Update `.env` file** accordingly
3. **Run the application**
4. **Test it** with user registration and queries

Want me to help you set up SQLite right now? It's the fastest way to see your data! 🚀
