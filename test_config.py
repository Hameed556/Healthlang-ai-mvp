"""Quick test script for environment configuration"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get environment
environment = os.getenv("ENVIRONMENT", "development")
print(f"Environment: {environment}")

# Show database configuration based on environment
if environment == "production":
    db_url = os.getenv("DATABASE_URL")
    print(f"Database URL: {db_url}")
else:
    # Development - construct from individual variables
    user = os.getenv("POSTGRES_USER", "healthlang")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "healthlang")
    
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    print(f"Database URL: {db_url}")

print("\n✅ Configuration loaded successfully!")
