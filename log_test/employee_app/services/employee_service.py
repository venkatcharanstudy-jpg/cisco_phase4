import logging

from ..core.exceptions import EmployeeAlreadyExistsError, EmployeeNotFoundError
from ..models.employee import Employee
from ..repositories.employee_repository import EmployeeRepository
from ..schemas.employee import EmployeeCreate, EmployeeUpdate

logger = logging.getLogger(__name__)


class EmployeeService:
    def __init__(self, repository: EmployeeRepository) -> None:
        self._repository = repository

    def create_employee(self, data: EmployeeCreate) -> Employee:
        self._ensure_email_available(data.email)
        employee = self._repository.create(data.model_dump())
        logger.info("Created employee id=%s email=%s", employee.id, employee.email)
        return employee

    def list_employees(self) -> list[Employee]:
        employees = self._repository.list_all()
        logger.debug("Listed %d employees", len(employees))
        return employees

    def get_employee(self, employee_id: int) -> Employee:
        employee = self._repository.get(employee_id)
        if employee is None:
            logger.warning("Employee id=%s not found", employee_id)
            raise EmployeeNotFoundError(employee_id)
        return employee

    def update_employee(self, employee_id: int, data: EmployeeUpdate) -> Employee:
        self.get_employee(employee_id)
        fields = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if "email" in fields:
            self._ensure_email_available(fields["email"], exclude_id=employee_id)
        employee = self._repository.update(employee_id, fields)
        logger.info("Updated employee id=%s fields=%s", employee_id, sorted(fields))
        return employee

    def delete_employee(self, employee_id: int) -> None:
        self.get_employee(employee_id)
        self._repository.delete(employee_id)
        logger.info("Deleted employee id=%s", employee_id)

    def _ensure_email_available(self, email: str, exclude_id: int | None = None) -> None:
        existing = self._repository.find_by_email(email)
        if existing is not None and existing.id != exclude_id:
            logger.warning("Duplicate email rejected: %s", email)
            raise EmployeeAlreadyExistsError(email)
