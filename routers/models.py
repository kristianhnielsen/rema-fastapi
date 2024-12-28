from datetime import datetime
from typing import Dict, List
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


class DiscountDepartment:
    def __init__(
        self,
        avg_price,
        min_price,
        max_price,
        department_name,
        department_id,
    ) -> None:

        self.avg_price = round(avg_price, 2)
        self.min_price = round(min_price, 2)
        self.max_price = round(max_price, 2)
        self.avg_difference_amount: float
        self.avg_difference_percent: float
        self.department_name = department_name
        self.department_id = department_id
        self.deals: List[DiscountDeal] = []

    def calc_avg_diff_amount(self):
        if len(self.deals) == 0:
            return 0

        products_diff_amount = sum(
            [product.difference_amount for product in self.deals]
        ) / len(self.deals)
        self.avg_difference_amount = round(products_diff_amount, 2)

    def calc_avg_diff_percent(self):
        if len(self.deals) == 0:
            return 0

        products_diff_percent = sum(
            [product.difference_percent for product in self.deals]
        ) / len(self.deals)
        self.avg_difference_percent = round(products_diff_percent, 2)

    def sort_deals_by_discount_percent(self):
        self.deals = sorted(
            self.deals,
            key=lambda deal: deal.difference_percent,
            reverse=True,
        )


class DiscountDeal:
    def __init__(
        self,
        product_id,
        product_name,
        image,
        advertised_price,
        regular_price,
    ) -> None:
        self.product_id = product_id
        self.product_name = product_name
        self.image = image
        self.advertised_price = advertised_price
        self.regular_price = (
            regular_price if regular_price is not None else advertised_price
        )
        self.difference_amount = self.calc_difference_amount()
        self.difference_percent = self.calc_difference_percent()

    def calc_difference_amount(self, rounded=True):
        difference = self.regular_price - self.advertised_price
        if rounded:
            return round(difference, 2)
        return difference

    def calc_difference_percent(self):
        difference_percent = (
            self.calc_difference_amount(rounded=False) / self.regular_price
        ) * 100
        return round(difference_percent, 2)
