from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class OperatorBase(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True
    max_active_leads: int = 5

class OperatorCreate(OperatorBase):
    pass

class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    max_active_leads: Optional[int] = None

class Operator(OperatorBase):
    id: int
    current_active_leads: Optional[int] = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

class LeadBase(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class LeadCreate(LeadBase):
    external_id: str

class Lead(LeadBase):
    id: int
    external_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SourceBase(BaseModel):
    name: str
    description: Optional[str] = None

class SourceCreate(SourceBase):
    pass

class Source(SourceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class OperatorWeightBase(BaseModel):
    operator_id: int
    source_id: int
    weight: float = 1.0

class OperatorWeightCreate(OperatorWeightBase):
    pass

class OperatorWeight(OperatorWeightBase):
    id: int
    
    class Config:
        from_attributes = True

class ContactBase(BaseModel):
    source_id: int
    message_text: Optional[str] = None
    contact_data: Optional[Dict[str, Any]] = None

class ContactCreate(ContactBase):
    external_id: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class Contact(ContactBase):
    id: int
    contact_id: str
    lead_id: int
    assigned_operator_id: Optional[int]
    status: str
    created_at: datetime
    assigned_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ContactResponse(BaseModel):
    contact: Contact
    lead: Lead
    assigned_operator: Optional[Operator] = None
    message: str

class DistributionStats(BaseModel):
    total_contacts: int
    assigned_contacts: int
    unassigned_contacts: int
    operator_stats: List[Dict[str, Any]]