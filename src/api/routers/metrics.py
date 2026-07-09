from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

# Database and Schemas
from src.connections.database import get_db
from src.domain.schemas import HiresByQuarterSchema, DepartmentAboveMeanSchema

# Initialize the router with a shared prefix and tag
router = APIRouter(prefix="/api/v1/metrics", tags=["Analytics"])

@router.get("/hires-by-quarter", response_model=List[HiresByQuarterSchema])
def get_hires_by_quarter(db: Session = Depends(get_db)):
    """
    Returns the number of employees hired for each job and department in 2021 
    divided by quarter. Ordered alphabetically by department and job.
    """
    # Querying the PostgreSQL View directly for maximum performance
    query = text("SELECT * FROM view_metrics_hires_by_quarter;")
    result = db.execute(query).mappings().all()
    
    return [dict(row) for row in result]

@router.get("/departments-above-mean", response_model=List[DepartmentAboveMeanSchema])
def get_departments_above_mean(db: Session = Depends(get_db)):
    """
    Returns the id, name, and number of employees hired for departments 
    that hired MORE than the global mean in 2021. Ordered descending.
    """
    query = text("SELECT * FROM view_metrics_departments_above_mean;")
    result = db.execute(query).mappings().all()
    
    return [dict(row) for row in result]