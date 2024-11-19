from datetime import datetime
import requests
import json


def get_departments():
    response = requests.get("https://cphapp.rema1000.dk/api/v3/departments")
    response_json = response.json()
    departments = [department for department in response_json["data"]]

    return departments


def get_products(department):
    response = requests.get(
        f"https://cphapp.rema1000.dk/api/v3/departments/{department['id']}/products?per_page=1000000000"
    )
    response_json = response.json()

    # parse product elements from fetched data
    products = []
    for product in response_json["data"]:
        # Add department info
        product["department_name"] = department["name"]
        product["department_id"] = department["id"]

        # Add price found date
        product["logged_on"] = datetime.now().isoformat()

        # Only keep medium-size image
        try:
            img_url = product["images"][0]["medium"]
            product["image"] = img_url
            del product["images"]
        except IndexError:
            product["image"] = None
            del product["images"]

        # Delete labels info
        del product["labels"]
        del product["hazard_precaution_statements"]

        # Convert temperature_zone from string to int
        if product["temperature_zone"] != None:
            temperature_num = int(product["temperature_zone"].split("_")[1])
            product["temperature_zone"] = temperature_num

        products.append(product)

    return products


def fetch(save_as_file=False):
    products = []
    departments = get_departments()
    for department in departments:
        department_products = get_products(department)
        products.extend(department_products)

    if save_as_file:
        with open("data.json", "w") as json_file:
            json.dump(products, json_file)

    return products


if __name__ == "__main__":
    fetch()
