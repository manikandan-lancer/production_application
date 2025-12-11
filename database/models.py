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

    # Reverse relationships
    counts = relationship("CountMaster", back_populates="mill")
    machines = relationship("Machine", back_populates="mill")
    employees = relationship("Employee", back_populates="mill")
    productions = relationship("DailyProduction", back_populates="mill")


# ----------------------------------------------------------
# DEPARTMENT MASTER
# ----------------------------------------------------------
class Department(Base):
    __tablename__ = "department_master"

    id = Column(Integer, primary_key=True)
    department_name = Column(String, nullable=False)

    machines = relationship("Machine", back_populates="department")
    productions = relationship("DailyProduction", back_populates="department")


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

    productions = relationship("DailyProduction", back_populates="shift")


# ----------------------------------------------------------
# COUNT MASTER
# ----------------------------------------------------------
class CountMaster(Base):
    __tablename__ = "count_master"

    id = Column(Integer, primary_key=True)
    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)

    count_name = Column(String, nullable=False)

    # Updated fields
    actual_count = Column(Numeric(10, 4))
    spinning_count_eff = Column(Numeric(10, 2))   # count-based efficiency
    std_hank_eff = Column(Numeric(10, 2))         # used for STD Hank
    conversion_factor = Column(Numeric(10, 2))

    mill = relationship("Mill", back_populates="counts")
    machines = relationship("Machine", back_populates="allocated_count")
    productions = relationship("DailyProduction", back_populates="count")


# ----------------------------------------------------------
# MACHINE MASTER  (constants only)
# ----------------------------------------------------------
class Machine(Base):
    __tablename__ = "machine_master"

    id = Column(Integer, primary_key=True)

    mill_id = Column(Integer, ForeignKey("mill_master.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department_master.id"), nullable=False)
    allocated_count_id = Column(Integer, ForeignKey("count_master.id"))

    machine_name = Column(String, nullable=False)
    spindles = Column(Integer)

    spdl_speed = Column(Numeric(10, 2))
    tpi = Column(Numeric(10, 2))

    # REQUIRED FIELD (you missed this earlier)
    std_hank = Column(Numeric(10, 2))

    # Relationships
    mill = relationship("Mill", back_populates="machines")
    department = relationship("Department", back_populates="machines")
    allocated_count = relationship("CountMaster", back_populates="machines")
    productions = relationship("DailyProduction", back_populates="machine")


# ----------------------------------------------------------
# EMPLOYEE MASTER
# ----------------------------------------------------------
class Employee(Base):
    __tablename__ = "employee_master"

    id = Column(Integer, primary_key=True)

    employee_no = Column(String, nullable=False)
    employee_name = Column(String, nullable=False)

    mill_id = Column(Integer, ForeignKey("mill_master.id"))

    mill = relationship("Mill", back_populates="employees")
    productions = relationship("DailyProduction", back_populates="employee")


# ----------------------------------------------------------
# DAILY PRODUCTION
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

    # Machine constants copied at entry time
    spindles = Column(Integer)
    spdl_speed = Column(Numeric(10, 2))
    tpi = Column(Numeric(10, 2))
    std_hank = Column(Numeric(10, 6))
    conversion_factor = Column(Numeric(10, 6))

    # User entry fields
    act_hank = Column(Numeric(10, 2))
    stop_min = Column(Numeric(10, 2))
    run_hours = Column(Numeric(10, 2))

    prod_kgs = Column(Numeric(10, 2))
    pne_bondas = Column(Numeric(10, 2))
    waste = Column(Numeric(10, 2))

    # Calculated fields
    worked_spindles = Column(Numeric(10, 2))
    target_kgs = Column(Numeric(10, 2))
    actual_prdn = Column(Numeric(10, 2))
    waste_percent = Column(Numeric(10, 2))
    efficiency = Column(Numeric(10, 2))
    oee = Column(Numeric(10, 2))

    remarks = Column(String)

    # Relationships
    mill = relationship("Mill", back_populates="productions")
    department = relationship("Department", back_populates="productions")
    shift = relationship("Shift", back_populates="productions")
    machine = relationship("Machine", back_populates="productions")
    employee = relationship("Employee", back_populates="productions")
    count = relationship("CountMaster", back_populates="productions")