from datetime import datetime
from sqlalchemy import ForeignKey
from typing import List, Optional
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    price: Mapped[float]
    logged_on: Mapped[datetime]
    price_over_max_quantity: Mapped[Optional[float]]
    max_quantity: Mapped[Optional[int]]
    is_advertised: Mapped[bool]
    is_campaign: Mapped[bool]
    starting_at: Mapped[datetime]
    ending_at: Mapped[datetime]
    deposit: Mapped[Optional[float]]
    compare_unit: Mapped[str]
    compare_unit_price: Mapped[float]
    consumption_unit: Mapped[Optional[str]]
    consumption_quantity: Mapped[Optional[int]]

    # Relationship to Product
    product: Mapped["Product"] = relationship(back_populates="prices")

    def __init__(self, price_data, product_data):
        super().__init__()
        self.price = price_data["price"]
        self.price_over_max_quantity = price_data["price_over_max_quantity"]
        self.max_quantity = price_data["max_quantity"]
        self.is_advertised = price_data["is_advertised"]
        self.is_campaign = price_data["is_campaign"]
        self.starting_at = datetime.fromisoformat(price_data["starting_at"])
        self.ending_at = datetime.fromisoformat(price_data["ending_at"])
        self.deposit = price_data["deposit"]
        self.compare_unit = price_data["compare_unit"]
        self.compare_unit_price = price_data["compare_unit_price"]
        self.consumption_unit = price_data["consumption_unit"]
        self.consumption_quantity = price_data["consumption_quantity"]
        self.logged_on = datetime.fromisoformat(product_data["logged_on"])
        self.product_id = product_data["id"]

    def __repr__(self) -> str:
        return f"Price(id={self.id!r}, price={self.price!r})"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    updated: Mapped[datetime]
    underline: Mapped[str]
    age_limit: Mapped[Optional[int]]
    description: Mapped[Optional[str]]
    info: Mapped[str]
    image: Mapped[Optional[str]]
    temperature_zone: Mapped[Optional[int]]
    is_self_scale_item: Mapped[bool]
    is_weight_item: Mapped[bool]
    is_available_in_all_stores: Mapped[bool]
    is_batch_item: Mapped[bool]
    department_name: Mapped[str]
    department_id: Mapped[int]

    # Relationship to Price
    prices: Mapped[List["Price"]] = relationship(back_populates="product", uselist=True)

    def __init__(self, data):
        super().__init__()
        self.id = data["id"]
        self.name = data["name"]
        self.underline = data["underline"]
        self.age_limit = data["age_limit"]
        self.description = data["description"]
        self.info = data["info"]
        self.image = data["image"]
        self.temperature_zone = data["temperature_zone"]
        self.is_self_scale_item = data["is_self_scale_item"]
        self.is_weight_item = data["is_weight_item"]
        self.is_available_in_all_stores = data["is_available_in_all_stores"]
        self.is_batch_item = data["is_batch_item"]
        self.department_name = data["department_name"]
        self.department_id = data["department_id"]
        self.updated = datetime.fromisoformat(data["logged_on"])

    def __repr__(self) -> str:
        return f"Product(id={self.id!r}, name={self.name!r})"
