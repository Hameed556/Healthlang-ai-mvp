# Quick Answer: How PostgreSQL is Used in Your Project

## Your Questions Answered:

### 1. "How is PostgreSQL used now?"

PostgreSQL is used as the **primary database** for storing:
- **User accounts** (username, email, password, preferences)
- **Chat history / Query history** (every question and response)
- **Translation history** (if translation features are used)

### 2. "Where is the data saved?"

**Location**: Inside a **Docker volume** named `postgres_data`

```yaml
# From docker-compose.yml
volumes:
  postgres_data:      # <-- Your data is here
    driver: local

services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data  # <-- Mounted here
```

**Physical Path** (on your machine):
- Windows: `C:\ProgramData\docker\volumes\healthlang-ai-mvp_postgres_data\_data\`
- Linux/Mac: `/var/lib/docker/volumes/healthlang-ai-mvp_postgres_data/_data/`

### 3. "Is there a file where chats are stored in relational tabular format?"

**NO CSV or visible files!** But YES, data is in **relational tabular format** inside PostgreSQL.

## The Data Structure

### Users Table
```
┌────────┬──────────┬─────────────────┬─────────────────┬────────────┐
│   id   │ username │      email      │ hashed_password │ created_at │
├────────┼──────────┼─────────────────┼─────────────────┼────────────┤
│ uuid-1 │ john_doe │ john@email.com  │  [bcrypt hash]  │ 2025-10-28 │
│ uuid-2 │ jane_sm  │ jane@email.com  │  [bcrypt hash]  │ 2025-10-28 │
└────────┴──────────┴─────────────────┴─────────────────┴────────────┘
```

### Queries Table (Your Chats - Linked by user_id)
```
┌────────┬─────────┬──────────────────────┬────────────────────┬──────────┬────────────┐
│   id   │ user_id │     query_text       │   response_text    │ sources  │ timestamp  │
├────────┼─────────┼──────────────────────┼────────────────────┼──────────┼────────────┤
│ q-001  │ uuid-1  │ "What is diabetes?"  │ "Diabetes is a..." │ [PubMed] │ 2025-10-28 │
│ q-002  │ uuid-1  │ "Flu symptoms?"      │ "Flu causes..."    │ [WHO]    │ 2025-10-28 │
│ q-003  │ uuid-2  │ "Blood pressure"     │ "BP refers to..."  │ [CDC]    │ 2025-10-28 │
│ q-004  │  NULL   │ "Anonymous query"    │ "Response..."      │ [Mayo]   │ 2025-10-28 │
└────────┴─────────┴──────────────────────┴────────────────────┴──────────┴────────────┘
                ↑
                └── Foreign key linking to users.id
```

## How to View Your Chat Data

### Option 1: SQL Query (Direct Database Access)

```bash
# 1. Connect to PostgreSQL in Docker
docker exec -it healthlang-postgres psql -U healthlang -d healthlang

# 2. See all chats with usernames
SELECT 
    u.username,
    q.query_text as question,
    q.response_text as answer,
    q.timestamp
FROM queries q
LEFT JOIN users u ON q.user_id = u.id
ORDER BY q.timestamp DESC
LIMIT 10;

# 3. See chats for specific user
SELECT query_text, response_text, timestamp 
FROM queries 
WHERE user_id = (SELECT id FROM users WHERE username = 'john_doe')
ORDER BY timestamp DESC;

# 4. Count chats per user
SELECT 
    u.username,
    COUNT(q.id) as total_chats
FROM users u
LEFT JOIN queries q ON u.id = q.user_id
GROUP BY u.username;
```

### Option 2: Export to CSV (If You Want a File)

Create this script `export_chats.py`:

```python
import csv
import asyncio
from app.database import get_db_context
from app.models.database_models import Query, User
from sqlalchemy.orm import joinedload

async def export_to_csv():
    async with get_db_context() as db:
        # Get all queries with user info
        queries = db.query(Query).options(
            joinedload(Query.user)
        ).all()
        
        # Write to CSV
        with open('chat_history.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Username', 'User Email', 'Question', 'Answer', 
                'Sources', 'Confidence', 'Timestamp'
            ])
            
            for q in queries:
                writer.writerow([
                    q.user.username if q.user else 'Anonymous',
                    q.user.email if q.user else 'N/A',
                    q.query_text,
                    q.response_text or q.analysis,
                    q.sources,
                    q.confidence_score,
                    q.timestamp
                ])
        
        print(f"✅ Exported {len(queries)} chats to chat_history.csv")

# Run it
asyncio.run(export_to_csv())
```

Then run:
```bash
python export_chats.py
```

This creates a `chat_history.csv` file you can open in Excel!

### Option 3: API Endpoint (Need to Add This)

We should add this to `app/api/routes/query.py`:

```python
@router.get("/queries/history")
async def get_my_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get authenticated user's chat history"""
    queries = (
        db.query(Query)
        .filter(Query.user_id == current_user.id)
        .order_by(desc(Query.timestamp))
        .limit(limit)
        .all()
    )
    
    return {
        "username": current_user.username,
        "total_chats": len(queries),
        "chats": [
            {
                "question": q.query_text,
                "answer": q.response_text or q.analysis,
                "timestamp": q.timestamp.isoformat(),
                "sources": q.sources
            }
            for q in queries
        ]
    }
```

Then access via:
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/queries/history
```

## Key Points

1. **Storage Format**: 
   - ❌ NOT CSV files
   - ✅ Binary PostgreSQL database (relational tables)

2. **Data Persistence**: 
   - Stored in Docker volume `postgres_data`
   - Survives container restarts
   - Backed up with volume backups

3. **Relational Structure**:
   - `users` table ←→ `queries` table (linked by `user_id`)
   - Each user can have many queries
   - Each query belongs to one user (or NULL for anonymous)

4. **Access Methods**:
   - SQL queries (direct)
   - Python scripts (programmatic)
   - Export to CSV (if you need files)
   - API endpoints (to be implemented)

5. **Per-User Chat History**:
   - ✅ YES! Each query has a `user_id` field
   - ✅ You can get all chats for any user
   - ✅ Anonymous chats have `user_id = NULL`

## Example: Real Chat Flow

```
1. User "john_doe" logs in
   → Receives JWT token

2. User asks: "What is diabetes?"
   → POST /api/v1/query
   → System identifies user from JWT token
   → Saves to database:
      {
        id: "q-12345",
        user_id: "john-uuid",
        query_text: "What is diabetes?",
        response_text: "Diabetes is...",
        timestamp: "2025-10-28T10:30:00Z"
      }

3. Later, john_doe asks: "What are the symptoms?"
   → Another row saved with same user_id
   
4. View john_doe's history:
   → Query database: WHERE user_id = 'john-uuid'
   → Returns all john_doe's questions and answers in order
```

## Want a Visual Dashboard?

You could create a simple web page showing chat history:

```python
# app/templates/chat_history.html
<html>
  <h1>My Chat History</h1>
  {% for chat in chats %}
    <div class="chat">
      <strong>You:</strong> {{ chat.question }}
      <br>
      <strong>AI:</strong> {{ chat.answer }}
      <br>
      <small>{{ chat.timestamp }}</small>
    </div>
  {% endfor %}
</html>
```

## Summary

- ✅ PostgreSQL IS being used
- ✅ Data IS stored in relational tables
- ✅ Each user's chats ARE linked by user_id
- ✅ Data persists in Docker volume
- ❌ Not stored as CSV (but can be exported if needed)
- ✅ Proper database with ACID guarantees

Your chat data is stored **professionally** in a real database, not as simple files! 🎉
