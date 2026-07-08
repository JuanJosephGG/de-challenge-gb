from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List

# --- Base Schemas (for Ingestion) ---

class DepartmentSchema(BaseModel):
    id: int
    department: str = Field(..., min_length=1)

class JobSchema(BaseModel):
    id: int
    job: str = Field(..., min_length=1)

class HiredEmployeeSchema(BaseModel):
    id: int
    name: str = Field(..., min_length=1)
    datetime: str
    department_id: int
    job_id: int

    @field_validator("datetime")
    @classmethod
    def validate_iso_format(cls, value: str) -> str:
        """
        Validates that the string is a valid ISO 8601 format 
        (e.g., 2021-07-27T16:02:08Z).
        """
        try:
            # Replace 'Z' with '+00:00' so Python 3.13's native parser can understand it without extra libraries
            parsed_time = value.replace("Z", "+00:00")
            datetime.fromisoformat(parsed_time)
            return value
        except ValueError:
            raise ValueError(f"Invalid ISO format: {value}. Expected format: YYYY-MM-DDTHH:MM:SSZ")


# --- Batch Schemas (for the REST API - Consideration 2) ---
# Use lists of the base schemas with size validators
class DepartmentBatch(BaseModel):
    data: List[DepartmentSchema] = Field(..., min_length=1, max_length=1000)

class JobBatch(BaseModel):
    data: List[JobSchema] = Field(..., min_length=1, max_length=1000)

class HiredEmployeeBatch(BaseModel):
    data: List[HiredEmployeeSchema] = Field(..., min_length=1, max_length=1000)

# --- Analytics / Metrics Schemas ---
class HiresByQuarterSchema(BaseModel):
    department: str
    job: str
    q1: int
    q2: int
    q3: int
    q4: int

class DepartmentAboveMeanSchema(BaseModel):
    id: int
    department: str
    hired: int

