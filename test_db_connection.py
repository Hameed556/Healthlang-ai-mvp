"""Test database connection to production PostgreSQL"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Load .env
load_dotenv()

def test_connection():
    """Test connection to database"""
    
    # Get database URL
    environment = os.getenv("ENVIRONMENT", "development")
    database_url = os.getenv("DATABASE_URL")
    
    print(f"Environment: {environment}")
    print(f"Testing connection to: {database_url[:50]}...")
    
    try:
        # Create engine with SSL configuration
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=5,
            pool_timeout=30,
            echo=False,
            connect_args={
                "sslmode": "require",
                "connect_timeout": 10
            }
        )
        
        # Test connection
        print("\n🔄 Attempting to connect...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"📊 PostgreSQL version: {version[:50]}...")
            
            # Test creating a simple table
            print("\n🔄 Testing table creation...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_connection (
                    id SERIAL PRIMARY KEY,
                    test_value VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ Table creation successful!")
            
            # Insert test data
            print("\n🔄 Testing data insertion...")
            conn.execute(text("""
                INSERT INTO test_connection (test_value) 
                VALUES ('Connection test successful')
            """))
            conn.commit()
            print("✅ Data insertion successful!")
            
            # Query test data
            print("\n🔄 Testing data retrieval...")
            result = conn.execute(text("SELECT * FROM test_connection ORDER BY id DESC LIMIT 1"))
            row = result.fetchone()
            print(f"✅ Data retrieval successful: {row[1]}")
            
            # Clean up
            print("\n🔄 Cleaning up test table...")
            conn.execute(text("DROP TABLE IF EXISTS test_connection"))
            conn.commit()
            print("✅ Cleanup successful!")
            
        print("\n🎉 All database tests passed!")
        return True
        
    except OperationalError as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nPossible issues:")
        print("1. Check if DATABASE_URL is correct")
        print("2. Verify Render PostgreSQL is running")
        print("3. Check if your IP is whitelisted (if required)")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
