from datetime import datetime
from typing import Dict, Optional
import requests
import json

REMA_API_BASE_URL = "https://cphapp.rema1000.dk/api/v3"


def safe_request(url: str) -> Optional[Dict]:
    try:
        response: requests.Response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None


def get_departments():
    response = safe_request(f"{REMA_API_BASE_URL}/departments")
    if response:
        departments = [department for department in response["data"]]
        return departments
    return []


def clean_temperature_zone(temp_zone: Optional[str]) -> Optional[int]:
    if temp_zone:
        try:
            return int(temp_zone.split("_")[1])
        except (ValueError, IndexError):
            return None
    return None


def process_product(product: dict, department: dict):
    # Add department info
    product["department_name"] = department["name"]
    product["department_id"] = department["id"]

    # Add price found date
    product["logged_on"] = datetime.now().isoformat()

    # Only keep medium-size image
    try:
        # Prioritize get medium quality img
        if product["images"][0]["medium"]:
            img_url = product["images"][0]["medium"]
        else:
            # Settle for small img
            img_url = product["images"][0]["small"]
        product["image"] = img_url
        del product["images"]
    except IndexError:
        product["image"] = None
        del product["images"]

    # Delete labels info
    del product["labels"]
    del product["hazard_precaution_statements"]

    # Convert temperature_zone from string to int
    product["temperature_zone"] = clean_temperature_zone(product["temperature_zone"])

    return product


def get_products(department):
    products_url = f"{REMA_API_BASE_URL}/departments/{department['id']}/products?per_page=1000000000"
    response = safe_request(products_url)
    if not response:
        return []

    # parse product elements from fetched data
    products = []
    for product in response["data"]:
        product = process_product(product, department)

        products.append(product)

    return products


def fetch(save_as_file=False):
    print(f"Connecting to Rema's API...")
    products = []
    departments = get_departments()
    for department in departments:
        department_products = get_products(department)
        products.extend(department_products)

    if save_as_file:
        with open(f"data_{datetime.now().date()}.json", "w") as json_file:
            json.dump(products, json_file)

    print(f"Fetched {len(products)} products")
    return products


def fetch_from_file(file_name):
    with open(file_name, "r") as json_file:
        return json.load(json_file)


if __name__ == "__main__":
    fetch(True)
