from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import (
    Mill, Department, Shift, CountMaster, Machine
)
from datetime import time

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()


# ---------------------------------------------------------
# UTILITY: ADD IF NOT EXISTS
# ---------------------------------------------------------
def add_once(model, **kwargs):
    exists = session.query(model).filter_by(**kwargs).first()
    if not exists:
        obj = model(**kwargs)
        session.add(obj)
        session.commit()
        return obj
    return exists


# ---------------------------------------------------------
# 1. MILLS
# ---------------------------------------------------------
mills = {}
mill_names = ["Mill A", "Mill B", "Mill C", "Mill D"]

for name in mill_names:
    mill = add_once(Mill, mill_name=name)
    mills[name] = mill


# ---------------------------------------------------------
# 2. DEPARTMENTS (1, 2, 3)
# ---------------------------------------------------------
departments = {}
for dept_id in [1, 2, 3]:
    dept = add_once(Department, id=dept_id, department_name=f"Department {dept_id}")
    departments[dept_id] = dept


# ---------------------------------------------------------
# 3. SHIFTS
# ---------------------------------------------------------
shifts = [
    ("Shift 1", time(6, 0), time(14, 0)),
    ("Shift 2", time(14, 0), time(22, 0)),
    ("Shift 3", time(22, 0), time(6, 0)),
]

for name, start, end in shifts:
    add_once(Shift, shift_name=name, start_time=start, end_time=end)


# ---------------------------------------------------------
# 4. COUNT MASTER (PRODUCTS)
# ---------------------------------------------------------

counts_mill_A = [
    "60PSF","60PSF","60PSF","60PSF","60PSF","60PSF","60PSF","60PSF","60PSF","60PSF",
    "60PSF","60PSF","60PSF","45PSF","45PSF","45PSFHT","45PSFHT","50PSF","57PC","57PC",
    "57PC","45PSF","63PSF","63PSF","63PSF","45PSF","50PSFL","57PSFL","57PSFL","57PSFL",
    "50PSFL","50PSFL","50PSFL","50PSFL","50PSFL","50PSFL","50PSFL","50PSFL","50PSFL",
    "20PC"
]

counts_mill_B = [
    "4.6PSF","10PSF","10PSF","63PSF","63PSF","63PSF","63PSF","63PSF",
    "63PSF","63PSF","40PSF","40PSF"
]

counts_mill_C = [
    "40PSFS","40PSF","40PSF","40PSF","40PSF","40PSF",
    "40PSF","40PSF","40PSF","40PSF","40PSF","40PSF"
]

counts_mill_D = [
    "4.6PSF","50PSFL","50PSFL","45PSF","45PSF","63PSF",
    "63PSF","63PSF","63PSF","25PSFL","20PSFL","20PSFL"
]


def insert_counts(mill_name, count_list):
    mill = mills[mill_name]
    for cname in count_list:
        add_once(CountMaster, mill_id=mill.id, count_name=cname)


insert_counts("Mill A", counts_mill_A)
insert_counts("Mill B", counts_mill_B)
insert_counts("Mill C", counts_mill_C)
insert_counts("Mill D", counts_mill_D)


# ---------------------------------------------------------
# 5. MACHINE MASTER
# ---------------------------------------------------------

# 40 Machines for Mill A → A01 … A40
for i in range(1, 41):
    add_once(
        Machine,
        machine_name=f"A{i:02d}",
        mill_id=mills["Mill A"].id,
        department_id=1,  # default dept
        spindles=None,
        allocated_count_id=None
    )

# 12 Machines each for B, C, D
for i in range(1, 13):
    add_once(
        Machine,
        machine_name=f"B{i:02d}",
        mill_id=mills["Mill B"].id,
        department_id=1,
        spindles=None,
        allocated_count_id=None
    )

    add_once(
        Machine,
        machine_name=f"C{i:02d}",
        mill_id=mills["Mill C"].id,
        department_id=1,
        spindles=None,
        allocated_count_id=None
    )

    add_once(
        Machine,
        machine_name=f"D{i:02d}",
        mill_id=mills["Mill D"].id,
        department_id=1,
        spindles=None,
        allocated_count_id=None
    )


# ---------------------------------------------------------
# DONE
# ---------------------------------------------------------
print("✅ Seed Completed Successfully!")