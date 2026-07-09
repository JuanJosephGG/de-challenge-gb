import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

from src.connections.s3_client import get_s3_client
from src.config.settings import settings

def invalid_records_to_log(table_name: str, invalid_records: List[Dict[str, Any]]) -> None:
    if not invalid_records:
        return

    jsonl_content = ""
    for record in invalid_records:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_reason": record.get("error_reason", "Razón desconocida"),
            "payload": record.get("payload", {})
        }
        jsonl_content += json.dumps(log_entry) + "\n"

    batch_id = uuid.uuid4().hex[:8]
    today = datetime.now().strftime("%Y-%m-%d")
    
    # The path will be: dlq/hired_employees/2026-07-08/batch_a1b2c3d4.jsonl
    s3_key = f"dlq/{table_name}/{today}/batch_{batch_id}.jsonl"

    # Upload the buffer to S3
    s3_client = get_s3_client()
    try:
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_key,
            Body=jsonl_content.encode('utf-8')
        )
        print(f"✅ DLQ guardado exitosamente en S3: {s3_key}")
    except Exception as e:
        print(f"❌ Error crítico: No se pudo escribir el DLQ en S3: {e}")