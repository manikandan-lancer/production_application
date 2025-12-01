from sqlalchemy import Column, Integer, String, Float, Date, Time, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ---------------------------
# MILL MASTER
# ---------------------------
class Mill(Base):
    __tablename__ = "mill_master"

    id = Column(Integer, primary_key=True)
    mill_name = Column(String)

    machines = relationship("Machine", back_populates="mill")


# ---------------------------
# DEPARTMENT MASTER
# ---------------------------
class Department(Base):
    __tablename__ = "department_master"

    id = Column(Integer, primary_key=True)
    department_name = Column(String)

    machines = relationship("Machine", back_populates="department")
    employees = relationship("Employee", back_populates="department")


# ---------------------------
# EMPLOYEE MASTER
# ---------------------------
class Employee(Base):
    __tablename__ = "employee_master"

    id = Column(Integer, primary_key=True)
    employee_no = Column(String)
    employee_name = Column(String)

    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    department_id = Column(Integer, ForeignKey("department_master.id"))

    mill = relationship("Mill")
    department = relationship("Department", back_populates="employees")

    production = relationship("DailyProduction", back_populates="employee")


# ---------------------------
# MACHINE MASTER
# ---------------------------
class Machine(Base):
    __tablename__ = "machine_master"

    id = Column(Integer, primary_key=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"))
    department_id = Column(Integer, ForeignKey("department_master.id"))

    frame_number = Column(String)
    product = Column(String)
    speed = Column(Float)
    tpi = Column(Float)
    std_hank = Column(Float)

    cycle_time = Column(Float)
    target = Column(Integer)

    mill = relationship("Mill", back_populates="machines")
    department = relationship("Department", back_populates="machines")

    production = relationship("DailyProduction", back_populates="machine")


# ---------------------------
# SHIFT MASTER
# ---------------------------
class Shift(Base):
    __tablename__ = "shift_master"

    id = Column(Integer, primary_key=True)
    shift_name = Column(String)  # A, B, C
    start_time = Column(Time)
    end_time = Column(Time)

    production = relationship("DailyProduction", back_populates="shift")


# ---------------------------
# DAILY PRODUCTION TABLE
# ---------------------------
class DailyProduction(Base):
    __tablename__ = "daily_production"

    id = Column(Integer, primary_key=True)

    date = Column(Date)
    mill_id = Column(Integer)
    department_id = Column(Integer)

    shift_id = Column(Integer, ForeignKey("shift_master.id"))
    machine_id = Column(Integer, ForeignKey("machine_master.id"))
    employee_id = Column(Integer, ForeignKey("employee_master.id"))

    actual = Column(Float)
    waste = Column(Float)
    run_hr = Column(Float)
    prod = Column(Float)
    ts = Column(String)
    count = Column(String)
    remarks = Column(String)
    target = Column(Float)

    shift = relationship("Shift", back_populates="production")
    machine = relationship("Machine", back_populates="production")
    employee = relationship("Employee", back_populates="production")