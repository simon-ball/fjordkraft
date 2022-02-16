import json
import requests
import datetime
import sqlalchemy
from decimal import Decimal

from .exceptions import APIInaccessibleException
from .models import ElectricityPrice
from .connection import make_engine
from .settings import tfmt

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
        # Adjust structure: currently, it returns a price as a string, including a decimal comma and a unit
        for d in values:
            string = d["price"]
            d["price"] = Decimal(string.replace(",", ".").split(" ")[0])
            d["unit"] = string.split(" ")[1]
        return values
    else:
        raise APIInaccessibleException("Status code {}".format(r.status_code))

def write_to_database(values=None):
    if values is None:
        values = read_api()
    timestamp = datetime.datetime.now()
    with sqlalchemy.orm.Session(engine) as session:
        for value in values:
            previous_value = (
                session.query(ElectricityPrice)
                    .filter_by(region=value["id"])
                    .order_by(ElectricityPrice.timestamp.desc())
                    .first()
            )
            if previous_value is None or not value["price"] == previous_value.price:
                # If the previous value is missing (i.e. empty database)
                # Or if the new value is different from the previous value
                # Then insert new data
                print("Value for region {} changed".format(value["id"]))
                statement = sqlalchemy.insert(ElectricityPrice).values(region=value["id"], timestamp=timestamp, price=value["price"])
                session.execute(statement)
            else:
                # The value has not changed, so don't insert new data
                print("Value for region {} identical".format(value["id"]))
        session.commit()
        # Is the commit actually necessary? Shouldn't the context manager take care of that?

def visualise(period=28):
    then = datetime.datetime.now() - datetime.timedelta(days=period)

    with sqlalchemy.orm.Session(make_engine()) as session:
        values = (
            session
                .query(ElectricityPrice)
                .filter_by(region=3)
                .filter(ElectricityPrice.timestamp >= then)
                .order_by(ElectricityPrice.timestamp.desc())
                .all()
        )
    times = [v.timestamp.strftime(tfmt) for v in values]
    prices = [v.price for v in values]
    return times, prices

