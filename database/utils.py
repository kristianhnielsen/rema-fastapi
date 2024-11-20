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
    return Product(
        id=product_data["id"],
        name=product_data["name"],
        underline=product_data["underline"],
        age_limit=product_data["age_limit"],
        description=product_data["description"],
        info=product_data["info"],
        image=product_data["image"],
        temperature_zone=product_data["temperature_zone"],
        is_self_scale_item=product_data["is_self_scale_item"],
        is_weight_item=product_data["is_weight_item"],
        is_available_in_all_stores=product_data["is_available_in_all_stores"],
        is_batch_item=product_data["is_batch_item"],
        department_name=product_data["department_name"],
        department_id=product_data["department_id"],
        updated=datetime.fromisoformat(product_data["logged_on"]),
    )


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
    return Price(
        price=price_data["price"],
        price_over_max_quantity=price_data["price_over_max_quantity"],
        max_quantity=price_data["max_quantity"],
        is_advertised=price_data["is_advertised"],
        is_campaign=price_data["is_campaign"],
        starting_at=datetime.fromisoformat(price_data["starting_at"]),
        ending_at=datetime.fromisoformat(price_data["ending_at"]),
        deposit=price_data["deposit"],
        compare_unit=price_data["compare_unit"],
        compare_unit_price=price_data["compare_unit_price"],
        consumption_unit=price_data["consumption_unit"],
        consumption_quantity=price_data["consumption_quantity"],
        logged_on=datetime.fromisoformat(product_data["logged_on"]),
        product_id=product_data["id"],
    )
