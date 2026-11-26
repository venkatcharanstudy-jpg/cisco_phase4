class EmployeeError(Exception):
    """Base class for employee domain errors."""


class EmployeeNotFoundError(EmployeeError):
    def __init__(self, employee_id: int) -> None:
        super().__init__(f"Employee with id {employee_id} not found")
        self.employee_id = employee_id


class EmployeeAlreadyExistsError(EmployeeError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Employee with email '{email}' already exists")
        self.email = email
