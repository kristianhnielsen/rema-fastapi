from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload
from database.models import Price, Product
from database.operations import get_db

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
    department_deals = []
    for dept in department_prices:
        department = {
            "avg_price": round(dept.avg_price, 2),
            "min_price": dept.min_price,
            "max_price": dept.max_price,
            "department_name": dept.department_name,
            "department_id": dept.department_id,
            "best_deals": [],
        }
        department_deals.append(department)

    for row in advertised_products:
        regular_price = (
            row.regular_price if row.regular_price is not None else row.advertised_price
        )
        advertised_price = row.advertised_price

        if regular_price and advertised_price:
            difference_amount = regular_price - advertised_price
            difference_percent = (
                (regular_price - advertised_price) / regular_price
            ) * 100

            deal = {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "advertised_price": advertised_price,
                "regular_price": regular_price,
                "difference_amount": round(difference_amount, 2),
                "difference_percent": round(difference_percent, 2),
            }

            # Add the deal to the respective department
            for department in department_deals:
                if row.department_id == department["department_id"]:
                    department["best_deals"].append(deal)

    for department in department_deals:
        products = department["best_deals"]
        if len(products) == 0:
            continue
        products_diff_amount = sum(
            [product["difference_amount"] for product in products]
        ) / len(products)
        products_diff_percent = sum(
            [product["difference_percent"] for product in products]
        ) / len(products)
        department["avg_difference_amount"] = round(products_diff_amount, 2)
        department["avg_difference_percent"] = round(products_diff_percent, 2)

    # Sort deals on price difference in percent
    for department in department_deals:
        department["best_deals"] = sorted(
            department["best_deals"],
            key=lambda x: x["difference_percent"],
            reverse=True,
        )

    return sorted(department_deals, key=lambda dept: dept["department_id"])
