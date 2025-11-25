from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Operator, Lead, Source, OperatorSourceWeight, Contact
from typing import List, Optional, Dict, Any
import random
from datetime import datetime
import json

class LeadDistributionService:
    def __init__(self, db: Session):
        self.db = db
    
    def find_or_create_lead(self, external_id: str, phone: Optional[str] = None, 
                          email: Optional[str] = None) -> Lead:
        lead = self.db.query(Lead).filter(Lead.external_id == external_id).first()
        
        if not lead:
            if phone:
                lead = self.db.query(Lead).filter(Lead.phone == phone).first()
            if not lead and email:
                lead = self.db.query(Lead).filter(Lead.email == email).first()
        
        if not lead:
            lead = Lead(
                external_id=external_id,
                phone=phone,
                email=email
            )
            self.db.add(lead)
            self.db.flush()
        
        return lead
    
    def get_operator_active_leads_count(self, operator_id: int) -> int:
        return self.db.query(Contact).filter(
            Contact.assigned_operator_id == operator_id,
            Contact.status.in_(["new", "in_progress"])
        ).count()
    
    def get_available_operators_for_source(self, source_id: int) -> List[Dict[str, Any]]:
        operator_weights = (
            self.db.query(OperatorSourceWeight)
            .join(Operator)
            .filter(
                OperatorSourceWeight.source_id == source_id,
                Operator.is_active == True
            )
            .all()
        )
        
        available_operators = []
        
        for ow in operator_weights:
            operator = ow.operator
            active_leads_count = self.get_operator_active_leads_count(operator.id)
            
            if active_leads_count < operator.max_active_leads:
                available_operators.append({
                    "operator": operator,
                    "weight": ow.weight,
                    "current_load": active_leads_count,
                    "max_load": operator.max_active_leads
                })
        
        return available_operators
    
    def select_operator_by_weights(self, available_operators: List[Dict[str, Any]]) -> Optional[Operator]:
        if not available_operators:
            return None
        
        weighted_list = []
        for op_data in available_operators:
            weight = int(op_data["weight"] * 100)
            weighted_list.extend([op_data["operator"]] * weight)
        
        return random.choice(weighted_list)
    
    def create_contact(self, lead: Lead, source_id: int, message_text: Optional[str] = None,
                    contact_data: Optional[Dict[str, Any]] = None) -> tuple[Contact, Optional[Operator]]:
        available_operators = self.get_available_operators_for_source(source_id)
        
        selected_operator = self.select_operator_by_weights(available_operators)
        
        contact = Contact(
            lead_id=lead.id,
            source_id=source_id,
            assigned_operator_id=selected_operator.id if selected_operator else None,
            message_text=message_text,
            contact_data=contact_data,
            status="new",
            assigned_at=datetime.utcnow() if selected_operator else None
        )
        
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        
        return contact, selected_operator

class StatisticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_operator_stats(self) -> List[Dict[str, Any]]:
        operators = self.db.query(Operator).all()
        stats = []
        
        for operator in operators:
            active_leads = self.get_operator_active_leads_count(operator.id)
            total_assigned = self.db.query(Contact).filter(
                Contact.assigned_operator_id == operator.id
            ).count()
            
            stats.append({
                "operator_id": operator.id,
                "operator_name": operator.name,
                "is_active": operator.is_active,
                "active_leads": active_leads,
                "max_active_leads": operator.max_active_leads,
                "total_assigned": total_assigned,
                "utilization": f"{(active_leads / operator.max_active_leads * 100):.1f}%" if operator.max_active_leads > 0 else "0%"
            })
        
        return stats
    
    def get_operator_active_leads_count(self, operator_id: int) -> int:
        return self.db.query(Contact).filter(
            Contact.assigned_operator_id == operator_id,
            Contact.status.in_(["new", "in_progress"])
        ).count()
    
    def get_lead_contacts(self, lead_id: int) -> List[Contact]:
        return self.db.query(Contact).filter(Contact.lead_id == lead_id).all()