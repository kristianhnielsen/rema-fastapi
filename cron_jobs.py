from database.operations import add_products
from database.services.rema import fetch


def daily():
    new_products_data = fetch()
    add_products(new_products_data)


if __name__ == "__main__":
    daily()
