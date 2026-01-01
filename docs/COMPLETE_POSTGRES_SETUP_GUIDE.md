# Complete Step-by-Step PostgreSQL Implementation Guide

## 📋 Table of Contents
1. [Install Docker Desktop](#step-1-install-docker-desktop)
2. [Verify Docker Installation](#step-2-verify-docker-installation)
3. [Start PostgreSQL Container](#step-3-start-postgresql-container)
4. [Verify PostgreSQL is Running](#step-4-verify-postgresql-is-running)
5. [Test Database Connection](#step-5-test-database-connection)
6. [Run Your Application](#step-6-run-your-application)
7. [Test User Registration](#step-7-test-user-registration)
8. [Test Query History Storage](#step-8-test-query-history-storage)
9. [View Stored Data](#step-9-view-stored-data)
10. [What Data to Store](#what-data-to-store)

---

## Step 1: Install Docker Desktop

### Windows Installation

1. **Download Docker Desktop**
   - Click "Download for Windows"
   - File size: ~500 MB     

2. **System Requirements**
   - Windows 10 64-bit: Pro, Enterprise, or Education (Build 19041 or higher)
   - OR Windows 11
   - Enable "Virtualization" in BIOS (usually enabled by default)
   - WSL 2 (Windows Subsystem for Linux) will be installed automatically

3. **Install Docker Desktop**
   ```
   1. Run the installer (Docker Desktop Installer.exe)
   2. Follow the installation wizard
   3. Check "Use WSL 2 instead of Hyper-V" (recommended)
   4. Click "Install"
   5. Wait 5-10 minutes for installation
   6. Click "Close" when done
   ```

4. **Restart Your Computer**
   ```
   Important: Restart Windows after installation
   ```

5. **Start Docker Desktop**
   ```
   1. Search for "Docker Desktop" in Start Menu
   2. Launch the application
   3. Wait for Docker to start (whale icon in system tray turns steady)
   4. Accept the Docker Subscription Service Agreement
   5. Skip the tutorial (optional)
   ```

6. **Verify Docker is Running**
   - Look for Docker whale icon in system tray (bottom-right)
   - Icon should be steady (not animating)
   - If animating, Docker is still starting

---

## Step 2: Verify Docker Installation

Open **PowerShell** and run:

```powershell
# Check Docker version
docker --version
```

**Expected Output:**
```
Docker version 24.0.6, build ed223bc
```

```powershell
# Check Docker Compose version
docker compose version
```

**Expected Output:**
```
Docker Compose version v2.23.0
```

```powershell
# Test Docker is working
docker run hello-world
```

**Expected Output:**
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

✅ **If you see these outputs, Docker is installed correctly!**

---

## Step 3: Start PostgreSQL Container

### Navigate to Your Project

```powershell
# Open PowerShell
cd C:\Users\user\Documents\Healthlang-ai-mvp
```

### Check Your Configuration Files

```powershell
# Verify .env file exists
cat .env | Select-String "DATABASE_URL"
```

**Expected Output:**
```
DATABASE_URL=postgresql://healthlang:healthlang_password@localhost:5432/healthlang
```

✅ **Good! PostgreSQL is configured.**

### Start PostgreSQL Container

```powershell
# Start only PostgreSQL (not the whole stack)
docker compose up postgres -d
```

**What This Does:**
- `docker compose up` - Starts services defined in docker-compose.yml
- `postgres` - Only starts the PostgreSQL service
- `-d` - Detached mode (runs in background)

**Expected Output:**
```
[+] Running 2/2
 ⠿ Network healthlang-ai-mvp_healthlang-network  Created
 ⠿ Container healthlang-postgres                 Started
```

✅ **PostgreSQL is now running!**

---

## Step 4: Verify PostgreSQL is Running

### Check Running Containers

```powershell
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE               COMMAND                  STATUS         PORTS                    NAMES
a1b2c3d4e5f6   postgres:15-alpine  "docker-entrypoint.s…"   Up 10 seconds  0.0.0.0:5432->5432/tcp   healthlang-postgres
```

✅ **You should see `healthlang-postgres` in the list!**

### Check Container Logs

```powershell
docker logs healthlang-postgres
```

**Expected Output (last few lines):**
```
PostgreSQL init process complete; ready for start up.

LOG:  database system is ready to accept connections
```

✅ **"ready to accept connections" means PostgreSQL is working!**

### Test Database Connection

```powershell
# Connect to PostgreSQL inside the container
docker exec -it healthlang-postgres psql -U healthlang -d healthlang
```

**You'll see a PostgreSQL prompt:**
```
psql (15.4)
Type "help" for help.

healthlang=#
```

**Try some commands:**
```sql
-- List all databases
\l

-- List all tables (should be empty for now)
\dt

-- Check current database
SELECT current_database();

-- Exit
\q
```

✅ **If you can run these commands, PostgreSQL is working perfectly!**

---

## Step 5: Test Database Connection from Python

### Activate Your Virtual Environment

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

**Your prompt should now show `(.venv)`**

### Test Database Connection

```powershell
# Test database connection
python -c "from app.database import check_database_connection; import asyncio; asyncio.run(check_database_connection())"
```

**Expected Output:**
```
2025-10-29 10:30:00 | INFO | Database connection successful
2025-10-29 10:30:00 | INFO | PostgreSQL version: 15.4
```

✅ **Connection successful!**

---

## Step 6: Run Your Application

### Start the FastAPI Application

```powershell
# Make sure virtual environment is activated
# (.venv should appear in your prompt)

# Start the application
python -m uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['C:\\Users\\user\\Documents\\Healthlang-ai-mvp']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**What Happens on Startup:**
1. App connects to PostgreSQL
2. Creates database tables automatically (`users`, `queries`, `translations`)
3. Sets up API routes
4. Ready to accept requests

✅ **Application is running!**

### Verify API is Working

Open a **new PowerShell window** (keep the app running in the first one):

```powershell
# Test health endpoint
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-29T10:30:00Z"
}
```

✅ **API is working!**

---

## Step 7: Test User Registration

### Register a New User

```powershell
# Create a new user
curl -X POST http://localhost:8000/api/v1/auth/register `
  -H "Content-Type: application/json" `
  -d '{\"username\": \"testuser\", \"email\": \"test@example.com\", \"password\": \"SecurePass123\", \"full_name\": \"Test User\"}'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-12345",
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "preferred_language": "en",
    "is_active": true,
    "is_verified": false
  }
}
```

**Copy the `access_token` value - you'll need it!**

✅ **User registered and saved to PostgreSQL!**

### Verify User in Database

```powershell
# Check if user was saved
docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT username, email, created_at FROM users;"
```

**Expected Output:**
```
 username  |       email        |         created_at
-----------+--------------------+----------------------------
 testuser  | test@example.com   | 2025-10-29 10:35:00.123456
(1 row)
```

✅ **User data is in PostgreSQL!**

---

## Step 8: Test Query History Storage

### Make an Authenticated Query

Replace `YOUR_TOKEN_HERE` with the token from Step 7:

```powershell
# Make a medical query (authenticated)
curl -X POST http://localhost:8000/api/v1/query `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_TOKEN_HERE" `
  -d '{\"text\": \"What are the symptoms of diabetes?\"}'
```

**Expected Response:**
```json
{
  "request_id": "uuid-67890",
  "original_query": "What are the symptoms of diabetes?",
  "response": "Diabetes symptoms include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, blurred vision...",
  "processing_time": 2.45,
  "timestamp": "2025-10-29T10:40:00Z",
  "metadata": {
    "mcp_tools_used": ["pubmed_search", "health_topics"],
    "rag_used": true,
    "sources": ["PubMed", "WHO"]
  },
  "success": true
}
```

✅ **Query processed successfully!**

### Make Another Query

```powershell
# Ask another question
curl -X POST http://localhost:8000/api/v1/query `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_TOKEN_HERE" `
  -d '{\"text\": \"What causes high blood pressure?\"}'
```

✅ **Another query stored!**

---

## Step 9: View Stored Data

### Check Query History in Database

```powershell
# View all queries
docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT id, user_id, query_text, success, timestamp FROM queries ORDER BY timestamp DESC LIMIT 5;"
```

**Expected Output:**
```
         id          |      user_id       |          query_text           | success |         timestamp
---------------------+--------------------+-------------------------------+---------+---------------------------
 query-uuid-2        | user-uuid-1        | What causes high blood...     | t       | 2025-10-29 10:45:00
 query-uuid-1        | user-uuid-1        | What are the symptoms...      | t       | 2025-10-29 10:40:00
(2 rows)
```

✅ **All queries are stored with timestamps!**

### View Complete Query Details

```powershell
# View full query details including response
docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT query_text, response_text, processing_time FROM queries ORDER BY timestamp DESC LIMIT 1;"
```

### View User's Complete History

```powershell
# Join users and queries tables
docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT u.username, q.query_text, q.timestamp FROM users u JOIN queries q ON u.id = q.user_id ORDER BY q.timestamp DESC;"
```

**Expected Output:**
```
 username  |          query_text              |         timestamp
-----------+----------------------------------+---------------------------
 testuser  | What causes high blood pressure? | 2025-10-29 10:45:00
 testuser  | What are the symptoms...         | 2025-10-29 10:40:00
(2 rows)
```

✅ **Perfect! User history is linked and stored!**

---

## What Data to Store in PostgreSQL

Your application already stores these tables:

### 1. **USERS Table** - User Account Information

**What's Stored:**
```python
- id (UUID)                    # Unique user identifier
- username                     # Login username
- email                        # User email address
- hashed_password             # Encrypted password (bcrypt)
- full_name                   # User's full name
- preferred_language          # Language preference (en, fr, es, etc.)
- is_active                   # Account status (active/disabled)
- is_verified                 # Email verification status
- created_at                  # When account was created
- updated_at                  # Last profile update
- last_login                  # Last login timestamp
```

**Use Cases:**
- User authentication
- Profile management
- Account settings
- Access control

---

### 2. **QUERIES Table** - Chat History & Medical Queries

**What's Stored:**
```python
- id (UUID)                    # Unique query identifier
- user_id (Foreign Key)       # Links to users table
- query_text                  # User's question
- response_text               # AI's response
- query_type                  # Type: medical, general, emergency
- language                    # Query language
- analysis                    # Detailed medical analysis
- recommendations (JSON)      # Medical recommendations list
- safety_level                # safe, caution, emergency
- confidence_score            # AI confidence (0.0-1.0)
- sources (JSON)              # List of sources used
- processing_time             # Time taken to process
- success                     # Query success status
- error                       # Error message if failed
- request_metadata (JSON)     # RAG sources, MCP tools, etc.
- timestamp                   # When query was made
- created_at                  # Same as timestamp
```

**Use Cases:**
- Chat history
- User conversation tracking
- Analytics (most asked questions)
- Quality monitoring
- Medical insights tracking
- Source attribution

---

### 3. **TRANSLATIONS Table** - Translation History

**What's Stored:**
```python
- id (UUID)                    # Unique translation identifier
- user_id (Foreign Key)       # Links to users table
- original_text               # Text before translation
- translated_text             # Text after translation
- source_language             # Original language
- target_language             # Target language
- confidence_score            # Translation confidence
- processing_time             # Time taken
- context                     # Medical context
- preserve_formatting         # Whether formatting was kept
- request_metadata (JSON)     # Additional metadata
- created_at                  # When translation was done
```

**Use Cases:**
- Translation history
- Multi-language support
- Translation quality tracking
- Language preferences

---

## Additional Data You Can Store

### 4. **USER_PREFERENCES Table** (To Add)

```python
class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    
    # UI Preferences
    theme = Column(String(20), default="light")  # light, dark
    font_size = Column(String(10), default="medium")
    
    # Notification Settings
    email_notifications = Column(Boolean, default=True)
    query_reminders = Column(Boolean, default=False)
    
    # Privacy Settings
    save_history = Column(Boolean, default=True)
    allow_analytics = Column(Boolean, default=True)
    
    # Medical Preferences
    medical_conditions = Column(JSON)  # List of conditions
    allergies = Column(JSON)  # List of allergies
    medications = Column(JSON)  # Current medications
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

**Use Cases:**
- Personalized experience
- Better medical recommendations
- Privacy control
- User settings

---

### 5. **CONVERSATIONS Table** (To Add)

```python
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    title = Column(String(200))  # Auto-generated or user-set
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    is_archived = Column(Boolean, default=False)
    
    # Relationship
    queries = relationship("Query", back_populates="conversation")
```

**Links queries together in conversation threads:**
- Chat history organization
- Topic-based grouping
- Easier navigation
- Archive old conversations

---

### 6. **FEEDBACK Table** (To Add)

```python
class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    query_id = Column(String(36), ForeignKey("queries.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    
    rating = Column(Integer)  # 1-5 stars
    helpful = Column(Boolean)  # Thumbs up/down
    accuracy = Column(Integer)  # 1-5
    completeness = Column(Integer)  # 1-5
    comment = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
```

**Use Cases:**
- Quality improvement
- AI model training
- User satisfaction tracking
- Identify problematic responses

---

### 7. **SEARCH_HISTORY Table** (To Add)

```python
class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    search_query = Column(Text)
    results_count = Column(Integer)
    clicked_result = Column(String(255))
    search_type = Column(String(50))  # medical, general, tavily
    created_at = Column(DateTime, server_default=func.now())
```

**Use Cases:**
- Search analytics
- Popular topics
- Search optimization
- Autocomplete suggestions

---

### 8. **ANALYTICS_EVENTS Table** (To Add)

```python
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50))  # page_view, button_click, etc.
    event_data = Column(JSON)
    session_id = Column(String(36))
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
```

**Use Cases:**
- User behavior analytics
- Feature usage tracking
- Performance monitoring
- A/B testing

---

## How Data Syncs with PostgreSQL

### Automatic Synchronization Flow

```
USER ACTION                    PYTHON CODE                    POSTGRESQL
────────────────────────────────────────────────────────────────────────

1. Register Account
   ↓
   POST /api/v1/auth/register
                               create_user()
                                    ↓
                               SQLAlchemy ORM
                                    ↓
                               INSERT INTO users...
                                                              ✅ User saved
                                                              
2. Login
   ↓
   POST /api/v1/auth/login
                               authenticate_user()
                                    ↓
                               SELECT FROM users...
                                                              ✅ User retrieved
                               UPDATE last_login...
                                                              ✅ Login time saved

3. Ask Question
   ↓
   POST /api/v1/query
                               process_query()
                                    ↓
                               create_query_record()
                                    ↓
                               INSERT INTO queries...
                                                              ✅ Query saved
                                                              
4. View History
   ↓
   GET /api/v1/queries/history
                               get_user_query_history()
                                    ↓
                               SELECT FROM queries
                               WHERE user_id = ...
                                                              ✅ History retrieved
```

### Real-Time Synchronization

**Every API call automatically syncs with PostgreSQL:**

```python
# app/api/routes/query.py

@router.post("/query")
async def process_medical_query(...):
    # 1. User makes request
    query_text = request.text
    
    # 2. Process with AI
    result = await workflow.process_query(query_text)
    
    # 3. ⚡ AUTOMATICALLY SAVE TO POSTGRES ⚡
    await QueryService.create_query_record(
        db=db,                           # Database session
        user_id=current_user.id,         # Links to user
        query_text=query_text,           # Question
        response_text=result["response"], # Answer
        processing_time=1.5,             # Performance metric
        success=True,                    # Status
        sources=result.get("sources"),   # Attribution
        metadata=result.get("metadata")  # Additional info
    )
    # ↑ This line saves to PostgreSQL instantly!
    
    # 4. Return response to user
    return response
```

**No manual work needed - it's all automatic!** ✅

---

## Data Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE RELATIONSHIPS                    │
└─────────────────────────────────────────────────────────────┘

         ┌─────────────┐
         │   USERS     │
         ├─────────────┤
         │ id          │◄──────────────────┐
         │ username    │                   │
         │ email       │                   │
         │ password    │                   │
         └─────────────┘                   │
                │                          │
                │ One user has             │
                │ many queries             │
                ↓                          │
         ┌─────────────┐                  │
         │  QUERIES    │                  │
         ├─────────────┤                  │
         │ id          │                  │
         │ user_id     │──────────────────┘ (Foreign Key)
         │ query_text  │
         │ response    │
         │ timestamp   │
         └─────────────┘
                │
                │ One query can have
                │ multiple feedback
                ↓
         ┌─────────────┐
         │  FEEDBACK   │
         ├─────────────┤
         │ id          │
         │ query_id    │────────┐
         │ user_id     │        │ (Foreign Key)
         │ rating      │        │
         └─────────────┘        │
                                ↓
                    Links back to specific query
```

---

## Summary - What You've Accomplished

After completing this guide, you have:

✅ **Docker Desktop installed and running**
✅ **PostgreSQL container running**
✅ **Database tables created automatically**
✅ **Application connected to PostgreSQL**
✅ **User registration working and saving data**
✅ **Query history being tracked**
✅ **All data persisting across restarts**

---

## Quick Reference Commands

```powershell
# Start PostgreSQL
docker compose up postgres -d

# Stop PostgreSQL
docker compose down postgres

# View PostgreSQL logs
docker logs healthlang-postgres

# Connect to database
docker exec -it healthlang-postgres psql -U healthlang -d healthlang

# Start your app
python -m uvicorn app.main:app --reload

# View all users
docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT * FROM users;"

# View all queries
docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT * FROM queries ORDER BY timestamp DESC LIMIT 10;"

# Backup database
docker exec healthlang-postgres pg_dump -U healthlang healthlang > backup.sql

# Restore database
docker exec -i healthlang-postgres psql -U healthlang healthlang < backup.sql
```

---

## Next Steps

1. **Add more tables** (preferences, feedback, analytics)
2. **Create API endpoints** to retrieve history
3. **Build a dashboard** to visualize data
4. **Set up automated backups**
5. **Deploy to production** (Render, AWS, etc.)

🎉 **You now have a production-ready PostgreSQL setup!**
