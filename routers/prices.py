from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import Price
from database.operations import get_db
from routers.utils import validate_date

route_prefix = "/prices"
router = APIRouter(prefix=route_prefix)


class PriceOnDate:
    def __init__(self, price: Price) -> None:
        self.price = price.price
        self.is_advertised = price.is_advertised
        self.is_campaign = price.is_campaign
        self.compare_unit_price = price.compare_unit_price
        self.compare_unit = price.compare_unit


@router.get("/{product_id}")
async def get_product_prices(
    product_id: int,
    start: str | None = None,
    end: str | None = None,
    session: Session = Depends(get_db),
):
    query = select(Price).where(Price.product_id == product_id)
    price_points = session.execute(query).scalars().all()
    price_on_date = {}

    if price_points is None:
        raise HTTPException(status_code=404, detail="No prices found for this product")

    start_date = validate_date(start) if start else datetime(year=2023, month=1, day=1)
    end_date = validate_date(end) if end else datetime.now()

    dates_between_start_and_end = pd.date_range(
        start_date, end_date - timedelta(days=1), freq="d"
    )
    for date in dates_between_start_and_end:
        date_str = date.strftime("%Y-%m-%d")  # returns str YYYY-MM-DD
        price_points_in_range = list(
            filter(
                lambda price: price.starting_at <= date <= price.ending_at,
                price_points,
            )
        )
        if len(price_points_in_range) == 0:
            continue  # no price point found
        elif len(price_points_in_range) == 1:
            price_on_date[date_str] = PriceOnDate(price_points_in_range[0])
        else:
            # there are more than one price point valid  during this date
            # to find the most relevant price point, we look at the price with the shortest interval
            # i.e. the lowest number of days between starting_at and ending_at
            most_relevant_price = min(
                price_points_in_range,
                key=lambda price: (price.ending_at - price.starting_at).days,
            )
            price_on_date[date_str] = PriceOnDate(most_relevant_price)
    return {"product_id": product_id, "price_on_date": price_on_date}
