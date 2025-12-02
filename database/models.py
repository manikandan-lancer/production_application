from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base


class Mill(Base):
    __tablename__ = "mill_master"

    id = Column(Integer, primary_key=True, index=True)
    mill_name = Column(String, nullable=False)


class Department(Base):
    __tablename__ = "department_master"

    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String, nullable=False)


class Employee(Base):
    __tablename__ = "employee_master"

    id = Column(Integer, primary_key=True, index=True)
    employee_no = Column(String, nullable=False)
    employee_name = Column(String, nullable=False)

    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    department_id = Column(Integer, ForeignKey("department_master.id"))

    mill = relationship("Mill")
    department = relationship("Department")


class Machine(Base):
    __tablename__ = "machine_master"

    id = Column(Integer, primary_key=True, index=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    department_id = Column(Integer, ForeignKey("department_master.id"))

    frame_number = Column(String)
    product = Column(String)
    speed = Column(Float)
    tpi = Column(Float)
    std_hank = Column(Float)
    cycle_time = Column(Float)
    target = Column(Integer)

    mill = relationship("Mill")
    department = relationship("Department")


class Shift(Base):
    __tablename__ = "shift_master"

    id = Column(Integer, primary_key=True, index=True)
    shift_name = Column(String)
    start_time = Column(String)
    end_time = Column(String)


class DailyProduction(Base):
    __tablename__ = "daily_production"

    id = Column(Integer, primary_key=True, index=True)

    date = Column(Date)
    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    department_id = Column(Integer, ForeignKey("department_master.id"))
    shift_id = Column(Integer, ForeignKey("shift_master.id"))
    machine_id = Column(Integer, ForeignKey("machine_master.id"))
    employee_id = Column(Integer, ForeignKey("employee_master.id"))

    actual = Column(Float)
    waste = Column(Float)
    run_hr = Column(Float)
    prod = Column(Float)
    target = Column(Integer)
    ts = Column(String)
    count = Column(String)
    remarks = Column(String)

    # NEW (You confirmed these columns exist)
    scrap = Column(Float, nullable=True)
    downtime = Column(Float, nullable=True)
    efficiency = Column(Float, nullable=True)
    oee = Column(Float, nullable=True)

    mill = relationship("Mill")
    department = relationship("Department")
    shift = relationship("Shift")
    machine = relationship("Machine")
    employee = relationship("Employee")