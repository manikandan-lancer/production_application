from sqlalchemy import (
    Column, Integer, String, Date, Time, ForeignKey, Numeric
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
# DEPARTMENT MASTER
# -------------------------------------------------------
class Department(Base):
    __tablename__ = "department_master"

    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String, nullable=False)


# -------------------------------------------------------
# SHIFT MASTER
# -------------------------------------------------------
class Shift(Base):
    __tablename__ = "shift_master"

    id = Column(Integer, primary_key=True, index=True)
    shift_name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    total_hours = Column(Numeric(10, 2), default=8.00)


# -------------------------------------------------------
# COUNT (PRODUCT) MASTER
# -------------------------------------------------------
class CountMaster(Base):
    __tablename__ = "count_master"

    id = Column(Integer, primary_key=True, index=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)
    count_name = Column(String, nullable=False)

    # NEW FIELDS
    actual_count = Column(Numeric(10, 2), default=0)
    conversion_factor = Column(Numeric(10, 4), default=0)
    efficiency_base = Column(Numeric(10, 2), default=0)

    mill = relationship("Mill")


# -------------------------------------------------------
# MACHINE MASTER (CONTAINS CONSTANTS)
# -------------------------------------------------------
class Machine(Base):
    __tablename__ = "machine_master"

    id = Column(Integer, primary_key=True, index=True)

    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department_master.id"), nullable=False)

    machine_name = Column(String, nullable=False)
    spindles = Column(Integer)  # manually entered by user

    # CONSTANT MACHINE VALUES
    spdl_speed = Column(Numeric(10, 2))   # constant per machine
    tpi = Column(Numeric(10, 2))          # constant per machine

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
# DAILY PRODUCTION ENTRY
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

    worked_spindles = Column(Numeric(10, 2))
    spdl_speed = Column(Numeric(10, 2))  # snapshotted from MachineMaster
    tpi = Column(Numeric(10, 2))         # snapshotted from MachineMaster

    std_hank = Column(Numeric(10, 2))
    act_hank = Column(Numeric(10, 2))
    stop_min = Column(Numeric(10, 2))
    target_kgs = Column(Numeric(10, 2))

    prod_kgs = Column(Numeric(10, 2))
    pne_bondas = Column(Numeric(10, 2))
    actual_prdn = Column(Numeric(10, 2))
    waste = Column(Numeric(10, 2))
    run_hours = Column(Numeric(10, 2))

    remarks = Column(String)

    efficiency = Column(Numeric(10, 2))
    oee = Column(Numeric(10, 2))

    mill = relationship("Mill")
    department = relationship("Department")
    shift = relationship("Shift")
    machine = relationship("Machine")
    employee = relationship("Employee")
    count = relationship("CountMaster")