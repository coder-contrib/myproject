from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel

class EmployeeCreate(BaseModel):
    employee_number: str | None = None
    position: str | None = None
    department_id: UUID | None = None
    user_id: UUID | None = None
    contract_type: str | None = None
    hire_date: date | None = None
    salary: float | None = None

class EmployeeResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    employee_number: str | None
    position: str | None
    contract_type: str | None
    salary: float | None
    created_at: datetime
    model_config = {"from_attributes": True}

class DepartmentCreate(BaseModel):
    name: str
    company_id: UUID | None = None
    manager_id: UUID | None = None

class DepartmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    created_at: datetime
    model_config = {"from_attributes": True}

class LeaveCreate(BaseModel):
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date

class LeaveResponse(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class PayrollCreate(BaseModel):
    employee_id: UUID
    period_start: date
    period_end: date
    base_salary: float
    deductions: float = 0
    bonuses: float = 0

class PayrollResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    employee_id: UUID
    base_salary: float | None
    net_salary: float | None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
