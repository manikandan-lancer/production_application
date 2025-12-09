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
for name in ["Mill A", "Mill B", "Mill C", "Mill D"]:
    mills[name] = add_once(Mill, mill_name=name)


# ---------------------------------------------------------
# 2. DEPARTMENTS
# ---------------------------------------------------------
departments = {}
for dept_id in [1, 2, 3]:
    departments[dept_id] = add_once(
        Department,
        id=dept_id,
        department_name=f"Department {dept_id}"
    )


# ---------------------------------------------------------
# 3. SHIFTS
# ---------------------------------------------------------
shift_data = [
    ("Shift 1", time(6, 0), time(14, 0)),
    ("Shift 2", time(14, 0), time(22, 0)),
    ("Shift 3", time(22, 0), time(6, 0)),
]

for name, start, end in shift_data:
    add_once(Shift, shift_name=name, start_time=start, end_time=end)


# ---------------------------------------------------------
# 4. COUNT MASTER
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


def insert_counts(mill_name, items):
    mill = mills[mill_name]
    for c in items:
        add_once(CountMaster, mill_id=mill.id, count_name=c)


insert_counts("Mill A", counts_mill_A)
insert_counts("Mill B", counts_mill_B)
insert_counts("Mill C", counts_mill_C)
insert_counts("Mill D", counts_mill_D)


# ---------------------------------------------------------
# 5. MACHINE CONSTANTS (SPEED + TPI)
# ---------------------------------------------------------

spdl_A = [
    16038,15973,15973,15973,15973,16511,15039,16082,16711,16076,
    16076,16074,16076,17019,16002,16778,16778,17441,12551,16292,
    16038,16038,11000,13756,13771,13000,16053,16085,16085,16085,
    16061,16563,14875,14859,14343,15003,15635,15635,15891,12546
]

tpi_A = [
    22.9,23.0,23.3,23.3,23.3,23.8,23.8,23.8,23.5,23.3,
    23.3,23.3,23.3,20.8,20.9,35.5,35.5,21.1,24.7,24.6,
    24.7,21.3,24.6,24.6,24.6,20.8,21.3,23.9,23.9,23.9,
    21.3,21.3,21.3,20.9,21.3,21.3,21.1,21.2,21.2,14.3
]

spdl_B = [7100,9816,10250,14285,15175,15175,13645,16835,16835,16449,15453,16200]
tpi_B  = [9.23,9.93,9.46,25.11,25.11,25.11,25.11,25.11,25.11,25.11,19.58,19.58]

spdl_C = [12753,15553,15328,13336,16038,14469,16038,15778,15803,15878,16038,13652]
tpi_C  = [20.56,19.12,19.12,19.12,19.12,19.12,19.58,19.58,19.58,19.58,19.12,19.12]

spdl_D = [7400,16350,16350,16241,14756,17028,17028,16698,17028,12963,12463,12403]
tpi_D  = [8.04,21.55,21.55,20.03,20.03,25.07,25.07,25.11,25.11,15.12,13.72,13.72]


# ---------------------------------------------------------
# 6. MACHINE CREATION + ATTRIBUTE ASSIGNMENT
# ---------------------------------------------------------

# Mill A → 40 machines
for i in range(40):
    m = add_once(
        Machine,
        machine_name=f"A{i+1:02d}",
        mill_id=mills["Mill A"].id,
        department_id=1,
        spindles=None
    )
    m.spdl_speed = spdl_A[i]
    m.tpi = tpi_A[i]

    # assign count
    count = session.query(CountMaster).filter_by(
        mill_id=mills["Mill A"].id,
        count_name=counts_mill_A[i]
    ).first()
    m.allocated_count_id = count.id
    session.commit()


# Mill B → 12 machines
for i in range(12):
    m = add_once(
        Machine,
        machine_name=f"B{i+1:02d}",
        mill_id=mills["Mill B"].id,
        department_id=1,
        spindles=None
    )
    m.spdl_speed = spdl_B[i]
    m.tpi = tpi_B[i]

    count = session.query(CountMaster).filter_by(
        mill_id=mills["Mill B"].id,
        count_name=counts_mill_B[i]
    ).first()
    m.allocated_count_id = count.id
    session.commit()


# Mill C → 12 machines
for i in range(12):
    m = add_once(
        Machine,
        machine_name=f"C{i+1:02d}",
        mill_id=mills["Mill C"].id,
        department_id=1,
        spindles=None
    )
    m.spdl_speed = spdl_C[i]
    m.tpi = tpi_C[i]

    count = session.query(CountMaster).filter_by(
        mill_id=mills["Mill C"].id,
        count_name=counts_mill_C[i]
    ).first()
    m.allocated_count_id = count.id
    session.commit()


# Mill D → 12 machines
for i in range(12):
    m = add_once(
        Machine,
        machine_name=f"D{i+1:02d}",
        mill_id=mills["Mill D"].id,
        department_id=1,
        spindles=None
    )
    m.spdl_speed = spdl_D[i]
    m.tpi = tpi_D[i]

    count = session.query(CountMaster).filter_by(
        mill_id=mills["Mill D"].id,
        count_name=counts_mill_D[i]
    ).first()
    m.allocated_count_id = count.id
    session.commit()


print("✅ Seed Completed Successfully!")