from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uuid
import json

Base = declarative_base()

class Operator(Base):
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    max_active_leads = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    

    source_weights = relationship("OperatorSourceWeight", back_populates="operator")
    contacts = relationship("Contact", back_populates="assigned_operator")

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    phone = Column(String, index=True, nullable=True)
    email = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    

    contacts = relationship("Contact", back_populates="lead")

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    

    operator_weights = relationship("OperatorSourceWeight", back_populates="source")
    contacts = relationship("Contact", back_populates="source")

class OperatorSourceWeight(Base):
    __tablename__ = "operator_source_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"))
    source_id = Column(Integer, ForeignKey("sources.id"))
    weight = Column(Float, default=1.0)
    

    operator = relationship("Operator", back_populates="source_weights")
    source = relationship("Source", back_populates="operator_weights")

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    source_id = Column(Integer, ForeignKey("sources.id"))
    assigned_operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True)
    
    status = Column(String, default="new") 
    message_text = Column(Text)
    contact_data = Column(JSON)  
    
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    

    lead = relationship("Lead", back_populates="contacts")
    source = relationship("Source", back_populates="contacts")
    assigned_operator = relationship("Operator", back_populates="contacts")