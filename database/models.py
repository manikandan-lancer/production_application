from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Time
from sqlalchemy.orm import relationship
from database.connection import Base

class Mill(Base):
    __tablename__ = "mill_master"
    id = Column(Integer, primary_key=True)
    mill_name = Column(String, nullable=False, unique=True)
    machines = relationship("Machine", back_populates="mill")
    counts = relationship("CountMaster", back_populates="mill")

class Department(Base):
    __tablename__ = "department_master"
    id = Column(Integer, primary_key=True)
    department_name = Column(String, nullable=False)
    machines = relationship("Machine", back_populates="department")

class Shift(Base):
    __tablename__ = "shift_master"
    id = Column(Integer, primary_key=True)
    shift_name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    total_hours = Column(Numeric(10, 2))

class CountMaster(Base):
    __tablename__ = "count_master"

    id = Column(Integer, primary_key=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)

    count_name = Column(String, nullable=False)

    actual_count = Column(Numeric(10, 4))
    spinning_count_eff = Column(Numeric(10, 2))
    std_hank_eff = Column(Numeric(10, 2))

    conversion_factor = Column(Numeric(10, 6))

    mill = relationship("Mill", back_populates="counts")
    machines = relationship("Machine", back_populates="allocated_count")


class Machine(Base):
    __tablename__ = "machine_master"
    id = Column(Integer, primary_key=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department_master.id"), nullable=False)
    machine_name = Column(String, nullable=False)
    spindles = Column(Integer)
    spdl_speed = Column(Numeric(10, 2))
    tpi = Column(Numeric(10, 2))
    allocated_count_id = Column(Integer, ForeignKey("count_master.id"))
    std_hank = Column(Numeric(10, 6))
    mill = relationship("Mill", back_populates="machines")
    department = relationship("Department", back_populates="machines")
    allocated_count = relationship("CountMaster", back_populates="machines")
    productions = relationship("DailyProduction", back_populates="machine")

class Employee(Base):
    __tablename__ = "employee_master"
    id = Column(Integer, primary_key=True)
    employee_no = Column(String, nullable=False)
    employee_name = Column(String, nullable=False)
    productions = relationship("DailyProduction", back_populates="employee")

class DailyProduction(Base):
    __tablename__ = "daily_production"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    mill_id = Column(Integer)
    department_id = Column(Integer)
    shift_id = Column(Integer)
    machine_id = Column(Integer)
    count_id = Column(Integer, ForeignKey("count_master.id"))
    count = relationship("CountMaster")
    employee_id = Column(Integer, nullable=True)

    spindles = Column(Integer)
    spdl_speed = Column(Numeric(10, 2))
    tpi = Column(Numeric(10, 2))
    std_hank = Column(Numeric(10, 4))
    conversion_factor = Column(Numeric(10, 6))

    act_hank = Column(Numeric(10, 2))
    stop_min = Column(Numeric(10, 2))
    prod_kgs = Column(Numeric(10, 2))
    pne_bondas = Column(Numeric(10, 2))

    worked_spindles = Column(Numeric(10, 2))
    target_kgs = Column(Numeric(10, 2))
    actual_prdn = Column(Numeric(10, 2))
    waste_percent = Column(Numeric(10, 2))

    remarks = Column(String)
