from sqlalchemy import (
    Column, Integer, String, Float, Date, Time,
    ForeignKey
)
from sqlalchemy.orm import relationship
from database.connection import Base


# -------------------------------------------------------
# MILL MASTER
# -------------------------------------------------------
class Mill(Base):
    __tablename__ = "mill_master"

    id = Column(Integer, primary_key=True, index=True)
    mill_name = Column(String, nullable=False, unique=True)


# -------------------------------------------------------
# DEPARTMENT MASTER (1, 2, 3)
# -------------------------------------------------------
class Department(Base):
    __tablename__ = "department_master"

    id = Column(Integer, primary_key=True, index=True)   # <-- FIXED!
    department_name = Column(String, nullable=False)


# -------------------------------------------------------
# SHIFT MASTER (Shift 1, Shift 2, Shift 3)
# -------------------------------------------------------
class Shift(Base):
    __tablename__ = "shift_master"

    id = Column(Integer, primary_key=True, index=True)
    shift_name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    total_hours = Column(Float, default=8.0)


# -------------------------------------------------------
# COUNT (PRODUCT) MASTER
# -------------------------------------------------------
class CountMaster(Base):
    __tablename__ = "count_master"

    id = Column(Integer, primary_key=True, index=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)
    count_name = Column(String, nullable=False)

    mill = relationship("Mill")


# -------------------------------------------------------
# MACHINE MASTER
# -------------------------------------------------------
class Machine(Base):
    __tablename__ = "machine_master"

    id = Column(Integer, primary_key=True, index=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department_master.id"), nullable=False)

    machine_name = Column(String, nullable=False)
    spindles = Column(Integer)
    allocated_count_id = Column(Integer, ForeignKey("count_master.id"))

    mill = relationship("Mill")
    department = relationship("Department")
    allocated_count = relationship("CountMaster")


# -------------------------------------------------------
# EMPLOYEE MASTER
# -------------------------------------------------------
class Employee(Base):
    __tablename__ = "employee_master"

    id = Column(Integer, primary_key=True, index=True)
    employee_no = Column(String, nullable=False)
    employee_name = Column(String, nullable=False)
    designation = Column(String)

    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    mill = relationship("Mill")


# -------------------------------------------------------
# DAILY PRODUCTION (FINAL STRUCTURE)
# -------------------------------------------------------
class DailyProduction(Base):
    __tablename__ = "daily_production"

    id = Column(Integer, primary_key=True, index=True)

    date = Column(Date, nullable=False)

    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department_master.id"), nullable=False)

    shift_id = Column(Integer, ForeignKey("shift_master.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machine_master.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee_master.id"))
    count_id = Column(Integer, ForeignKey("count_master.id"))

    # Daily Entry Fields
    prod_kgs = Column(Float)
    pne_bondas = Column(Float)
    actual_prdn = Column(Float)
    waste = Column(Float)
    run_hours = Column(Float)
    remarks = Column(String)

    # Future formula fields
    efficiency = Column(Float)
    oee = Column(Float)

    # Relationships
    mill = relationship("Mill")
    department = relationship("Department")
    shift = relationship("Shift")
    machine = relationship("Machine")
    employee = relationship("Employee")
    count = relationship("CountMaster")