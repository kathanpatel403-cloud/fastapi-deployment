import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Load environment variables from .env file
load_dotenv()

# Extract database connection variables
DB_USER = os.getenv("DB_USER") or os.getenv("POSTGRES_USER") or "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or "postgres"
DB_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST") or "localhost"
DB_PORT = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT") or "5432"
DB_NAME = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB") or "appdb"

# Construct Database URLs (Async for FastAPI, Sync for Alembic if needed)
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_SYNC_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create the async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


# Async dependency for database session
async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()