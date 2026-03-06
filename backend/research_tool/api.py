from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ganuda.backend.research_tool import models, schemas, crud
from ganuda.backend.research_tool.database import get_db

router = APIRouter()

@router.get("/research_data/", response_model=List[schemas.ResearchData])
def read_research_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of research data entries.
    """
    research_data = crud.get_research_data(db, skip=skip, limit=limit)
    return research_data

@router.get("/research_data/{data_id}", response_model=schemas.ResearchData)
def read_research_data_by_id(data_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific research data entry by ID.
    """
    db_research_data = crud.get_research_data_by_id(db, data_id=data_id)
    if db_research_data is None:
        raise HTTPException(status_code=404, detail="Research data not found")
    return db_research_data

@router.post("/research_data/", response_model=schemas.ResearchData)
def create_research_data(research_data: schemas.ResearchDataCreate, db: Session = Depends(get_db)):
    """
    Create a new research data entry.
    """
    return crud.create_research_data(db=db, research_data=research_data)

@router.put("/research_data/{data_id}", response_model=schemas.ResearchData)
def update_research_data(data_id: int, research_data: schemas.ResearchDataUpdate, db: Session = Depends(get_db)):
    """
    Update an existing research data entry.
    """
    db_research_data = crud.get_research_data_by_id(db, data_id=data_id)
    if db_research_data is None:
        raise HTTPException(status_code=404, detail="Research data not found")
    return crud.update_research_data(db=db, data_id=data_id, research_data=research_data)

@router.delete("/research_data/{data_id}", response_model=schemas.ResearchData)
def delete_research_data(data_id: int, db: Session = Depends(get_db)):
    """
    Delete a research data entry.
    """
    db_research_data = crud.get_research_data_by_id(db, data_id=data_id)
    if db_research_data is None:
        raise HTTPException(status_code=404, detail="Research data not found")
    return crud.delete_research_data(db=db, data_id=data_id)