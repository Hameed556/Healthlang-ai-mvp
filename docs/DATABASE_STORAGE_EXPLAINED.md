# PostgreSQL Data Storage Explained

## Where is the Data Actually Stored?

### ❌ **NOT Stored As:**
- CSV files
- Excel files
- JSON files
- Text files
- Any readable file format you can directly open

### ✅ **Actually Stored As:**
PostgreSQL stores data in **binary database files** inside a **Docker volume**.

## Data Storage Location

### 1. Docker Volume (Binary Storage)
```
Docker Volume: postgres_data
Physical Location: /var/lib/docker/volumes/healthlang-ai-mvp_postgres_data/_data/
Storage Format: Binary PostgreSQL database files (.dat, .wal, .conf files)
```

**You CANNOT directly read these files** - they are in PostgreSQL's internal binary format.

## How Your Chat Data is Stored

### Database Structure (Relational Tables)

```
┌─────────────────────────────────────────────────┐
│                  USERS TABLE                     │
├──────┬────────────┬───────────────┬──────────────┤
│  id  │  username  │     email     │   password   │
├──────┼────────────┼───────────────┼──────────────┤
│  1   │  john_doe  │ john@mail.com │  [hashed]    │
│  2   │  jane_sm   │ jane@mail.com │  [hashed]    │
└──────┴────────────┴───────────────┴──────────────┘
           ↓ (user_id foreign key relationship)
┌─────────────────────────────────────────────────────────────────────┐
│                         QUERIES TABLE                               │
├────┬─────────┬─────────────────────┬────────────────────┬──────────┤
│ id │ user_id │    query_text       │   response_text    │timestamp │
├────┼─────────┼─────────────────────┼────────────────────┼──────────┤
│ 1  │    1    │ "What is diabetes?" │ "Diabetes is..."   │ 2025-... │
│ 2  │    1    │ "Symptoms of flu?"  │ "Flu symptoms..."  │ 2025-... │
│ 3  │    2    │ "Blood pressure?"   │ "Blood pressure..." │ 2025-... │
│ 4  │   NULL  │ "Anonymous query"   │ "Response..."      │ 2025-... │
└────┴─────────┴─────────────────────┴────────────────────┴──────────┘
```

### Real Database Schema

#### **USERS Table**
| Column | Type | Description |
|--------|------|-------------|
| `id` | String(36) UUID | Unique user identifier |
| `username` | String(50) | User's username (unique) |
| `email` | String(255) | User's email (unique) |
| `hashed_password` | String(255) | Bcrypt hashed password |
| `full_name` | String(100) | User's full name |
| `preferred_language` | String(10) | Language preference (default: "en") |
| `is_active` | Boolean | Account active status |
| `is_verified` | Boolean | Email verified status |
| `created_at` | DateTime | Account creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `last_login` | DateTime | Last login timestamp |

#### **QUERIES Table** (Your Chat History)
| Column | Type | Description |
|--------|------|-------------|
| `id` | String(36) UUID | Unique query identifier |
| `user_id` | String(36) | Foreign key to users table (NULL for anonymous) |
| `query_text` | Text | The user's question/prompt |
| `response_text` | Text | **NOT IN CURRENT SCHEMA - Need to add** |
| `query_type` | String(50) | Type of medical query |
| `language` | String(10) | Query language |
| `analysis` | Text | AI's analysis |
| `recommendations` | JSON | Medical recommendations |
| `safety_level` | String(20) | Safety assessment |
| `confidence_score` | Float | AI confidence level |
| `sources` | JSON | Sources used (URLs, documents) |
| `processing_time` | Float | Time taken to process |
| `request_metadata` | JSON | Additional metadata (RAG sources, MCP tools, etc.) |
| `created_at` | DateTime | When query was made |

## How to Access Your Data

### Method 1: SQL Queries (Inside Docker Container)

```bash
# Connect to PostgreSQL inside Docker
docker exec -it healthlang-postgres psql -U healthlang -d healthlang

# View all users
SELECT id, username, email, created_at FROM users;

# View all queries for a specific user
SELECT 
    id, 
    query_text, 
    analysis, 
    confidence_score, 
    created_at 
FROM queries 
WHERE user_id = 'user-uuid-here' 
ORDER BY created_at DESC 
LIMIT 10;

# View queries with user information (JOIN)
SELECT 
    u.username,
    u.email,
    q.query_text,
    q.analysis,
    q.created_at
FROM queries q
JOIN users u ON q.user_id = u.id
ORDER BY q.created_at DESC;

# Count queries per user
SELECT 
    u.username,
    COUNT(q.id) as total_queries
FROM users u
LEFT JOIN queries q ON u.id = q.user_id
GROUP BY u.id, u.username;

# Exit psql
\q
```

### Method 2: Python Script (Query from Application)

```python
from app.database import get_db_context
from app.models.database_models import User, Query
from sqlalchemy import desc

async def get_user_chat_history(username: str):
    """Get all chats for a specific user"""
    async with get_db_context() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return []
        
        queries = (
            db.query(Query)
            .filter(Query.user_id == user.id)
            .order_by(desc(Query.created_at))
            .all()
        )
        
        return [
            {
                "query": q.query_text,
                "response": q.analysis,
                "timestamp": q.created_at,
                "sources": q.sources
            }
            for q in queries
        ]
```

### Method 3: Export to CSV (If Needed)

```python
import csv
from app.database import get_db_context
from app.models.database_models import Query

async def export_queries_to_csv(filename: str):
    """Export all queries to CSV file"""
    async with get_db_context() as db:
        queries = db.query(Query).all()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                'ID', 'User ID', 'Query', 'Response', 
                'Confidence', 'Timestamp'
            ])
            
            # Data
            for q in queries:
                writer.writerow([
                    q.id,
                    q.user_id,
                    q.query_text,
                    q.analysis,
                    q.confidence_score,
                    q.created_at
                ])
    
    print(f"Exported to {filename}")

# Usage
import asyncio
asyncio.run(export_queries_to_csv("query_history.csv"))
```

### Method 4: API Endpoint (Recommended - TO BE IMPLEMENTED)

We should create this endpoint:

```python
# app/api/routes/query.py

@router.get("/queries/history")
async def get_query_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get query history for authenticated user.
    
    Returns list of previous queries with responses.
    """
    queries = (
        db.query(Query)
        .filter(Query.user_id == current_user.id)
        .order_by(desc(Query.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return {
        "total": len(queries),
        "queries": [
            {
                "id": q.id,
                "query": q.query_text,
                "response": q.analysis,
                "confidence": q.confidence_score,
                "sources": q.sources,
                "timestamp": q.created_at.isoformat()
            }
            for q in queries
        ]
    }
```

## Visual: Data Flow

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ POST /api/v1/query
       │ {"text": "What is diabetes?"}
       ↓
┌──────────────────────┐
│   FastAPI Backend    │
│   (Your App)         │
├──────────────────────┤
│ 1. Process query     │
│ 2. Get AI response   │
│ 3. Save to database  │
└──────┬───────────────┘
       │ SQL INSERT INTO queries...
       ↓
┌─────────────────────────────────┐
│   PostgreSQL Container          │
│                                 │
│   ┌──────────────────────┐     │
│   │  QUERIES TABLE       │     │
│   ├──────────────────────┤     │
│   │ id: "uuid-123"       │     │
│   │ user_id: "user-456"  │     │
│   │ query_text: "What is │     │
│   │             diabetes?"│    │
│   │ analysis: "Diabetes  │     │
│   │           is..."      │    │
│   │ created_at: 2025-... │     │
│   └──────────────────────┘     │
│                                 │
└───────────┬─────────────────────┘
            │ Data persisted in Docker volume
            ↓
┌────────────────────────────────┐
│  Docker Volume                 │
│  postgres_data                 │
│                                │
│  /var/lib/postgresql/data/     │
│  ├── base/                     │
│  ├── global/                   │
│  ├── pg_wal/                   │
│  └── [binary database files]   │
└────────────────────────────────┘
```

## Important Notes

### ⚠️ Schema Mismatch Found!

The current `Query` model in `database_models.py` **DOES NOT** have a `response_text` column!

It has:
- `query_text` ✅
- `analysis` ✅ (this is the response)
- But NOT `response_text` ❌

The `query_service.py` tries to save to `response_text` which doesn't exist!

**We need to either:**
1. Use `analysis` field instead of `response_text`, OR
2. Add `response_text` column to the Query model

### Current Working Fields:
- `query_text` - User's question
- `analysis` - AI's response (already exists!)
- `recommendations` - Structured recommendations
- `sources` - Source URLs/documents
- `confidence_score` - AI confidence
- `processing_time` - Time taken
- `request_metadata` - Additional data

## How to View Your Data Right Now

### Quick Check:
```bash
# 1. Start PostgreSQL
docker compose up postgres -d

# 2. Connect to database
docker exec -it healthlang-postgres psql -U healthlang -d healthlang

# 3. List tables
\dt

# 4. View table structure
\d users
\d queries

# 5. View data
SELECT * FROM users;
SELECT * FROM queries ORDER BY created_at DESC LIMIT 5;
```

## Summary

1. **Storage Format**: Binary PostgreSQL database files (NOT CSV/Excel)
2. **Location**: Docker volume `postgres_data` 
3. **Structure**: Relational tables (users, queries, translations)
4. **Access Methods**:
   - SQL queries inside Docker container
   - Python scripts using SQLAlchemy
   - Export to CSV if needed
   - API endpoints (to be implemented)
5. **Relationship**: Each query linked to user via `user_id` foreign key
6. **Anonymous Queries**: `user_id = NULL` for non-authenticated requests

Your chat history is stored in a **proper relational database** with full ACID compliance, transactions, and data integrity - much better than CSV files! 🎉
