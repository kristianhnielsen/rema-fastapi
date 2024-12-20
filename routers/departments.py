from fastapi import APIRouter, Depends
from sqlalchemy import select
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
    return [
        {"name": dept.department_name, "id": dept.department_id} for dept in departments
    ]


@router.get("/{department_id}/count")
async def get_products_count(department_id: int, session: Session = Depends(get_db)):
    count = session.query(Product).where(Product.department_id == department_id).count()
    return count


@router.get("/{department_id}")
async def get_products_from_department(
    department_id: int,
    limit: int | None = None,
    offset: int | None = None,
    session: Session = Depends(get_db),
):
    query = (
        select(Product)
        .where(Product.department_id == department_id)
        .order_by(Product.name)
        .limit(limit)
        .offset(offset)
    )
    products = session.execute(query).scalars().all()
    return products
