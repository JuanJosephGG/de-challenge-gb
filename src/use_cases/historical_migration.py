import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from fastapi import UploadFile
from src.connections.s3_client import upload_file_to_s3
from src.config.settings import settings
from src.domain.models import Department, Job
from src.domain.schemas import HiredEmployeeSchema, HiredEmployeeBatch
from src.use_cases.ingestion import process_employee_batch
from src.use_cases.dlq_manager import invalid_records_to_log
from pydantic import ValidationError

TABLE_COLUMNS = {
    "departments": ["id", "department"],
    "jobs": ["id", "job"],
    "hired_employees": ["id", "name", "datetime", "department_id", "job_id"]
}

def process_historical_csv(db: Session, table_name: str, file: UploadFile) -> dict:
    if table_name not in TABLE_COLUMNS:
        raise ValueError(f"Table '{table_name}' not supported.")

    # Upload to S3
    s3_key = f"bronze/{table_name}/{file.filename}"
    if not upload_file_to_s3(file.file, s3_key):
        raise Exception("Failed to upload the file to S3.")

    # Read CSV from S3 into a DataFrame
    s3_path = f"s3://{settings.AWS_S3_BUCKET_NAME}/{s3_key}"
    df = pd.read_csv(
        s3_path, 
        names=TABLE_COLUMNS[table_name],
        storage_options={
            "key": settings.AWS_ACCESS_KEY_ID,
            "secret": settings.AWS_SECRET_ACCESS_KEY
        }
    )
    
    # Replace NaN with None for SQLAlchemy compatibility
    df = df.replace({np.nan: None})
    records = df.to_dict(orient="records")

    inserted_total = 0
    rejected_total = 0

    # 3. Insertion and Validation via Use Case Layer
    if table_name == "hired_employees":
        # Process in batches to avoid memory issues and to respect the batch size limit
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            chunk = records[i:i + batch_size]
            valid_pydantic_records = []
            error_batch = []
            
            # A. Structural Validation (Pydantic: Required fields and ISO format)
            for record in chunk:
                try:
                    valid_emp = HiredEmployeeSchema(**record)
                    valid_pydantic_records.append(valid_emp)
                except ValidationError as e:
                    error_msg = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
                    error_batch.append({
                        "payload": record,
                        "error_reason": error_msg
                    })
                    rejected_total += 1
            
            if error_batch:
                invalid_records_to_log(table_name, error_batch)
            
            # B. Relational Validation and Saving
            if valid_pydantic_records:
                batch_schema = HiredEmployeeBatch(data=valid_pydantic_records)
                result = process_employee_batch(db, batch_schema)
                inserted_total += result["inserted"]
                rejected_total += result["rejected"]

    else:
        model = Department if table_name == "departments" else Job
        
        # Filter out basic nulls before insertion
        valid_records = [r for r in records if r["id"] is not None]
        rejected_total += len(records) - len(valid_records)
        
        if valid_records:
            db.bulk_insert_mappings(model, valid_records)
            db.commit()
            inserted_total += len(valid_records)

    return {
        "status": "success",
        "message": "Historical migration completed.",
        "s3_path": s3_path,
        "original_rows": len(records),
        "db_table_name": table_name,
        "rows_inserted": inserted_total,
        "rows_rejected_to_dlq": rejected_total
    }