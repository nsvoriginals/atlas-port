# THIS FILE DEFINES THE USER AND RESUME DATABASE MODELS
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.db import Base

# USER TABLE MODEL
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    
    # RELATIONSHIP TO RESUME TABLE
    resumes = relationship("Resume", back_populates="user")

# RESUME TABLE MODEL
class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    template_name = Column(String, default="default")
    resume_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # RELATIONSHIP TO USER TABLE
    user = relationship("User", back_populates="resumes")