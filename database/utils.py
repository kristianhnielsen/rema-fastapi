from datetime import datetime
from typing import List
from sqlalchemy import select
from .models import Price, Product
from sqlalchemy.orm import Session


def remove_duplicates(
    objects: List[Price] | List[Product], session: Session
) -> List[Product | Price | None]:
    filtered_objects = []
    for element in objects:
        duplicate_element = is_duplicate(element, session=session)
        if not duplicate_element:
            filtered_objects.append(element)

    return filtered_objects


def is_duplicate(obj: Price | Product, session: Session):
    if type(obj) is Price:
        statement = select(Price).where(
            Price.price == obj.price,
            Price.starting_at == obj.starting_at,
            Price.ending_at == obj.ending_at,
            Price.product_id == obj.product_id,
        )
    elif type(obj) is Product:
        statement = select(Product).where(Product.id == obj.id)
    else:
        return

    existing_obj: Price | Product | None = session.scalars(statement=statement).first()
    return existing_obj


def create_product_object(product_data):
    n = product_data["name"].lower()
    if "marsh" in n:
        print()
    return Product(data=product_data)


def create_price_objects(product_data) -> list[Price]:
    prices: list[Price] = []

    for product in product_data:
        for price_data in product["prices"]:
            price: Price = create_price_object(
                price_data=price_data, product_data=product
            )
            prices.append(price)

    return prices


def create_price_object(price_data, product_data) -> Price:
    return Price(price_data, product_data)
