from sqlalchemy import Column, Integer , String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from pgvector.sqlalchemy import Vector
class Document(Base):
    __tablename__="documents"
    id=Column(Integer, primary_key=True)
    filename=Column(String(100),nullable=False)
    uploaded_at=Column(DateTime,default=lambda: datetime.now(timezone.utc))
    status=Column(String,default="pending")
    user_id=Column(Integer, ForeignKey("users.id"))
    chunks = relationship("Chunk", back_populates="documents", cascade="all, delete-orphan")
    owner=relationship("User", back_populates="documents")
    
class Chunk(Base):
    __tablename__="chunks"
    id=Column(Integer, primary_key=True)
    content=Column(Text, nullable=False)
    document_id=Column(Integer,ForeignKey("documents.id"))
    documents=relationship("Document",back_populates="chunks")
    embedding = Column(Vector(384))

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    email=Column(Text,nullable=False,unique=True)
    firstname=Column(String(50))
    surname=Column(String(50))
    username=Column(String(30),unique=True)
    documents=relationship("Document",back_populates="owner")