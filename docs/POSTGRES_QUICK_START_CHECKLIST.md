# PostgreSQL Implementation - Quick Start Checklist

## ✅ Step-by-Step Checklist

### Phase 1: Installation (15 minutes)

- [ ] **Step 1.1:** Download Docker Desktop
  - URL: https://www.docker.com/products/docker-desktop/
  - File: ~500 MB

- [ ] **Step 1.2:** Install Docker Desktop
  - Run installer
  - Check "Use WSL 2"
  - Wait for installation
  
- [ ] **Step 1.3:** Restart Computer
  - Important: Must restart!

- [ ] **Step 1.4:** Start Docker Desktop
  - Find in Start Menu
  - Wait for whale icon to be steady
  
- [ ] **Step 1.5:** Verify Docker Installation
  ```powershell
  docker --version
  docker compose version
  ```

---

### Phase 2: Start PostgreSQL (5 minutes)

- [ ] **Step 2.1:** Open PowerShell
  ```powershell
  cd C:\Users\user\Documents\Healthlang-ai-mvp
  ```

- [ ] **Step 2.2:** Start PostgreSQL Container
  ```powershell
  docker compose up postgres -d
  ```

- [ ] **Step 2.3:** Verify Container is Running
  ```powershell
  docker ps
  # Should see: healthlang-postgres
  ```

- [ ] **Step 2.4:** Check PostgreSQL Logs
  ```powershell
  docker logs healthlang-postgres
  # Should see: "ready to accept connections"
  ```

- [ ] **Step 2.5:** Test Database Connection
  ```powershell
  docker exec -it healthlang-postgres psql -U healthlang -d healthlang
  # Type: \q to exit
  ```

---

### Phase 3: Start Application (5 minutes)

- [ ] **Step 3.1:** Activate Virtual Environment
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

- [ ] **Step 3.2:** Test Database Connection from Python
  ```powershell
  python -c "from app.database import check_database_connection; import asyncio; asyncio.run(check_database_connection())"
  ```

- [ ] **Step 3.3:** Start FastAPI Application
  ```powershell
  python -m uvicorn app.main:app --reload
  ```

- [ ] **Step 3.4:** Test Health Endpoint
  ```powershell
  # In new PowerShell window
  curl http://localhost:8000/health
  ```

---

### Phase 4: Test User Registration (5 minutes)

- [ ] **Step 4.1:** Register a New User
  ```powershell
  curl -X POST http://localhost:8000/api/v1/auth/register `
    -H "Content-Type: application/json" `
    -d '{\"username\": \"testuser\", \"email\": \"test@example.com\", \"password\": \"SecurePass123\", \"full_name\": \"Test User\"}'
  ```

- [ ] **Step 4.2:** Copy the Access Token
  - Save the `access_token` from response

- [ ] **Step 4.3:** Verify User in Database
  ```powershell
  docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT username, email FROM users;"
  ```

---

### Phase 5: Test Query Storage (5 minutes)

- [ ] **Step 5.1:** Make an Authenticated Query
  ```powershell
  # Replace YOUR_TOKEN_HERE with actual token
  curl -X POST http://localhost:8000/api/v1/query `
    -H "Content-Type: application/json" `
    -H "Authorization: Bearer YOUR_TOKEN_HERE" `
    -d '{\"text\": \"What are the symptoms of diabetes?\"}'
  ```

- [ ] **Step 5.2:** Make Another Query
  ```powershell
  curl -X POST http://localhost:8000/api/v1/query `
    -H "Content-Type: application/json" `
    -H "Authorization: Bearer YOUR_TOKEN_HERE" `
    -d '{\"text\": \"What causes high blood pressure?\"}'
  ```

- [ ] **Step 5.3:** Verify Queries in Database
  ```powershell
  docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT id, query_text, timestamp FROM queries ORDER BY timestamp DESC;"
  ```

---

### Phase 6: View Data (5 minutes)

- [ ] **Step 6.1:** View All Users
  ```powershell
  docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT * FROM users;"
  ```

- [ ] **Step 6.2:** View All Queries
  ```powershell
  docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT * FROM queries ORDER BY timestamp DESC LIMIT 5;"
  ```

- [ ] **Step 6.3:** View User's Complete History
  ```powershell
  docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT u.username, q.query_text, q.timestamp FROM users u JOIN queries q ON u.id = q.user_id ORDER BY q.timestamp DESC;"
  ```

---

## 🎯 What Data is Now Being Stored

### ✅ Currently Stored (Working Now!)

1. **User Accounts**
   - Username, email, password (encrypted)
   - Full name, language preference
   - Account status, verification status
   - Creation date, last login

2. **Query History (Chat History)**
   - User's questions
   - AI's responses
   - Processing time
   - Success/failure status
   - Sources used (PubMed, WHO, etc.)
   - Metadata (RAG sources, MCP tools)
   - Timestamps

3. **Translation History**
   - Original text, translated text
   - Source and target languages
   - Translation confidence
   - Timestamps

### 🔜 Can Be Added (Future Enhancement)

4. **User Preferences**
   - Theme (light/dark)
   - Notification settings
   - Medical conditions
   - Allergies, medications

5. **Conversations**
   - Group queries into threads
   - Conversation titles
   - Archive old chats

6. **Feedback**
   - Query ratings (1-5 stars)
   - Helpful/not helpful
   - User comments

7. **Analytics**
   - Page views
   - Feature usage
   - Popular questions
   - User behavior

---

## 🔄 How Data Syncs Automatically

```
USER ACTION          WHAT HAPPENS                 WHERE STORED
──────────────────────────────────────────────────────────────

Register Account
   ↓
POST /auth/register  → create_user()           → users table
                       (Python code)              (PostgreSQL)
                       ✅ Auto-saved!

Login
   ↓
POST /auth/login     → authenticate_user()     → users table
                       UPDATE last_login          (updated)
                       ✅ Auto-updated!

Ask Question
   ↓
POST /query          → process_query()         → queries table
                       → create_query_record()    (PostgreSQL)
                       ✅ Auto-saved!

View History
   ↓
GET /queries/history → get_user_history()     ← queries table
                       ✅ Auto-retrieved!
```

**Everything is AUTOMATIC - No manual work needed!** 🎉

---

## 📊 Quick Commands Reference

```powershell
# ===== DOCKER COMMANDS =====

# Start PostgreSQL
docker compose up postgres -d

# Stop PostgreSQL
docker compose stop postgres

# Stop and remove PostgreSQL
docker compose down postgres

# View logs
docker logs healthlang-postgres

# Follow logs (live)
docker logs -f healthlang-postgres

# Restart PostgreSQL
docker compose restart postgres


# ===== DATABASE COMMANDS =====

# Connect to database
docker exec -it healthlang-postgres psql -U healthlang -d healthlang

# Inside psql:
\dt                  # List all tables
\d users             # Describe users table
\d queries           # Describe queries table
SELECT * FROM users; # View all users
\q                   # Exit psql

# Run SQL command directly
docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c "SELECT * FROM users;"


# ===== APPLICATION COMMANDS =====

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start application
python -m uvicorn app.main:app --reload

# Test health endpoint
curl http://localhost:8000/health

# Test database connection
python -c "from app.database import check_database_connection; import asyncio; asyncio.run(check_database_connection())"


# ===== BACKUP/RESTORE =====

# Backup database
docker exec healthlang-postgres pg_dump -U healthlang healthlang > backup.sql

# Restore database
docker exec -i healthlang-postgres psql -U healthlang healthlang < backup.sql

# Export table to CSV
docker exec healthlang-postgres psql -U healthlang -d healthlang -c "COPY queries TO STDOUT CSV HEADER" > queries.csv
```

---

## ⚠️ Troubleshooting

### Problem: Docker not recognized

**Solution:**
```powershell
# Make sure Docker Desktop is running
# Check system tray for Docker whale icon
# Try restarting Docker Desktop
```

### Problem: PostgreSQL not starting

**Solution:**
```powershell
# Check logs
docker logs healthlang-postgres

# Remove and recreate
docker compose down postgres
docker compose up postgres -d
```

### Problem: Can't connect to database

**Solution:**
```powershell
# Check if container is running
docker ps

# Check .env file has correct DATABASE_URL
cat .env | Select-String "DATABASE_URL"

# Should be:
# DATABASE_URL=postgresql://healthlang:healthlang_password@localhost:5432/healthlang
```

### Problem: Tables not created

**Solution:**
```powershell
# Stop app, restart to trigger init_db()
# Or manually create:
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

---

## 🎓 What You've Learned

After completing this checklist:

✅ Installed Docker Desktop
✅ Started PostgreSQL container
✅ Connected application to database
✅ Registered users and stored in database
✅ Made queries and stored chat history
✅ Viewed data using SQL commands
✅ Understood automatic data synchronization

---

## 📚 Documentation Reference

- **Complete Setup Guide**: `docs/COMPLETE_POSTGRES_SETUP_GUIDE.md`
- **Visual Data Guide**: `docs/DATA_STORAGE_VISUAL_GUIDE.md`
- **Production Q&A**: `docs/PRODUCTION_QUESTIONS_ANSWERED.md`
- **Quick Answer**: `docs/QUICK_ANSWER_POSTGRES.md`
- **Storage Explained**: `docs/DATABASE_STORAGE_EXPLAINED.md`

---

## 🚀 Next Steps

1. **Add More Features:**
   - User preferences table
   - Conversation threads
   - Feedback system
   - Analytics tracking

2. **Create API Endpoints:**
   - GET /api/v1/queries/history (view history)
   - DELETE /api/v1/queries/{id} (delete query)
   - GET /api/v1/stats (user statistics)

3. **Build Dashboard:**
   - User profile page
   - Chat history viewer
   - Analytics visualization

4. **Deploy to Production:**
   - Render.com (free tier)
   - AWS RDS (production)
   - DigitalOcean (self-hosted)

---

## ✨ Success Criteria

You'll know everything is working when:

- [ ] Docker shows PostgreSQL container running
- [ ] App starts without errors
- [ ] User registration returns a token
- [ ] Queries are saved and retrievable
- [ ] Database contains user and query data
- [ ] Data persists after container restart

---

**Total Time: ~40 minutes**
**Difficulty: Easy (step-by-step)**
**Result: Production-ready database system!** 🎉
