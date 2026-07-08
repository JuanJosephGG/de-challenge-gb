from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from src.use_cases.historical_migration import process_historical_csv
from src.domain.schemas import HiresByQuarterSchema, DepartmentAboveMeanSchema

# Import database dependency injection
from src.connections.database import get_db

# Import Domain Layer (Data Dictionary & Batch Rules)
from src.domain.schemas import (
    DepartmentBatch, 
    JobBatch, 
    HiredEmployeeBatch
)

# Import Use Case Layer (Business Logic)
from src.use_cases.ingestion import process_employee_batch
from src.use_cases.backup import backup_table_to_s3, restore_table_from_s3

app = FastAPI(
    title="Data Platform Ingestion API",
    description="Robust API for batch ingestion and AVRO backup management",
    version="1.0.0"
)

# ==========================================
# INGESTION ENDPOINTS (Requirement 2 & 3)
# ==========================================

@app.post("/api/v1/departments", status_code=201, tags=["Ingestion"])
def ingest_departments(batch: DepartmentBatch, db: Session = Depends(get_db)):
    """
    Batch ingestion (1 to 1000) for Departments.
    Strict validation automatically occurs in 'batch' via Pydantic.
    """
    # To keep the PoC agile, we use direct insertion here for tables without Foreign Keys.
    # In a complete environment, this would also go to a Use Case.
    from src.domain.models import Department
    
    valid_records = [dept.model_dump() for dept in batch.data]
    db.bulk_insert_mappings(Department, valid_records)
    db.commit()
    
    return {"message": "Batch processed successfully", "inserted": len(valid_records)}


@app.post("/api/v1/jobs", status_code=201, tags=["Ingestion"])
def ingest_jobs(batch: JobBatch, db: Session = Depends(get_db)):
    """Batch ingestion (1 to 1000) for Jobs."""
    from src.domain.models import Job
    
    valid_records = [job.model_dump() for job in batch.data]
    db.bulk_insert_mappings(Job, valid_records)
    db.commit()
    
    return {"message": "Batch processed successfully", "inserted": len(valid_records)}


@app.post("/api/v1/hired_employees", status_code=201, tags=["Ingestion"])
def ingest_hired_employees(batch: HiredEmployeeBatch, db: Session = Depends(get_db)):
    """
    Batch ingestion (1 to 1000) for Employees.
    Executes relational validation: verifies that department_id and job_id exist.
    Invalid records are sent to the DLQ (Logs) without stopping the batch.
    """
    # Delegate complex logic to the Use Case layer
    result = process_employee_batch(db, batch)
    return result


# ==========================================
# ADMINISTRATION ENDPOINTS (Requirements 4 & 5)
# ==========================================

@app.post("/api/v1/admin/backup/{table_name}", tags=["Admin Backup/Restore"])
def create_backup(
    table_name: str = Path(..., description="Options: departments, jobs, hired_employees"),
    db: Session = Depends(get_db)
):
    """Exports the specified table to an AVRO file in S3."""
    try:
        s3_path = backup_table_to_s3(db, table_name)
        return {"message": f"Backup for {table_name} successful", "s3_path": s3_path}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admin/restore/{table_name}", tags=["Admin Backup/Restore"])
def restore_backup(
    s3_key: str, 
    table_name: str = Path(..., description="Options: departments, jobs, hired_employees"),
    db: Session = Depends(get_db)
):
    """
    Restores the specified table from an AVRO file stored in S3.
    Example s3_key: backups/jobs/backup_20260708_120000.avro
    """
    try:
        rows_restored = restore_table_from_s3(db, table_name, s3_key)
        return {"message": f"Restore for {table_name} successful", "rows_restored": rows_restored}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to restore from S3: {str(e)}")
# ==========================================
# HISTORICAL DATA USING GENERIC ENDPOINT
# ==========================================
    
@app.post("/api/v1/historical/{table_name}", status_code=201, tags=["Historical Migration"])
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


# ==========================================
# ANALYTICS & METRICS ENDPOINTS (Requirements 1 & 2)
# ==========================================

@app.get(
    "/api/v1/metrics/hires-by-quarter", 
    response_model=List[HiresByQuarterSchema], 
    tags=["Analytics"]
)
def get_hires_by_quarter(db: Session = Depends(get_db)):
    """
    Returns the number of employees hired for each job and department in 2021 
    divided by quarter. Ordered alphabetically by department and job.
    """
    # Querying the PostgreSQL View directly for maximum performance
    query = text("SELECT * FROM view_metrics_hires_by_quarter;")
    result = db.execute(query).mappings().all()
    
    return [dict(row) for row in result]


@app.get(
    "/api/v1/metrics/departments-above-mean", 
    response_model=List[DepartmentAboveMeanSchema], 
    tags=["Analytics"]
)
def get_departments_above_mean(db: Session = Depends(get_db)):
    """
    Returns the id, name, and number of employees hired for departments 
    that hired MORE than the global mean in 2021. Ordered descending.
    """
    query = text("SELECT * FROM view_metrics_departments_above_mean;")
    result = db.execute(query).mappings().all()
    
    return [dict(row) for row in result]