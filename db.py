from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# The connection string format is:
# postgresql://username:password@host:port/database_name

# Replace 'YOUR_PASSWORD' with the password you made during installation!
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/library_exam_db"

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to use in your API routes (FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
