from dataclasses import replace

from ..models.employee import Employee


class EmployeeRepository:
    """In-memory storage. Replace with a database-backed implementation later."""

    def __init__(self) -> None:
        self._employees: dict[int, Employee] = {}
        self._next_id = 1

    def create(self, fields: dict[str, str]) -> Employee:
        employee = Employee(id=self._next_id, **fields)
        self._employees[employee.id] = employee
        self._next_id += 1
        return employee

    def get(self, employee_id: int) -> Employee | None:
        return self._employees.get(employee_id)

    def list_all(self) -> list[Employee]:
        return list(self._employees.values())

    def update(self, employee_id: int, fields: dict[str, str]) -> Employee:
        updated = replace(self._employees[employee_id], **fields)
        self._employees[employee_id] = updated
        return updated

    def delete(self, employee_id: int) -> None:
        del self._employees[employee_id]

    def find_by_email(self, email: str) -> Employee | None:
        target = email.lower()
        for employee in self._employees.values():
            if employee.email.lower() == target:
                return employee
        return None
