import io
import fastavro
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Dict, Any

from src.domain.models import Department, Job, HiredEmployee
from src.connections.s3_client import get_s3_client
from src.config.settings import settings
from sqlalchemy.dialects.postgresql import insert

# Configuration dictionary mapping table names to their ORM models and strict Avro schemas
TABLE_CONFIG: Dict[str, Dict[str, Any]] = {
    "departments": {
        "model": Department,
        "avro_schema": {
            "doc": "Backup of departments table",
            "name": "Department",
            "type": "record",
            "fields": [
                {"name": "id", "type": "int"},
                {"name": "department", "type": "string"},
            ],
        }
    },
    "jobs": {
        "model": Job,
        "avro_schema": {
            "doc": "Backup of jobs table",
            "name": "Job",
            "type": "record",
            "fields": [
                {"name": "id", "type": "int"},
                {"name": "job", "type": "string"},
            ],
        }
    },
    "hired_employees": {
        "model": HiredEmployee,
        "avro_schema": {
            "doc": "Backup of hired_employees table",
            "name": "HiredEmployee",
            "type": "record",
            "fields": [
                {"name": "id", "type": "int"},
                {"name": "name", "type": "string"},
                {"name": "datetime", "type": "string"},
                {"name": "department_id", "type": "int"},
                {"name": "job_id", "type": "int"},
            ],
        }
    }
}

def backup_table_to_s3(db: Session, table_name: str) -> str:
    """
    Exports a specific table to an in-memory AVRO format based on its dynamic schema
    and streams it directly to Amazon S3.
    """
    if table_name not in TABLE_CONFIG:
        raise ValueError(f"Table '{table_name}' is not supported for backup.")

    config = TABLE_CONFIG[table_name]
    model = config["model"]
    
    # 1. Extract all records dynamically
    records = db.execute(select(model)).scalars().all()
    
    # Convert SQLAlchemy objects to a list of dictionaries required by fastavro
    # We iterate over the columns defined in the ORM model to extract data dynamically
    data_to_write = [{col.name: getattr(r, col.name) for col in model.__table__.columns} for r in records]
    
    # 2. Write AVRO data to an in-memory buffer (Zero local disk usage)
    buffer = io.BytesIO()
    parsed_schema = fastavro.parse_schema(config["avro_schema"])
    fastavro.writer(buffer, parsed_schema, data_to_write)
    buffer.seek(0)
    
    # 3. Stream buffer directly to S3
    s3_client = get_s3_client()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_key = f"backups/{table_name}/backup_{timestamp}.avro"
    
    s3_client.upload_fileobj(buffer, settings.AWS_S3_BUCKET_NAME, s3_key)
        
    return f"s3://{settings.AWS_S3_BUCKET_NAME}/{s3_key}"

def restore_table_from_s3(db: Session, table_name: str, s3_key: str) -> int:
    """
    Downloads an AVRO file from S3 and restores it using an UPSERT (Merge) strategy.
    This prevents Foreign Key RESTRICT violations by updating existing records 
    instead of deleting them.
    """
    if table_name not in TABLE_CONFIG:
        raise ValueError(f"Table '{table_name}' is not supported for restore.")

    model = TABLE_CONFIG[table_name]["model"]
    s3_client = get_s3_client()
    buffer = io.BytesIO()
    
    # 1. Download S3 object directly into memory
    s3_client.download_fileobj(settings.AWS_S3_BUCKET_NAME, s3_key, buffer)
    buffer.seek(0)
    
    # 2. Read AVRO from memory
    reader = fastavro.reader(buffer)
    records = [record for record in reader]
        
    if records:
        # 3. Create the PostgreSQL UPSERT statement
        stmt = insert(model).values(records)
        
        # 4. Dynamically figure out which columns to update if the ID already exists
        # We update everything except the Primary Key ('id')
        update_dict = {c.name: c for c in stmt.excluded if c.name != 'id'}
        
        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
            
        # 5. Execute the Upsert
        db.execute(stmt)
        db.commit()
        
    return len(records)