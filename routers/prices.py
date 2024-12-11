from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import Price
from database.operations import get_db
from routers.utils import validate_date
from typing import Dict, Optional

route_prefix = "/prices"
router = APIRouter(prefix=route_prefix)


class PriceOnDate(BaseModel):
    price: float
    is_advertised: bool
    is_campaign: bool
    compare_unit_price: Optional[float]
    compare_unit: Optional[str]


class ProductPricesResponse(BaseModel):
    product_id: int
    price_on_date: Dict[str, PriceOnDate]

    @property
    def avg_price(self) -> float:
        """Calculate the average price."""
        if not self.price_on_date:
            return 0.0  # Return 0 if there are no prices
        total_price = sum(
            price_data.price for price_data in self.price_on_date.values()
        )
        return total_price / len(self.price_on_date)

    @property
    def current_price(self) -> Optional[PriceOnDate]:
        """Find the current/most recent price."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        if today_str in self.price_on_date:
            return self.price_on_date[today_str]

        # If today’s price is not available, find the most recent past date
        dates = sorted(self.price_on_date.keys(), reverse=True)
        for date_str in dates:
            if datetime.strptime(date_str, "%Y-%m-%d") <= datetime.now():
                return self.price_on_date[date_str]
        return None  # No valid current/recent price

    @property
    def lowest_price(self) -> Optional[PriceOnDate]:
        """Find the lowest price."""
        if not self.price_on_date:
            return None
        return min(self.price_on_date.values(), key=lambda price: price.price)


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
            price_on_date[date_str] = PriceOnDate(
                price=price_points_in_range[0].price,
                is_advertised=price_points_in_range[0].is_advertised,
                is_campaign=price_points_in_range[0].is_campaign,
                compare_unit_price=price_points_in_range[0].compare_unit_price,
                compare_unit=price_points_in_range[0].compare_unit,
            )
        else:
            # there are more than one price point valid  during this date
            # to find the most relevant price point, we look at the price with the shortest interval
            # i.e. the lowest number of days between starting_at and ending_at
            most_relevant_price = min(
                price_points_in_range,
                key=lambda price: (price.ending_at - price.starting_at).days,
            )
            price_on_date[date_str] = PriceOnDate(
                price=most_relevant_price.price,
                is_advertised=most_relevant_price.is_advertised,
                is_campaign=most_relevant_price.is_campaign,
                compare_unit_price=most_relevant_price.compare_unit_price,
                compare_unit=most_relevant_price.compare_unit,
            )

    return ProductPricesResponse(product_id=product_id, price_on_date=price_on_date)
