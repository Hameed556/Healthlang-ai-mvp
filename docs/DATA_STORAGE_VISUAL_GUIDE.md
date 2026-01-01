# Data Storage Architecture - Visual Guide

## What Data is Stored & How It Syncs

```
┌──────────────────────────────────────────────────────────────────────┐
│                    YOUR HEALTHLANG AI APPLICATION                     │
└──────────────────────────────────────────────────────────────────────┘

                              USER INTERACTIONS
                                     │
                    ┌────────────────┼────────────────┐
                    ↓                ↓                ↓
            
    ┌───────────────────┐  ┌─────────────────┐  ┌──────────────────┐
    │  Register/Login   │  │  Medical Query  │  │  View History    │
    │                   │  │                 │  │                  │
    │  - Username       │  │  - Question     │  │  - Past queries  │
    │  - Email          │  │  - Get Answer   │  │  - Timestamps    │
    │  - Password       │  │  - View Sources │  │  - Responses     │
    └─────────┬─────────┘  └────────┬────────┘  └────────┬─────────┘
              │                     │                     │
              │                     │                     │
              ↓                     ↓                     ↓
              
    ┌─────────────────────────────────────────────────────────────┐
    │              FASTAPI APPLICATION (Python)                    │
    │                                                              │
    │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
    │  │ Auth Service │   │Query Service │   │History Service│   │
    │  │              │   │              │   │              │   │
    │  │ create_user()│   │create_query()│   │get_history() │   │
    │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
    │         │                  │                  │            │
    │         └──────────────────┼──────────────────┘            │
    │                            │                               │
    │                    ┌───────▼────────┐                      │
    │                    │  SQLAlchemy    │                      │
    │                    │  ORM Layer     │                      │
    │                    │  (Auto SQL)    │                      │
    │                    └───────┬────────┘                      │
    └────────────────────────────┼─────────────────────────────┘
                                 │
                                 │ SQL Commands (automatic)
                                 │
                ┌────────────────▼────────────────┐
                │   PostgreSQL Database           │
                │   (Docker Container)            │
                │                                 │
                │  ┌──────────────────────────┐  │
                │  │     USERS TABLE          │  │
                │  ├──────┬───────────────────┤  │
                │  │ id   │ username │ email  │  │
                │  │ 001  │ john_doe │ j@...  │  │
                │  │ 002  │ jane_sm  │ jane@..│  │
                │  └──────┴───────────────────┘  │
                │              ↕ (relationship)   │
                │  ┌──────────────────────────────────────┐
                │  │     QUERIES TABLE (Chat History)     │
                │  ├────┬─────────┬──────────────┬────────┤
                │  │ id │ user_id │ query_text   │response│
                │  │ q1 │  001    │ "diabetes?"  │ "Dia..."│
                │  │ q2 │  001    │ "flu sympt?" │ "Flu..."│
                │  │ q3 │  002    │ "BP high?"   │ "BP..." │
                │  └────┴─────────┴──────────────┴────────┘
                │                                 │
                │  ┌──────────────────────────┐  │
                │  │  TRANSLATIONS TABLE      │  │
                │  ├────┬─────────┬───────────┤  │
                │  │ id │ user_id │ source→   │  │
                │  │ t1 │  001    │ en→es     │  │
                │  └────┴─────────┴───────────┘  │
                │                                 │
                │  📦 Stored in Docker Volume:   │
                │     postgres_data              │
                └─────────────────────────────────┘
```

---

## Data Flow: User Asks a Question

```
STEP 1: USER INPUT
┌─────────────────────────────────────┐
│  User (john_doe) asks:              │
│  "What are the symptoms of          │
│   diabetes?"                        │
└─────────────────┬───────────────────┘
                  │
                  ↓ POST /api/v1/query
                  │ (with JWT token)
                  │
STEP 2: AUTHENTICATION
┌─────────────────┴───────────────────┐
│  Python: Verify JWT token           │
│  ↓                                   │
│  SELECT FROM users                  │
│  WHERE username = 'john_doe'        │
│  ↓                                   │
│  User found! user_id = 001          │
└─────────────────┬───────────────────┘
                  │
                  ↓
STEP 3: PROCESS QUERY
┌─────────────────┴───────────────────┐
│  Python: workflow.process_query()   │
│  ↓                                   │
│  1. Call MCP for medical data       │
│  2. Call Tavily for general info    │
│  3. Call Groq LLM for response      │
│  4. Format response                 │
│  ↓                                   │
│  Response: "Diabetes symptoms       │
│  include increased thirst..."       │
└─────────────────┬───────────────────┘
                  │
                  ↓
STEP 4: SAVE TO DATABASE (AUTOMATIC!)
┌─────────────────┴───────────────────┐
│  Python: QueryService               │
│    .create_query_record()           │
│  ↓                                   │
│  SQLAlchemy generates:              │
│  ↓                                   │
│  INSERT INTO queries (              │
│    id,                              │
│    user_id,                         │
│    query_text,                      │
│    response_text,                   │
│    processing_time,                 │
│    success,                         │
│    sources,                         │
│    metadata,                        │
│    timestamp                        │
│  ) VALUES (                         │
│    'q-uuid-123',                    │
│    '001',           ← Linked to user│
│    'What are...',                   │
│    'Diabetes...',                   │
│    2.5,                             │
│    true,                            │
│    '["PubMed", "WHO"]',            │
│    '{"rag_used": true}',           │
│    '2025-10-29 10:30:00'           │
│  );                                 │
│  ↓                                   │
│  ✅ SAVED TO POSTGRES!               │
└─────────────────┬───────────────────┘
                  │
                  ↓
STEP 5: RETURN TO USER
┌─────────────────┴───────────────────┐
│  Response sent to browser:          │
│  {                                   │
│    "request_id": "q-uuid-123",      │
│    "response": "Diabetes symptoms   │
│     include increased thirst...",   │
│    "sources": ["PubMed", "WHO"],    │
│    "timestamp": "2025-10-29..."     │
│  }                                   │
└─────────────────────────────────────┘

✅ EVERYTHING SAVED AUTOMATICALLY!
✅ NO MANUAL WORK REQUIRED!
```

---

## What Data Gets Stored - Complete Breakdown

### 📝 USERS Table

```
┌─────────────────────────────────────────────────────────────┐
│                        USER DATA                            │
└─────────────────────────────────────────────────────────────┘

What's Stored:
├── Account Information
│   ├── ID (UUID): Unique identifier
│   ├── Username: Login name
│   ├── Email: Contact email
│   └── Hashed Password: Secure (bcrypt)
│
├── Profile Data
│   ├── Full Name: Display name
│   └── Preferred Language: en, es, fr, etc.
│
├── Status Flags
│   ├── Is Active: Can user login?
│   └── Is Verified: Email confirmed?
│
└── Timestamps
    ├── Created At: When account made
    ├── Updated At: Last profile change
    └── Last Login: Last sign-in time

Example Row:
┌──────────────────────────────────────────────────────────┐
│ id:         uuid-12345                                   │
│ username:   john_doe                                     │
│ email:      john@example.com                             │
│ password:   $2b$12$hashed_password_here                  │
│ full_name:  John Doe                                     │
│ language:   en                                           │
│ is_active:  true                                         │
│ verified:   false                                        │
│ created:    2025-10-28 10:30:00                          │
│ updated:    2025-10-29 09:15:00                          │
│ last_login: 2025-10-29 09:15:00                          │
└──────────────────────────────────────────────────────────┘
```

### 💬 QUERIES Table (Chat History)

```
┌─────────────────────────────────────────────────────────────┐
│                   CHAT HISTORY DATA                         │
└─────────────────────────────────────────────────────────────┘

What's Stored:
├── Query Information
│   ├── ID (UUID): Unique query ID
│   ├── User ID: Links to user
│   ├── Query Text: User's question
│   └── Response Text: AI's answer
│
├── Medical Analysis
│   ├── Analysis: Detailed breakdown
│   ├── Recommendations: Medical advice
│   ├── Safety Level: safe/caution/emergency
│   └── Confidence Score: 0.0 to 1.0
│
├── Source Attribution
│   ├── Sources: List of URLs/docs
│   └── Metadata: RAG sources, MCP tools
│
├── Performance Metrics
│   ├── Processing Time: Seconds
│   └── Success: true/false
│
└── Timestamps
    ├── Timestamp: When query made
    └── Created At: Same as timestamp

Example Row:
┌──────────────────────────────────────────────────────────┐
│ id:          query-uuid-67890                            │
│ user_id:     uuid-12345  (john_doe)                      │
│ query_text:  "What are the symptoms of diabetes?"       │
│ response:    "Diabetes symptoms include increased       │
│              thirst, frequent urination..."              │
│ analysis:    "Type 2 diabetes presents with..."         │
│ confidence:  0.92                                        │
│ safety:      "safe"                                      │
│ sources:     ["PubMed", "WHO", "Mayo Clinic"]          │
│ metadata:    {                                           │
│               "mcp_tools": ["pubmed_search"],           │
│               "rag_used": true,                         │
│               "tavily_used": false                      │
│              }                                           │
│ time:        2.45 seconds                                │
│ success:     true                                        │
│ timestamp:   2025-10-29 10:40:00                         │
└──────────────────────────────────────────────────────────┘
```

### 🌐 TRANSLATIONS Table

```
┌─────────────────────────────────────────────────────────────┐
│                  TRANSLATION HISTORY                        │
└─────────────────────────────────────────────────────────────┘

What's Stored:
├── Translation Data
│   ├── ID (UUID): Unique translation ID
│   ├── User ID: Links to user
│   ├── Original Text: Before translation
│   └── Translated Text: After translation
│
├── Language Information
│   ├── Source Language: Original (en, es, etc.)
│   └── Target Language: Translated to
│
├── Quality Metrics
│   ├── Confidence Score: Translation confidence
│   └── Processing Time: Seconds
│
└── Timestamps
    └── Created At: When translated

Example Row:
┌──────────────────────────────────────────────────────────┐
│ id:          trans-uuid-abc123                           │
│ user_id:     uuid-12345                                  │
│ original:    "What are diabetes symptoms?"               │
│ translated:  "¿Cuáles son los síntomas de diabetes?"   │
│ from:        en                                          │
│ to:          es                                          │
│ confidence:  0.95                                        │
│ time:        0.8 seconds                                 │
│ created:     2025-10-29 11:00:00                         │
└──────────────────────────────────────────────────────────┘
```

---

## Real-World Usage Examples

### Example 1: John's Medical Journey

```
Day 1: October 28, 2025
─────────────────────────

10:30 AM - John registers
         → SAVED TO: users table
         → Data: username=john_doe, email=john@email.com

10:35 AM - John asks: "What are diabetes symptoms?"
         → SAVED TO: queries table
         → Data: user_id=john, query="What are...", 
                 response="Diabetes symptoms include..."

10:40 AM - John asks: "How is diabetes diagnosed?"
         → SAVED TO: queries table
         → Data: Another row linked to john_doe

Day 2: October 29, 2025
─────────────────────────

09:00 AM - John logs in
         → UPDATED: users table
         → Data: last_login = 2025-10-29 09:00:00

09:15 AM - John views his history
         → QUERY: SELECT FROM queries WHERE user_id=john
         → Returns: All 2 previous questions

09:20 AM - John asks: "What causes high blood pressure?"
         → SAVED TO: queries table
         → Data: New row, now john has 3 queries total

Result:
─────────────────────────
users table:
  1 row (john_doe account)

queries table:
  3 rows (all john's questions with answers)
  
All linked by user_id! ✅
```

### Example 2: Multiple Users

```
┌────────────────────────────────────────────────────────┐
│                 USERS TABLE                            │
├────────┬──────────┬─────────────────┬─────────────────┤
│   id   │ username │     email       │   created_at    │
├────────┼──────────┼─────────────────┼─────────────────┤
│  001   │ john_doe │ john@email.com  │ 2025-10-28 ...  │
│  002   │ jane_sm  │ jane@email.com  │ 2025-10-28 ...  │
│  003   │ bob_med  │ bob@email.com   │ 2025-10-29 ...  │
└────────┴──────────┴─────────────────┴─────────────────┘
                 ↕ (linked by user_id)
┌────────────────────────────────────────────────────────────┐
│               QUERIES TABLE                                │
├────┬─────────┬───────────────────────┬───────────────────┤
│ id │ user_id │      query_text       │    timestamp      │
├────┼─────────┼───────────────────────┼───────────────────┤
│ q1 │  001    │ "diabetes symptoms?"  │ 2025-10-28 10:35  │
│ q2 │  001    │ "diabetes diagnosis?" │ 2025-10-28 10:40  │
│ q3 │  002    │ "high BP causes?"     │ 2025-10-28 11:00  │
│ q4 │  001    │ "blood pressure?"     │ 2025-10-29 09:20  │
│ q5 │  003    │ "flu symptoms?"       │ 2025-10-29 10:00  │
│ q6 │  002    │ "vaccine info?"       │ 2025-10-29 10:30  │
└────┴─────────┴───────────────────────┴───────────────────┘

Summary:
- john_doe (001): 3 queries
- jane_sm (002):  2 queries
- bob_med (003):  1 query

Each user's history is separate and private! ✅
```

---

## How to View Your Data

### Method 1: SQL Commands (Direct)

```sql
-- See all users
SELECT username, email, created_at FROM users;

-- See all queries
SELECT 
    u.username,
    q.query_text,
    q.timestamp
FROM queries q
JOIN users u ON q.user_id = u.id
ORDER BY q.timestamp DESC;

-- See one user's history
SELECT 
    query_text,
    response_text,
    timestamp
FROM queries
WHERE user_id = (SELECT id FROM users WHERE username = 'john_doe')
ORDER BY timestamp DESC;

-- Count queries per user
SELECT 
    u.username,
    COUNT(q.id) as total_queries
FROM users u
LEFT JOIN queries q ON u.id = q.user_id
GROUP BY u.username;
```

### Method 2: API Endpoints (Need to Add)

```python
# app/api/routes/query.py

@router.get("/queries/history")
async def get_my_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get authenticated user's query history"""
    queries = (
        db.query(Query)
        .filter(Query.user_id == current_user.id)
        .order_by(desc(Query.timestamp))
        .all()
    )
    
    return {
        "username": current_user.username,
        "total": len(queries),
        "queries": [
            {
                "question": q.query_text,
                "answer": q.response_text,
                "timestamp": q.timestamp.isoformat(),
                "sources": q.sources
            }
            for q in queries
        ]
    }
```

Then access:
```bash
curl -H "Authorization: Bearer token" \
  http://localhost:8000/api/v1/queries/history
```

---

## Summary

✅ **What's Stored:**
- User accounts (login, profile)
- Complete chat history (questions + answers)
- Translation history (multi-language)
- Sources and metadata (attribution)
- Performance metrics (timing, success)

✅ **How It Syncs:**
- AUTOMATIC on every API call
- No manual work needed
- SQLAlchemy handles SQL generation
- Real-time database updates
- Persists across restarts

✅ **Why This is Powerful:**
- Track user behavior
- Analyze popular questions
- Improve AI responses
- Provide personalized experience
- Comply with data retention policies

🎉 **You have a complete data storage system!**
