# PostgreSQL Implementation Guide

## Overview
This document explains the complete PostgreSQL implementation for the HealthLang AI MVP, including user accounts, query history, persistent RAG cache, and conversation memory.

## System Architecture

### Database Components

1. **PostgreSQL Database**
   - Container: `postgres:15-alpine`
   - Port: `5432`
   - Database: `healthlang`
   - User: `healthlang`
   - Password: `healthlang_password`

2. **Tables**
   - `users` - User accounts with authentication
   - `queries` - Query history with responses and metadata
   - `translations` - Translation history (future use)

3. **Data Persistence**
   - PostgreSQL data stored in Docker volume
   - ChromaDB vectors stored in `./data/chroma`
   - Application logs in `./logs/`

## Setup Instructions

### 1. Start PostgreSQL Container

```bash
docker-compose up postgres -d
```

Check if it's running:
```bash
docker-compose ps
docker-compose logs postgres
```

### 2. Initialize Database

The database tables are automatically created when the application starts via the `init_db()` function in `app/database.py`.

To manually initialize:
```bash
# Start Python environment
.\.venv\Scripts\activate

# Run app which triggers init_db()
python -m uvicorn app.main:app --reload
```

### 3. Verify Database Connection

```bash
docker exec -it healthlang-postgres psql -U healthlang -d healthlang
```

Inside psql:
```sql
-- List all tables
\dt

-- Check users table
SELECT * FROM users;

-- Check queries table
SELECT * FROM queries LIMIT 5;

-- Exit
\q
```

## API Endpoints

### Authentication Endpoints

#### Register New User
```bash
POST http://localhost:8000/api/v1/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepassword123",
  "full_name": "Test User",
  "preferred_language": "en"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "1",
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "preferred_language": "en",
    "is_active": true,
    "is_verified": false
  }
}
```

#### Login
```bash
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=testuser&password=securepassword123
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "1",
    "username": "testuser",
    ...
  }
}
```

#### Get Current User
```bash
GET http://localhost:8000/api/v1/auth/me
Authorization: Bearer eyJhbGc...
```

### Query Endpoints

#### Submit Medical Query (Authenticated)
```bash
POST http://localhost:8000/api/v1/query
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "text": "What are the symptoms of diabetes?",
  "use_cache": true,
  "include_sources": true
}
```

#### Submit Medical Query (Anonymous)
```bash
POST http://localhost:8000/api/v1/query
Content-Type: application/json

{
  "text": "What are the symptoms of diabetes?",
  "use_cache": true,
  "include_sources": true
}
```

**Note**: Anonymous queries work but are not saved to query history.

## Database Models

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    preferred_language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    queries = relationship("Query", back_populates="user")
    translations = relationship("Translation", back_populates="user")
```

### Query Model
```python
class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    processing_time = Column(Float)
    success = Column(Boolean, default=True)
    sources = Column(Text)  # Comma-separated URLs
    metadata = Column(JSON)
    error = Column(Text)
    original_language = Column(String(10), default="en")
    target_language = Column(String(10), default="en")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="queries")
```

## Query History Logging

Every query (successful or failed) is automatically logged to the database with:

- **User ID**: Links to authenticated user (or NULL for anonymous)
- **Query Text**: Original user question
- **Response Text**: AI-generated answer
- **Processing Time**: Time taken in seconds
- **Success**: Boolean flag
- **Sources**: List of URLs/references used
- **Metadata**: RAG sources, MCP tools used, etc.
- **Error**: Error message if query failed
- **Languages**: Source and target language codes
- **Timestamp**: When query was made

## ChromaDB Persistence

### Configuration
- **Path**: `./data/chroma/`
- **Client**: `PersistentClient` (changed from `EphemeralClient`)
- **Collections**: 
  - `medical_docs` - Medical knowledge base
  - `tavily_cache` - Cached Tavily search results

### Benefits
- Vector embeddings persist across application restarts
- Cached search results speed up repeated queries
- RAG context accumulates over time

## Authentication Flow

1. **Registration**
   - User submits username, email, password
   - Password is hashed with bcrypt
   - User record created in database
   - JWT access token generated
   - Token and user info returned

2. **Login**
   - User submits username/password
   - Password verified against hashed version
   - JWT access token generated
   - Token and user info returned

3. **Protected Routes**
   - Client includes `Authorization: Bearer <token>` header
   - Server validates JWT signature and expiration
   - User object retrieved from database
   - Request proceeds with user context

4. **Optional Authentication**
   - Query endpoint accepts both authenticated and anonymous requests
   - If token provided: user identified, query history saved
   - If no token: anonymous query, no history saved

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://healthlang:healthlang_password@localhost:5432/healthlang
POSTGRES_DB=healthlang
POSTGRES_USER=healthlang
POSTGRES_PASSWORD=healthlang_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# ChromaDB Persistence
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_DB_PATH=./data/chroma
```

## Testing Workflow

### 1. Start Services
```bash
# Start PostgreSQL
docker-compose up postgres -d

# Start application
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

### 2. Test User Registration
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'
```

Save the `access_token` from the response.

### 3. Test Authenticated Query
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token-here>" \
  -d '{
    "text": "What are the symptoms of diabetes?"
  }'
```

### 4. Verify Query History
```bash
docker exec -it healthlang-postgres psql -U healthlang -d healthlang -c \
  "SELECT id, query_text, success, timestamp FROM queries ORDER BY timestamp DESC LIMIT 5;"
```

### 5. Test Anonymous Query
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is hypertension?"
  }'
```

This should work but not appear in query history.

### 6. Test ChromaDB Persistence
```bash
# Stop application
# Check that ./data/chroma directory exists with data

# Restart application
python -m uvicorn app.main:app --reload

# Submit same query - should be faster due to cached embeddings
```

## Database Migrations

Currently using SQLAlchemy's `create_all()` for simplicity. For production, consider using Alembic:

```bash
# Install Alembic
pip install alembic

# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## Security Considerations

1. **Password Security**
   - Bcrypt hashing with automatic salt generation
   - Never store plaintext passwords
   - Strong password policy recommended

2. **JWT Tokens**
   - 30-minute expiration (configurable)
   - HS256 algorithm
   - Secret key must be changed in production
   - Consider refresh tokens for longer sessions

3. **Database Access**
   - PostgreSQL user has limited permissions
   - Connection string includes credentials (secure in production)
   - Use environment variables for sensitive data

4. **SQL Injection Prevention**
   - SQLAlchemy ORM prevents SQL injection
   - Never concatenate user input into queries
   - Use parameterized queries

## Troubleshooting

### PostgreSQL Connection Errors
```bash
# Check if postgres is running
docker-compose ps

# Check logs
docker-compose logs postgres

# Restart postgres
docker-compose restart postgres
```

### Database Tables Not Created
```bash
# Check if init_db() is called in main.py lifespan
# Manually trigger:
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Authentication Errors
```bash
# Check JWT secret key is set
echo $JWT_SECRET_KEY

# Check token expiration
# Default: 30 minutes (JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
```

### ChromaDB Not Persisting
```bash
# Check directory exists
ls ./data/chroma

# Check permissions
# Ensure application can write to directory

# Check vector_store.py uses PersistentClient
grep -n "PersistentClient" app/services/rag/vector_store.py
```

## Next Steps

1. **Implement Refresh Tokens**
   - Add refresh token to login response
   - Create refresh endpoint
   - Extend session duration

2. **Add User Profile Management**
   - Update user info endpoint
   - Change password endpoint
   - Email verification

3. **Implement Query History Retrieval**
   - GET /api/v1/queries - List user's query history
   - GET /api/v1/queries/{id} - Get specific query
   - DELETE /api/v1/queries/{id} - Delete query

4. **Add Conversation Memory**
   - Store conversation threads
   - Link queries in conversations
   - Retrieve conversation context

5. **Production Deployment**
   - Use managed PostgreSQL (AWS RDS, Azure Database)
   - Configure SSL for database connections
   - Set up database backups
   - Implement rate limiting per user
   - Add API key authentication for service-to-service

## Summary

The PostgreSQL implementation provides:
- ✅ User accounts with JWT authentication
- ✅ Query history logging for authenticated users
- ✅ Persistent ChromaDB storage for RAG embeddings
- ✅ Anonymous query support (no history)
- ✅ Secure password hashing
- ✅ Automatic database initialization
- ✅ Docker-based deployment

All components are now ready for testing!
