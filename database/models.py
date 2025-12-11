from sqlalchemy import Column, Integer, String, Date, Time, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base


# ----------------------------------------------------------
# MILL MASTER
# ----------------------------------------------------------
class Mill(Base):
    __tablename__ = "mill_master"
    id = Column(Integer, primary_key=True)
    mill_name = Column(String, nullable=False, unique=True)


# ----------------------------------------------------------
# DEPARTMENT MASTER
# ----------------------------------------------------------
class Department(Base):
    __tablename__ = "department_master"
    id = Column(Integer, primary_key=True)
    department_name = Column(String, nullable=False)


# ----------------------------------------------------------
# SHIFT MASTER
# ----------------------------------------------------------
class Shift(Base):
    __tablename__ = "shift_master"
    id = Column(Integer, primary_key=True)
    shift_name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    total_hours = Column(Numeric(10, 2), default=8.0)


# ----------------------------------------------------------
# COUNT MASTER  (Updated per your redesign)
# ----------------------------------------------------------
class CountMaster(Base):
    __tablename__ = "count_master"

    id = Column(Integer, primary_key=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)

    count_name = Column(String, nullable=False)

    # NEW FIELDS
    actual_count = Column(Numeric(10, 4))
    spinning_count_eff = Column(Numeric(10, 2))   # renamed from efficiency_base
    std_hank_eff = Column(Numeric(10, 2))         # moved from machine master
    conversion_factor = Column(Numeric(10, 6))

    mill = relationship("Mill", back_populates="counts")


# ----------------------------------------------------------
# MACHINE MASTER (constants only)
# ----------------------------------------------------------
class Machine(Base):
    __tablename__ = "machine_master"

    id = Column(Integer, primary_key=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department_master.id"), nullable=False)

    machine_name = Column(String, nullable=False)
    spindles = Column(Integer)

    allocated_count_id = Column(Integer, ForeignKey("count_master.id"))

    spdl_speed = Column(Numeric(10, 2))
    tpi = Column(Numeric(10, 2))

    mill = relationship("Mill")
    department = relationship("Department")
    allocated_count = relationship("CountMaster")


# ----------------------------------------------------------
# EMPLOYEE MASTER
# ----------------------------------------------------------
class Employee(Base):
    __tablename__ = "employee_master"

    id = Column(Integer, primary_key=True)
    employee_no = Column(String, nullable=False)
    employee_name = Column(String, nullable=False)


# ----------------------------------------------------------
# DAILY PRODUCTION (complete structure)
# ----------------------------------------------------------
class DailyProduction(Base):
    __tablename__ = "daily_production"

    id = Column(Integer, primary_key=True)

    date = Column(Date, nullable=False)
    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    department_id = Column(Integer, ForeignKey("department_master.id"))
    shift_id = Column(Integer, ForeignKey("shift_master.id"))
    machine_id = Column(Integer, ForeignKey("machine_master.id"))
    employee_id = Column(Integer, ForeignKey("employee_master.id"))
    count_id = Column(Integer, ForeignKey("count_master.id"))

    # Machine constants at entry time
    spindles = Column(Integer)
    spdl_speed = Column(Numeric(10, 2))
    tpi = Column(Numeric(10, 2))
    std_hank = Column(Numeric(10, 6))
    conversion_factor = Column(Numeric(10, 6))

    # Entry fields
    act_hank = Column(Numeric(10, 2))
    stop_min = Column(Numeric(10, 2))
    run_hours = Column(Numeric(10, 2))

    prod_kgs = Column(Numeric(10, 2))
    pne_bondas = Column(Numeric(10, 2))
    waste = Column(Numeric(10, 2))

    # Calculated
    worked_spindles = Column(Numeric(10, 2))
    target_kgs = Column(Numeric(10, 2))
    actual_prdn = Column(Numeric(10, 2))
    waste_percent = Column(Numeric(10, 2))
    efficiency = Column(Numeric(10, 2))
    oee = Column(Numeric(10, 2))

    remarks = Column(String)

    machine = relationship("Machine")
    count = relationship("CountMaster")
    employee = relationship("Employee")
    shift = relationship("Shift")
