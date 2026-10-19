import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# reading the env variables
load_dotenv()

# Read the PostgreSQL connection URL from the environment.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("PSQL_DB_USER"),
    password=os.getenv("PSQL_DB_PASSWORD"),
    host=os.getenv("PSQL_DB_HOST"),
    port=os.getenv("PSQL_DB_PORT"),
    database=os.getenv("PSQL_DB_NAME"),
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Please configure your PostgreSQL connection URL.")


# Create the engine: SQLAlchemy's interface to the database.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# Create a factory that produces database sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class inherited by all SQLAlchemy database models."""


def get_db():
    """Provide a database session to a FastAPI request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
