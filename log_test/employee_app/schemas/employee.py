from pydantic import BaseModel, ConfigDict, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class EmployeeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=EMAIL_PATTERN)
    department: str = Field(min_length=1, max_length=50)
    designation: str = Field(min_length=1, max_length=50)


class EmployeeUpdate(BaseModel):
    """Partial update: omitted or null fields are left unchanged."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, pattern=EMAIL_PATTERN)
    department: str | None = Field(default=None, min_length=1, max_length=50)
    designation: str | None = Field(default=None, min_length=1, max_length=50)


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    department: str
    designation: str
