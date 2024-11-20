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

    def __repr__(self) -> str:
        return f"Product(id={self.id!r}, name={self.name!r})"
