from database.operations import add_products
from database.services.rema import fetch

new_products_data = fetch()
add_products(new_products_data)