from typing import List, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from ganuda.backend.models.federation import Federation
from ganuda.backend.schemas.federation import FederationCreate, FederationUpdate


class FederationService:
    def __init__(self, db: Session):
        self.db = db

    def get_federations(self) -> List[Federation]:
        """
        Retrieve all federations from the database.
        """
        return self.db.query(Federation).all()

    def get_federation(self, federation_id: int) -> Optional[Federation]:
        """
        Retrieve a specific federation by ID.
        """
        return self.db.query(Federation).filter(Federation.id == federation_id).first()

    def create_federation(self, federation: FederationCreate) -> Federation:
        """
        Create a new federation in the database.
        """
        db_federation = Federation(**federation.dict())
        self.db.add(db_federation)
        self.db.commit()
        self.db.refresh(db_federation)
        return db_federation

    def update_federation(self, federation_id: int, federation: FederationUpdate) -> Optional[Federation]:
        """
        Update an existing federation in the database.
        """
        db_federation = self.get_federation(federation_id)
        if db_federation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Federation not found")
        
        for key, value in federation.dict().items():
            setattr(db_federation, key, value)
        
        self.db.commit()
        self.db.refresh(db_federation)
        return db_federation

    def delete_federation(self, federation_id: int) -> None:
        """
        Delete a federation from the database.
        """
        db_federation = self.get_federation(federation_id)
        if db_federation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Federation not found")
        
        self.db.delete(db_federation)
        self.db.commit()