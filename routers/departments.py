from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from database.models import Price, Product
from database.operations import get_db
from routers.models import DepartmentPriceMetricsResponse, PriceMetricsOnDate


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


@router.get("/metrics")
async def get_price_metrics(db: Session = Depends(get_db)):
    """
    Returns the median price, price range, and price volatility for each department over time.
    """

    # Create query for median price, price range, and price volatility
    query = (
        select(
            Product.department_id,
            Product.department_name,
            func.date(Price.logged_on).label("date"),
            func.avg(Price.price).label("median_price"),
            func.min(Price.price).label("min_price"),
            func.max(Price.price).label("max_price"),
            func.coalesce(func.stddev(Price.price), 0).label("price_volatility"),
        )
        .join(Product, Product.id == Price.product_id)
        .group_by(
            Product.department_id, Product.department_name, func.date(Price.logged_on)
        )
    )

    # Execute the query and group the results
    results = db.execute(query).fetchall()

    # Organize data into a structured format
    departments_metrics = {}

    for row in results:
        department_id = row.department_id
        department_name = row.department_name
        date_str = row.date.strftime("%Y-%m-%d")

        # Create the PriceMetricsOnDate object
        price_metrics = PriceMetricsOnDate(
            median_price=row.median_price,
            min_price=row.min_price,
            max_price=row.max_price,
            price_volatility=row.price_volatility,
        )

        # If the department isn't already in the dictionary, add it
        if department_id not in departments_metrics:
            departments_metrics[department_id] = DepartmentPriceMetricsResponse(
                department_id=department_id,
                department_name=department_name,
                price_on_date={},
            )

        # Add the price metrics to the department's date
        departments_metrics[department_id].price_on_date[date_str] = price_metrics

    # Convert the dictionary to a list of responses sorted by department_id
    department_metrics_sorted = sorted(
        departments_metrics.values(), key=lambda dept: dept.department_id
    )
    return department_metrics_sorted


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
