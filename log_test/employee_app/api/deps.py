from functools import lru_cache

from fastapi import Depends

from ..repositories.employee_repository import EmployeeRepository
from ..services.employee_service import EmployeeService


@lru_cache
def get_employee_repository() -> EmployeeRepository:
    return EmployeeRepository()


def get_employee_service(
    repository: EmployeeRepository = Depends(get_employee_repository),
) -> EmployeeService:
    return EmployeeService(repository)
