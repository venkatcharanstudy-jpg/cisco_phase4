from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from ..schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from ..services.employee_service import EmployeeService
from .deps import get_employee_service

router = APIRouter(prefix="/employees", tags=["employees"])

ServiceDep = Annotated[EmployeeService, Depends(get_employee_service)]


@router.post("", response_model=EmployeeResponse, status_code=201)
def create_employee(payload: EmployeeCreate, service: ServiceDep):
    return service.create_employee(payload)


@router.get("", response_model=list[EmployeeResponse])
def list_employees(service: ServiceDep):
    return service.list_employees()


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, service: ServiceDep):
    return service.get_employee(employee_id)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, payload: EmployeeUpdate, service: ServiceDep):
    return service.update_employee(employee_id, payload)


@router.delete("/{employee_id}", status_code=204, response_class=Response)
def delete_employee(employee_id: int, service: ServiceDep):
    service.delete_employee(employee_id)
    return Response(status_code=204)
