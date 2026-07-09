import pytest
from pydantic import ValidationError
from src.domain.schemas import DepartmentBatch, JobBatch, HiredEmployeeBatch

# ==========================================
# 🏢 TESTS FOR DEPARTMENTS
# ==========================================

def test_department_valid_batch():
    """1. Validates that a correct payload for departments is processed successfully."""
    payload = {"data": [{"id": 1, "department": "Engineering"}]}
    batch = DepartmentBatch(**payload)
    
    assert len(batch.data) == 1
    assert batch.data[0].department == "Engineering"
    assert batch.data[0].id == 1

def test_department_missing_name():
    """2. Validates that the absence of the required 'department' field raises an error."""
    payload = {"data": [{"id": 1}]} # Missing the department string
    
    with pytest.raises(ValidationError) as exc_info:
        DepartmentBatch(**payload)
    
    assert "department" in str(exc_info.value)

def test_department_invalid_id_type():
    """3. Validates that an ID with an incorrect data type (letters instead of numbers) is rejected."""
    payload = {"data": [{"id": "not_an_int", "department": "HR"}]}
    
    with pytest.raises(ValidationError) as exc_info:
        DepartmentBatch(**payload)
    
    # Pydantic should specifically complain about the 'id' field
    assert "id" in str(exc_info.value)


# ==========================================
# 💼 TESTS FOR JOBS
# ==========================================

def test_job_valid_batch():
    """1. Validates that a correct payload for jobs is accepted."""
    payload = {"data": [{"id": 1, "job": "Data Engineer"}]}
    batch = JobBatch(**payload)
    
    assert batch.data[0].job == "Data Engineer"

def test_job_missing_job_title():
    """2. Validates that omitting the job title stops validation."""
    payload = {"data": [{"id": 1}]}
    
    with pytest.raises(ValidationError) as exc_info:
        JobBatch(**payload)
        
    assert "job" in str(exc_info.value)

def test_job_invalid_data_structure():
    """3. Validates that sending a structure that is not a list in 'data' fails catastrophically."""
    # Sending a string instead of a list of dictionaries
    payload = {"data": "This should be a list"}
    
    with pytest.raises(ValidationError) as exc_info:
        JobBatch(**payload)
        
    assert "data" in str(exc_info.value)


# ==========================================
# 🧑‍💻 TESTS FOR HIRED EMPLOYEES
# ==========================================

def test_hired_employee_valid_batch():
    """1. Validates that an employee with all fields and foreign keys is accepted."""
    payload = {
        "data": [{
            "id": 1, 
            "name": "Juan Perez", 
            "datetime": "2021-11-07T02:48:42Z", 
            "department_id": 1, 
            "job_id": 1
        }]
    }
    batch = HiredEmployeeBatch(**payload)
    
    assert batch.data[0].name == "Juan Perez"
    assert batch.data[0].department_id == 1

def test_hired_employee_missing_foreign_keys():
    """2. Validates the absence of references (foreign keys) in the payload."""
    payload = {
        "data": [{
            "id": 2, 
            "name": "Maria Lopez", 
            "datetime": "2021-11-07T02:48:42Z"
        }] # Intentionally missing department_id and job_id
    }
    
    with pytest.raises(ValidationError) as exc_info:
        HiredEmployeeBatch(**payload)
        
    error_msg = str(exc_info.value)
    assert "department_id" in error_msg
    assert "job_id" in error_msg

def test_hired_employee_null_values_rejected():
    """3. Validates that sending explicit null values (None/null) in required fields fails."""
    payload = {
        "data": [{
            "id": 3, 
            "name": None, # Name cannot be null
            "datetime": "2021-11-07T02:48:42Z", 
            "department_id": 1, 
            "job_id": 1
        }]
    }
    
    with pytest.raises(ValidationError) as exc_info:
        HiredEmployeeBatch(**payload)
        
    assert "name" in str(exc_info.value)