from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from models import Base, Operator, Lead, Source, OperatorSourceWeight, Contact
from backend.db import get_db
from schemas import (
    OperatorCreate, Operator as OperatorSchema, OperatorUpdate, 
    LeadCreate, Lead as LeadSchema,
    SourceCreate, Source as SourceSchema, 
    OperatorWeightCreate, OperatorWeight as OperatorWeightSchema,
    ContactCreate, ContactResponse, DistributionStats
)
from services.distribution_service import LeadDistributionService, StatisticsService

app = FastAPI(
    title="Lead Distribution Service",
    description="Сервис распределения обращений лидов между операторами",
    version="1.0.0"
)

@app.post("/operators/", response_model=OperatorSchema, status_code=status.HTTP_201_CREATED)
def create_operator(operator: OperatorCreate, db=Depends(get_db)):
    existing_operator = db.query(Operator).filter(Operator.email == operator.email).first()
    if existing_operator:
        raise HTTPException(
            status_code=400,
            detail="Operator with this email already exists"
        )
    
    db_operator = Operator(**operator.dict())
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    return db_operator

@app.get("/operators/", response_model=List[OperatorSchema])
def read_operators(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    operators = db.query(Operator).offset(skip).limit(limit).all()
    
    stats_service = StatisticsService(db)
    for operator in operators:
        operator.current_active_leads = stats_service.get_operator_active_leads_count(operator.id)
    
    return operators

@app.get("/operators/{operator_id}", response_model=OperatorSchema)
def read_operator(operator_id: int, db=Depends(get_db)):
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if operator is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    stats_service = StatisticsService(db)
    operator.current_active_leads = stats_service.get_operator_active_leads_count(operator.id)
    
    return operator

@app.patch("/operators/{operator_id}", response_model=OperatorSchema)
def update_operator(operator_id: int, operator_update: OperatorUpdate, db=Depends(get_db)):
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if operator is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    update_data = operator_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(operator, field, value)
    
    db.commit()
    db.refresh(operator)
    return operator

@app.post("/sources/", response_model=SourceSchema, status_code=status.HTTP_201_CREATED)
def create_source(source: SourceCreate, db=Depends(get_db)):
    existing_source = db.query(Source).filter(Source.name == source.name).first()
    if existing_source:
        raise HTTPException(
            status_code=400,
            detail="Source with this name already exists"
        )
    
    db_source = Source(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@app.get("/sources/", response_model=List[SourceSchema])
def read_sources(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    sources = db.query(Source).offset(skip).limit(limit).all()
    return sources

@app.post("/operator-weights/", response_model=OperatorWeightSchema, status_code=status.HTTP_201_CREATED)
def create_operator_weight(weight: OperatorWeightCreate, db=Depends(get_db)):
    operator = db.query(Operator).filter(Operator.id == weight.operator_id).first()
    source = db.query(Source).filter(Source.id == weight.source_id).first()
    
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    existing_weight = db.query(OperatorSourceWeight).filter(
        OperatorSourceWeight.operator_id == weight.operator_id,
        OperatorSourceWeight.source_id == weight.source_id
    ).first()
    
    if existing_weight:
        raise HTTPException(
            status_code=400,
            detail="Weight for this operator and source already exists"
        )
    
    db_weight = OperatorSourceWeight(**weight.dict())
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight

@app.get("/sources/{source_id}/operators/")
def get_source_operators(source_id: int, db=Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    weights = db.query(OperatorSourceWeight).filter(
        OperatorSourceWeight.source_id == source_id
    ).all()
    
    result = []
    for weight in weights:
        operator = weight.operator
        result.append({
            "operator_id": operator.id,
            "operator_name": operator.name,
            "weight": weight.weight,
            "is_active": operator.is_active
        })
    
    return {
        "source_id": source.id,
        "source_name": source.name,
        "operators": result
    }

@app.post("/contacts/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(contact: ContactCreate, db=Depends(get_db)):
    distribution_service = LeadDistributionService(db)
    
    try:
        db.begin()
        
        lead = distribution_service.find_or_create_lead(
            external_id=contact.external_id,
            phone=contact.phone,
            email=contact.email
        )
        
        new_contact, assigned_operator = distribution_service.create_contact(
            lead=lead,
            source_id=contact.source_id,
            message_text=contact.message_text,
            contact_data=contact.contact_data
        )
        
        db.commit()
        
        message = "Contact created successfully"
        if assigned_operator:
            message = f"Contact assigned to operator {assigned_operator.name}"
        else:
            message = "Contact created but no available operators found"
        
        def orm_to_dict(orm_obj):
            if orm_obj is None:
                return None
            return {c.name: getattr(orm_obj, c.name) for c in orm_obj.__table__.columns}
        
        return ContactResponse(
            contact=orm_to_dict(new_contact),
            lead=orm_to_dict(lead),
            assigned_operator=orm_to_dict(assigned_operator),
            message=message
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating contact: {str(e)}")
    finally:
        db.close()

@app.get("/leads/{lead_id}/contacts/")
def get_lead_contacts(lead_id: int, db=Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    stats_service = StatisticsService(db)
    contacts = stats_service.get_lead_contacts(lead_id)
    
    return {
        "lead": lead,
        "contacts": contacts
    }

@app.get("/stats/distribution/", response_model=DistributionStats)
def get_distribution_stats(db=Depends(get_db)):
    stats_service = StatisticsService(db)
    
    total_contacts = db.query(Contact).count()
    assigned_contacts = db.query(Contact).filter(Contact.assigned_operator_id.isnot(None)).count()
    unassigned_contacts = total_contacts - assigned_contacts
    operator_stats = stats_service.get_operator_stats()
    
    return DistributionStats(
        total_contacts=total_contacts,
        assigned_contacts=assigned_contacts,
        unassigned_contacts=unassigned_contacts,
        operator_stats=operator_stats
    )

@app.get("/")
def root():
    return {"message": "Lead Distribution Service", "version": "1.0.0"}