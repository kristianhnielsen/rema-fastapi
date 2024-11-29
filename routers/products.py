from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from database.models import Product
from database.operations import get_db

route_prefix = "/product"
router = APIRouter(prefix=route_prefix)


@router.get("/")
async def get_all_products(
    limit: int | None = None, session: Session = Depends(get_db)
):

    query = select(
        Product.id, Product.name, Product.department_name, Product.image
    ).limit(limit)

    products = session.execute(query).all()

    return [
        {"id": prod[1], "name": prod[0], "department": prod[2], "img": prod[3]}
        for prod in products
    ]


@router.get("/{id}")
async def get_product_by_id(
    id: int,
    session: Session = Depends(get_db),
):
    query = select(Product).options(joinedload(Product.prices)).where(Product.id == id)
    product = session.execute(query).scalars().unique().one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product
