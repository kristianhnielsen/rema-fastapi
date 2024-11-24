from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload
from database.models import Product
from database.operations import get_db
from routers.utils import compare_date

route_prefix = "/product"
router = APIRouter(prefix=route_prefix)


def build_product_query(
    id: int | None,
    department: int | None,
    updated_on: str | None,
    is_available_in_all_stores: bool | None,
    is_batch_item: bool | None,
    is_weight_item: bool | None,
    is_self_scale_item: bool | None,
    temp_zone: int | None,
    age_limit: int | None,
    limit: int | None,
):

    # Start with the base query
    query = select(Product).options(joinedload(Product.prices))

    query_filters = []
    if id is not None:
        query_filters.append(Product.id == id)
    if department is not None:
        query_filters.append(Product.department_id == department)
    if updated_on is not None:
        is_same_date = compare_date(Product.updated, updated_on)
        query_filters.append(is_same_date)
    if is_available_in_all_stores is not None:
        query_filters.append(
            Product.is_available_in_all_stores == is_available_in_all_stores
        )
    if is_batch_item is not None:
        query_filters.append(Product.is_batch_item == is_batch_item)
    if is_weight_item is not None:
        query_filters.append(Product.is_weight_item == is_weight_item)
    if is_self_scale_item is not None:
        query_filters.append(Product.is_self_scale_item == is_self_scale_item)
    if temp_zone is not None:
        query_filters.append(Product.temperature_zone == temp_zone)
    if age_limit is not None:
        query_filters.append(Product.age_limit == age_limit)

    # Apply filters to the query
    if query_filters:
        query = query.where(*query_filters)

    # Apply the limit if provided
    if limit:
        query = query.limit(limit)

    return query


@router.get("/")
async def get_products_by_params(
    id: int | None = None,
    department: int | None = None,
    updated_on: str | None = None,
    is_available_in_all_stores: bool | None = None,
    is_batch_item: bool | None = None,
    is_weight_item: bool | None = None,
    is_self_scale_item: bool | None = None,
    temp_zone: int | None = None,
    age_limit: int | None = None,
    limit: int | None = None,
    session: Session = Depends(get_db),
):

    # Build query
    query = build_product_query(
        id,
        department,
        updated_on,
        is_available_in_all_stores,
        is_batch_item,
        is_weight_item,
        is_self_scale_item,
        temp_zone,
        age_limit,
        limit,
    )

    # Query database
    products = session.execute(query).scalars().unique().all()

    if products is None:
        raise HTTPException(status_code=404, detail="No products were found.")

    return products
