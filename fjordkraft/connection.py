import urllib.parse
from sqlalchemy import create_engine


from .settings import config


def make_url():
    url = "{dialect}://{username}:{password}@{host}:{port}/{database}".format(
        dialect=config["database.dialect"],
        username=config["database.user"],
        password=config["database.password"],
        host=config["database.host"],
        port=config["database.port"],
        database=config["database.database"],
    )
    return url

def make_engine():
    return create_engine(make_url())

