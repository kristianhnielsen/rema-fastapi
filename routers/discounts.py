from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload
from database.models import Price, Product
from database.operations import get_db
from routers.models import DiscountDeal, DiscountDepartment

route_prefix = "/discount"
router = APIRouter(prefix=route_prefix)


@router.get("/")
async def get_all_advertised_products(db: Session = Depends(get_db)):

    today = datetime.today()
    query = (
        select(Product)
        .order_by(Product.department_id)
        .join(Price, Product.prices)
        .where(
            and_(
                Price.is_advertised == True,
                Price.starting_at <= today,
                Price.ending_at >= today,
            )
        )
        .distinct()
    ).options(joinedload(Product.prices))

    products = db.execute(query).unique().scalars().all()
    return products


@router.get("/departments")
async def get_department_deals(db: Session = Depends(get_db)):
    # Aggregate department-level price data
    department_prices = db.execute(
        select(
            Product.department_id,
            Product.department_name,
            func.avg(Price.price).label("avg_price"),
            func.min(Price.price).label("min_price"),
            func.max(Price.price).label("max_price"),
        )
        .join(Price, Product.id == Price.product_id)
        .group_by(Product.department_id, Product.department_name)
    ).all()

    # Find advertised products and calculate price differences
    # Get today's date
    today = datetime.today()
    advertised_products = db.execute(
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.image,
            Product.department_name,
            Product.department_id,
            Price.price.label("advertised_price"),
            (
                select(Price.price)
                .where(
                    Price.product_id == Product.id,
                    Price.is_advertised == False,
                    # Price.starting_at < today,
                )
                .limit(1)  # Only get the closest match
                .correlate(Product)  # Ensure correlation with the outer query
                .scalar_subquery()
            ).label("regular_price"),
        )
        .join(Price, Product.id == Price.product_id)
        .where(
            Price.is_advertised == True,
            Price.starting_at <= today,
            Price.ending_at >= today,
        )
        .distinct()  # Ensure no duplicates for the advertised prices
    ).all()

    # Process and structure the response
    departments: List[DiscountDepartment] = []
    for dept in department_prices:
        # Base department object
        department = DiscountDepartment(
            avg_price=dept.avg_price,
            min_price=dept.min_price,
            max_price=dept.max_price,
            department_name=dept.department_name,
            department_id=dept.department_id,
        )

        # Add the deal to the respective department
        for product in advertised_products:
            # Base  deal object
            if product.department_id == department.department_id:
                deal = DiscountDeal(
                    product_id=product.product_id,
                    product_name=product.product_name,
                    image=product.image,
                    advertised_price=product.advertised_price,
                    regular_price=product.regular_price,
                )
                department.deals.append(deal)

        department.calc_avg_diff_amount()
        department.calc_avg_diff_percent()
        departments.append(department)

    # Sort deals on price difference in percent
    for department in departments:
        department.sort_deals_by_discount_percent()

    # Sort list by department_id
    departments_sorted_by_id = sorted(departments, key=lambda dept: dept.department_id)

    return departments_sorted_by_id
