from datetime import datetime
from typing import Dict
from database.models import Price


class PriceOnDate:
    def __init__(self, price: Price) -> None:
        self.price = price.price
        self.is_advertised = price.is_advertised
        self.is_campaign = price.is_campaign
        self.compare_unit_price = price.compare_unit_price
        self.compare_unit = price.compare_unit


class ProductPricesResponse:
    def __init__(self, product_id: int, price_on_date: Dict[str, PriceOnDate]) -> None:
        self.product_id = product_id
        self.price_on_date = price_on_date
        self.avg_price = self.get_avg_price()
        self.current_price = self.get_current_price()
        self.lowest_price = self.get_lowest_price()

    def get_avg_price(self) -> float:
        """Calculate the average price."""
        if not self.price_on_date:
            return 0.0  # Return 0 if there are no prices
        total_price = sum(
            price_data.price for price_data in self.price_on_date.values()
        )
        return round(total_price / len(self.price_on_date), 2)

    def get_lowest_price(self):
        """Find the lowest price."""
        if not self.price_on_date:
            return None
        return min(self.price_on_date.values(), key=lambda price: price.price).price

    def get_current_price(self):
        """Find the current/most recent price."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        if today_str in self.price_on_date:
            return self.price_on_date[today_str].price

        # If today’s price is not available, find the most recent past date
        dates = sorted(self.price_on_date.keys(), reverse=True)
        for date_str in dates:
            if datetime.strptime(date_str, "%Y-%m-%d") <= datetime.now():
                return self.price_on_date[date_str].price
