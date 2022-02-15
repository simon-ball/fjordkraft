from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from .connection import make_engine

Base = declarative_base()

class Region(Base):
    __tablename__ = "region"
    id = Column(Integer, primary_key=True)
    region_name = Column(String)

class ElectricityPrice(Base):
    __tablename__ = "price"
    id = Column(Integer, primary_key=True)
    region = Column(Integer, ForeignKey("region.id"))
    timestamp = Column(DateTime)
    price = Column(Numeric)


# Create the tables
Base.metadata.create_all(bind=make_engine())

# Insert the lookup table data if not already present
