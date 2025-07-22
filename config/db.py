# THIS FILE HANDLES DATABASE CONNECTION AND SESSION MANAGEMENT
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError
import time
from typing import Generator

# LOAD ENVIRONMENT VARIABLES
load_dotenv()

# GET DATABASE URL FROM ENVIRONMENT OR USE SQLITE BY DEFAULT
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume.db")

# CREATE DATABASE ENGINE BASED ON DATABASE TYPE
# IF USING SQLITE, ADD SPECIAL PARAMS
if SQLALCHEMY_DATABASE_URL.startswith('sqlite'):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # IF USING POSTGRESQL, ADD CONNECTION POOL SETTINGS
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # RECYCLE CONNECTIONS AFTER 30 MINUTES
        pool_pre_ping=True  # ENABLE CONNECTION HEALTH CHECKS
    )

# CREATE SESSION LOCAL FOR DATABASE OPERATIONS
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# BASE CLASS FOR MODELS
Base = declarative_base()

# FUNCTION TO RECREATE ALL TABLES (DROPS AND CREATES)
def recreate_tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

# FUNCTION TO GET DATABASE SESSION WITH RETRY LOGIC
def get_db() -> Generator:
    db = SessionLocal()
    max_retries = 3
    retry_delay = 1  # SECONDS
    
    for attempt in range(max_retries):
        try:
            yield db
            break
        except OperationalError as e:
            if attempt == max_retries - 1:  # LAST ATTEMPT
                raise e
            time.sleep(retry_delay)
            db = SessionLocal()  # CREATE NEW SESSION
        finally:
            db.close()