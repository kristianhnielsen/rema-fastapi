from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from database.models import Base, Product
from database.utils import (
    create_price_objects,
    remove_duplicates,
)


class Database:
    def __init__(self) -> None:
        self.engine: Engine = create_engine("sqlite:///rema.db")
        self.session: Session = Session(bind=self.engine)
        Base.metadata.create_all(self.engine)


def process_product_data(product_data, session: Session):
    product_objs = [Product(product) for product in product_data]
    products = remove_duplicates(product_objs, session)

    price_objs = create_price_objects(product_data)
    prices = remove_duplicates(price_objs, session)

    return products, prices


def add_products(data):
    db = Database()

    with db.session as session:
        products, prices = process_product_data(data, session)

        print(f"New products found: {len(products)}")
        print(f"New prices found: {len(prices)}")
        session.add_all(products)
        session.add_all(prices)
        session.commit()

        print("done")
