from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Time
from sqlalchemy.orm import relationship
from database.connection import Base


# -----------------------
# MILL MASTER
# -----------------------
class Mill(Base):
    __tablename__ = "mill_master"

    id = Column(Integer, primary_key=True, index=True)
    mill_name = Column(String, nullable=False)


# -----------------------
# DEPARTMENT MASTER
# -----------------------
class Department(Base):
    __tablename__ = "department_master"

    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String, nullable=False)


# -----------------------
# COUNT (PRODUCT) MASTER
# -----------------------
class CountMaster(Base):
    __tablename__ = "count_master"

    id = Column(Integer, primary_key=True, index=True)
    count_name = Column(String, nullable=False)
    actual_count = Column(Float)
    production_factor = Column(Float)


# -----------------------
# EMPLOYEE MASTER
# -----------------------
class Employee(Base):
    __tablename__ = "employee_master"

    id = Column(Integer, primary_key=True, index=True)
    employee_no = Column(String, nullable=False)
    employee_name = Column(String, nullable=False)
    designation = Column(String)

    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    mill = relationship("Mill")


# -----------------------
# MACHINE MASTER
# -----------------------
class Machine(Base):
    __tablename__ = "machine_master"

    id = Column(Integer, primary_key=True, index=True)
    frame_no = Column(String, nullable=False)

    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    mill = relationship("Mill")

    spindles = Column(Integer)
    allocated_count_id = Column(Integer, ForeignKey("count_master.id"))
    allocated_count = relationship("CountMaster")

    speed = Column(Float)
    hank = Column(Float)
    tpi = Column(Float)


# -----------------------
# SHIFT MASTER
# -----------------------
class Shift(Base):
    __tablename__ = "shift_master"

    id = Column(Integer, primary_key=True, index=True)
    shift_name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    total_hours = Column(Float, default=8.0)


# -----------------------
# DAILY PRODUCTION
# -----------------------
class DailyProduction(Base):
    __tablename__ = "daily_production"

    id = Column(Integer, primary_key=True, index=True)

    date = Column(Date, nullable=False)
    shift_id = Column(Integer, ForeignKey("shift_master.id"))
    machine_id = Column(Integer, ForeignKey("machine_master.id"))
    employee_id = Column(Integer, ForeignKey("employee_master.id"))
    count_id = Column(Integer, ForeignKey("count_master.id"))

    shift = relationship("Shift")
    machine = relationship("Machine")
    employee = relationship("Employee")
    count = relationship("CountMaster")

    target = Column(Float)
    actual = Column(Float)
    waste = Column(Float)
    run_hours = Column(Float)

    efficiency = Column(Float)
    oee = Column(Float)

    remarks = Column(String)