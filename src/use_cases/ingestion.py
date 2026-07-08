from sqlalchemy.orm import Session
from sqlalchemy import select
from src.domain.schemas import HiredEmployeeBatch
from src.domain.models import HiredEmployee, Department, Job
from src.use_cases.dlq_manager import invalid_records_to_log

def process_employee_batch(db: Session, batch: HiredEmployeeBatch) -> dict:
    """
    Procesa un lote de empleados. Separa los válidos de los inválidos 
    usando validación relacional en bloque.
    """
    # 1. Extraer IDs únicos para validación en bloque (O(1) consultas a DB)
    unique_dept_ids = {emp.department_id for emp in batch.data}
    unique_job_ids = {emp.job_id for emp in batch.data}

    # 2. Consultar qué IDs realmente existen en la base de datos
    valid_depts = db.scalars(select(Department.id).where(Department.id.in_(unique_dept_ids))).all()
    valid_jobs = db.scalars(select(Job.id).where(Job.id.in_(unique_job_ids))).all()

    valid_dept_set = set(valid_depts)
    valid_job_set = set(valid_jobs)

    valid_records_to_insert = []
    rejected_count = 0

    # 3. Filtrar y separar (Split)
    for emp in batch.data:
        errors = []
        if emp.department_id not in valid_dept_set:
            errors.append(f"department_id {emp.department_id} not found")
        if emp.job_id not in valid_job_set:
            errors.append(f"job_id {emp.job_id} not found")

        if errors:
            # Va al DLQ
            invalid_records_to_log.append({
                "payload": emp.model_dump(),
                "error_reason": " | ".join(errors)
            })
            rejected_count += 1
        else:
            # Es válido, preparamos para inserción masiva
            valid_records_to_insert.append(emp.model_dump())

    # 4. Inserción Masiva (Bulk Insert) de los válidos
    inserted_count = 0
    if valid_records_to_insert:
        db.bulk_insert_mappings(HiredEmployee, valid_records_to_insert)
        db.commit()
        inserted_count = len(valid_records_to_insert)

    return {
        "status": "success",
        "inserted": inserted_count,
        "rejected": rejected_count
    }