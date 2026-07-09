from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Path
from sqlalchemy.orm import Session

# Database, Schemas, Models, and Use Cases
from src.connections.database import get_db
from src.domain.schemas import DepartmentBatch, JobBatch, HiredEmployeeBatch
from src.domain.models import Department, Job
from src.use_cases.ingestion import process_employee_batch
from src.use_cases.historical_migration import process_historical_csv

# Initialize the router (No shared tags here since we have two distinct features)
router = APIRouter(prefix="/api/v1")

@router.post("/departments", status_code=201, tags=["Ingestion"])
def ingest_departments(batch: DepartmentBatch, db: Session = Depends(get_db)):
    """
    Batch ingestion (1 to 1000) for Departments.
    Strict validation automatically occurs in 'batch' via Pydantic.
    """
    valid_records = [dept.model_dump() for dept in batch.data]
    db.bulk_insert_mappings(Department, valid_records)
    db.commit()
    
    return {"message": "Batch processed successfully", "inserted": len(valid_records)}

@router.post("/jobs", status_code=201, tags=["Ingestion"])
def ingest_jobs(batch: JobBatch, db: Session = Depends(get_db)):
    """Batch ingestion (1 to 1000) for Jobs."""
    valid_records = [job.model_dump() for job in batch.data]
    db.bulk_insert_mappings(Job, valid_records)
    db.commit()
    
    return {"message": "Batch processed successfully", "inserted": len(valid_records)}

@router.post("/hired_employees", status_code=201, tags=["Ingestion"])
def ingest_hired_employees(batch: HiredEmployeeBatch, db: Session = Depends(get_db)):
    """
    Batch ingestion (1 to 1000) for Employees.
    Executes relational validation: verifies that department_id and job_id exist.
    Invalid records are sent to the DLQ (Logs) without stopping the batch.
    """
    result = process_employee_batch(db, batch)
    return result

@router.post("/historical/{table_name}", status_code=201, tags=["Historical Migration"])
def upload_historical_data(
    table_name: str = Path(..., description="Options: departments, jobs, hired_employees"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Receives a historical CSV file, stores it in Amazon S3, and then processes its content 
    by performing a bulk insert into the database.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="The file must be a CSV.")

    try:
        result = process_historical_csv(db, table_name, file)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))