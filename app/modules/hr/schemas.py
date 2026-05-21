from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, field_validator


# --- Department ---

class DepartmentCreate(BaseModel):
    name: str
    manager_id: UUID | None = None

class DepartmentUpdate(BaseModel):
    name: str | None = None
    manager_id: UUID | None = None

class DepartmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    manager_id: UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Employee ---

class EmployeeCreate(BaseModel):
    user_id: UUID | None = None
    department_id: UUID | None = None
    employee_number: str | None = None
    position: str | None = None
    national_id: str | None = None
    contract_type: str | None = None
    hire_date: date | None = None
    salary: float | None = None

class EmployeeUpdate(BaseModel):
    department_id: UUID | None = None
    position: str | None = None
    contract_type: str | None = None
    salary: float | None = None

class EmployeeResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID | None
    department_id: UUID | None
    employee_number: str | None
    position: str | None
    national_id: str | None
    contract_type: str | None
    hire_date: date | None
    salary: float | None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Attendance ---

class AttendanceCreate(BaseModel):
    employee_id: UUID
    date: date
    check_in: datetime | None = None
    check_out: datetime | None = None

class AttendanceResponse(BaseModel):
    id: UUID
    employee_id: UUID
    date: date
    check_in: datetime | None
    check_out: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Leave ---

class LeaveCreate(BaseModel):
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date

    @field_validator("leave_type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        allowed = {"annual", "sick", "unpaid", "maternity", "paternity", "emergency"}
        if v not in allowed:
            raise ValueError(f"Leave type must be one of: {', '.join(allowed)}")
        return v

class LeaveActionRequest(BaseModel):
    action: str

    @field_validator("action")
    @classmethod
    def valid_action(cls, v: str) -> str:
        if v not in ("approve", "reject"):
            raise ValueError("Action must be 'approve' or 'reject'")
        return v

class LeaveResponse(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    status: str
    approved_by: UUID | None
    approved_at: datetime | None
    rejection_reason: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Payroll ---

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
    period_start: date
    period_end: date
    base_salary: float | None
    deductions: float
    bonuses: float
    net_salary: float | None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class PayrollStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"draft", "approved", "paid", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v
