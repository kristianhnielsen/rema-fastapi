from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.models import Product
from database.operations import get_db


route_prefix = "/department"
router = APIRouter(prefix=route_prefix)


@router.get("/")
async def get_all_departments(session: Session = Depends(get_db)):
    departments = (
        session.query(Product.department_name, Product.department_id).distinct().all()
    )
    return {
        "departments": [
            {"name": dept.department_name, "id": dept.department_id}
            for dept in departments
        ]
    }
