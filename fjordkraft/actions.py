import json
import requests
import datetime
import sqlalchemy
from decimal import Decimal

from .exceptions import APIInaccessibleException
from .models import ElectricityPrice
from .connection import make_engine

API_URL = r"https://www.fjordkraft.no/Templates/Fjordkraft/webservices/PriceMap.asmx/GetDailyPricesJson?regionPriceMapPageId=1"

engine = make_engine()


def read_api():
    r = requests.get(API_URL)
    if r.status_code == 200:
        text = r.text
        # strip the xml crap out
        text = text.split(">")[2]
        text = text.split("<")[0]
        dictionary = json.loads(text)
        values = dictionary["Areas"]
        # Adjust structure: currently, it returns a price as a string, including a decimal comma and a price
        for d in values:
            string = d["price"]
            d["price"] = Decimal(string.replace(",", ".").split(" ")[0])
            d["unit"] = string.split(" ")[1]
        return values
    else:
        raise APIInaccessibleException("Status code {}".format(r.status_code))

def write_to_database(values):
    timestamp = datetime.datetime.now()
    with engine.connect() as conn:
        for value in values:
            previous_value = conn.execute(sqlalchemy.select(ElectricityPrice))
            statement = sqlalchemy.insert(ElectricityPrice).values(region=value["id"], timestamp=timestamp, price=value["price"])
            result = conn.execute(statement)


if __name__ == "__main__":
    values = read_api()
    print(values)