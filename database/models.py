from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date, Time, ForeignKey

Base = declarative_base()

class Machine(Base):
    __tablename__ = "machine_master"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    product_id = Column(Integer)
    cycle_time = Column(Float)
    target = Column(Integer)

class Shift(Base):
    __tablename__ = "shift_master"
    id = Column(Integer, primary_key=True)
    shift_name = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)

class DailyProduction(Base):
    __tablename__ = "daily_production"
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    shift_id = Column(Integer, ForeignKey("shift_master.id"))
    machine_id = Column(Integer, ForeignKey("machine_master.id"))
    actual = Column(Integer)
    scrap = Column(Integer)
    downtime = Column(Integer)
    efficiency = Column(Float)
    oee = Column(Float)