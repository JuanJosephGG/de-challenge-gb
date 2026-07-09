from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session
from src.connections.database import get_db
from src.use_cases.backup import backup_table_to_s3, restore_table_from_s3


router = APIRouter(prefix="/api/v1/admin", tags=["Admin Backup/Restore"])

@router.post("/backup/{table_name}")
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

@router.post("/restore/{table_name}")
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