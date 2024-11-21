from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from database.models import Base
from database.utils import (
    create_price_objects,
    create_product_object,
    remove_duplicates,
)


def process_product_data(product_data, session: Session):
    product_objs = [create_product_object(product) for product in product_data]
    products = remove_duplicates(product_objs, session)

    price_objs = create_price_objects(product_data)
    prices = remove_duplicates(price_objs, session)

    return products, prices


def add_products(data):
    engine: Engine = create_engine("sqlite:///rema.db")
    with Session(engine) as session:
        Base.metadata.create_all(engine)

        products, prices = process_product_data(data, session)

        session.add_all(products)
        session.add_all(prices)
        session.commit()

        print("done")
