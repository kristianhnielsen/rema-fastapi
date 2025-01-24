from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import and_, desc, func, select
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
async def get_all_departments_deals(db: Session = Depends(get_db)):
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


@router.get("/departments/{department_id}")
async def get_department_deals(department_id: int, db: Session = Depends(get_db)):

    # Find advertised products and calculate price differences
    # Get today's date
    today = datetime.today()
    # Subquery to find the closest starting_at date for each product
    closest_advertisement_subquery = (
        select(
            Price.product_id,
            func.min(Price.starting_at).label("closest_starting_at"),
        )
        .where(
            and_(
                Price.is_advertised == True,
                Price.starting_at <= today,
                Price.ending_at >= today,
            )
        )
        .group_by(Price.product_id)
        .subquery()
    )

    # Main query to get the relevant products with the closest advertisement
    advertised_products = db.execute(
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.image,
            Product.department_name,
            Product.department_id,
            Price.price.label("advertised_price"),
            (
                select(func.coalesce(Price.price, Price.price))  # Handle NULLs
                .where(
                    Price.product_id == Product.id,
                    Price.is_advertised == False,
                )
                .limit(1)
                .correlate(Product)
                .scalar_subquery()
            ).label("regular_price"),
        )
        .join(Price, Product.id == Price.product_id)
        .join(
            closest_advertisement_subquery,
            and_(
                Price.product_id == closest_advertisement_subquery.c.product_id,
                Price.starting_at
                == closest_advertisement_subquery.c.closest_starting_at,
            ),
        )
        .where(
            Product.department_id == department_id,
        )
        .distinct()
    ).all()

    # Process and structure the response
    department_deals = [
        DiscountDeal(
            product_id=product.product_id,
            product_name=product.product_name,
            image=product.image,
            advertised_price=product.advertised_price,
            regular_price=product.regular_price,
        )
        for product in advertised_products
    ]
    department_deals_sorted = sorted(
        department_deals, key=lambda product: product.difference_amount, reverse=True
    )

    return department_deals_sorted


@router.get("/top-10-discounts")
async def get_top_10_discount_products(db: Session = Depends(get_db)):
    # Get today's date
    today = datetime.today()

    # Find advertised products and calculate price differences
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

    allDeals = [
        DiscountDeal(
            product_id=product.product_id,
            product_name=product.product_name,
            image=product.image,
            advertised_price=product.advertised_price,
            regular_price=product.regular_price,
        )
        for product in advertised_products
    ]

    top_10_deals = sorted(
        allDeals, key=lambda product: product.difference_amount, reverse=True
    )[:10]

    return top_10_deals


@router.get("/under-50-percent")
async def get_products_under_half_price(db: Session = Depends(get_db)):

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

    allDeals = [
        DiscountDeal(
            product_id=product.product_id,
            product_name=product.product_name,
            image=product.image,
            advertised_price=product.advertised_price,
            regular_price=product.regular_price,
        )
        for product in advertised_products
    ]
    under_half_price_products = list(
        filter(lambda product: product.difference_percent >= 50, allDeals)
    )
    under_half_price_products_sorted = sorted(
        under_half_price_products,
        key=lambda product: product.difference_percent,
        reverse=True,
    )

    return under_half_price_products_sorted
