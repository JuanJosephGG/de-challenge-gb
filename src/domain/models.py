from sqlalchemy import Column, Integer, String, ForeignKey
from src.connections.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String, nullable=False)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job = Column(String, nullable=False)


class HiredEmployee(Base):
    __tablename__ = "hired_employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    datetime = Column(String, nullable=False)  
    # If a department is deleted, it will fail instead of setting to NULL, preserving integrity
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False)