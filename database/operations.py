from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Product
from database.utils import (
    create_price_objects,
    remove_duplicates,
)

engine: Engine = create_engine("sqlite:///rema.db")
db_session: sessionmaker = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def get_db():
    database = db_session()
    try:
        yield database
    finally:
        database.close()


def process_product_data(product_data, session):
    product_objs = [Product(product) for product in product_data]
    products = remove_duplicates(product_objs, session)

    price_objs = create_price_objects(product_data)
    prices = remove_duplicates(price_objs, session)

    return products, prices


def add_products(data):
    with db_session() as session:
        products, prices = process_product_data(data, session)

        print(f"New products found: {len(products)}")
        print(f"New prices found: {len(prices)}")
        session.add_all(products)
        session.add_all(prices)
        session.commit()

        print("done")
