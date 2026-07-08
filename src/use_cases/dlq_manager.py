import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Asumiendo tu estructura simplificada
from src.connections.s3_client import get_s3_client
from src.config.settings import settings

def invalid_records_to_log(table_name: str, invalid_records: List[Dict[str, Any]]) -> None:
    """
    Toma una lista de registros inválidos de un lote, los convierte a JSON Lines 
    en memoria y sube el archivo a Amazon S3 en la ruta dlq/.
    """
    if not invalid_records:
        return

    # 1. Construir el contenido JSON Lines en memoria
    jsonl_content = ""
    for record in invalid_records:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_reason": record.get("error_reason", "Razón desconocida"),
            "payload": record.get("payload", {})
        }
        jsonl_content += json.dumps(log_entry) + "\n"

    # 2. Crear una ruta única en S3 por cada lote procesado
    # Usamos UUID para evitar colisiones si llegan peticiones concurrentes
    batch_id = uuid.uuid4().hex[:8]
    today = datetime.now().strftime("%Y-%m-%d")
    
    # La ruta será: dlq/hired_employees/2026-07-08/batch_a1b2c3d4.jsonl
    s3_key = f"dlq/{table_name}/{today}/batch_{batch_id}.jsonl"

    # 3. Subir el buffer directamente a S3
    s3_client = get_s3_client()
    try:
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_key,
            Body=jsonl_content.encode('utf-8')
        )
        print(f"✅ DLQ guardado exitosamente en S3: {s3_key}")
    except Exception as e:
        # Aquí enviaríamos una alerta a Datadog/CloudWatch en producción
        print(f"❌ Error crítico: No se pudo escribir el DLQ en S3: {e}")