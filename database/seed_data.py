from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Mill, Department, Shift, Machine
from datetime import time

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()


# ---------------------------------------------------------
# UTILITY: ADD IF NOT EXISTS
# ---------------------------------------------------------
def add_once(model, **kwargs):
    existing = session.query(model).filter_by(**kwargs).first()
    if existing:
        return existing
    obj = model(**kwargs)
    session.add(obj)
    session.commit()
    return obj


# ---------------------------------------------------------
# 1. MILLS
# ---------------------------------------------------------
mill_names = ["Mill A", "Mill B", "Mill C", "Mill D"]
mills = {}

for name in mill_names:
    mills[name] = add_once(Mill, mill_name=name)


# ---------------------------------------------------------
# 2. DEPARTMENTS 1,2,3
# ---------------------------------------------------------
departments = {}
for dept_id in [1, 2, 3]:
    departments[dept_id] = add_once(
        Department,
        id=dept_id,
        department_name=f"Department {dept_id}"
    )


# ---------------------------------------------------------
# 3. SHIFTS (No change)
# ---------------------------------------------------------
shift_data = [
    ("Shift 1", time(6, 0), time(14, 0)),
    ("Shift 2", time(14, 0), time(22, 0)),
    ("Shift 3", time(22, 0), time(6, 0)),
]

for name, start, end in shift_data:
    add_once(
        Shift,
        shift_name=name,
        start_time=start,
        end_time=end
    )


# ---------------------------------------------------------
# 4. MACHINE MASTER CREATION (NO COUNTS, NO SPEED/TPI)
# ---------------------------------------------------------
# Mill A → 40 machines
for i in range(1, 41):
    add_once(
        Machine,
        machine_name=f"A{i:02d}",
        mill_id=mills["Mill A"].id,
        department_id=1,   # default dept
        spindles=None,
        spdl_speed=None,
        tpi=None,
        efficiency=None,
        std_hank=None,
        allocated_count_id=None
    )

# Mill B → 12 machines
for i in range(1, 13):
    add_once(
        Machine,
        machine_name=f"B{i:02d}",
        mill_id=mills["Mill B"].id,
        department_id=1,
        spindles=None,
        spdl_speed=None,
        tpi=None,
        efficiency=None,
        std_hank=None,
        allocated_count_id=None
    )

# Mill C → 12 machines
for i in range(1, 13):
    add_once(
        Machine,
        machine_name=f"C{i:02d}",
        mill_id=mills["Mill C"].id,
        department_id=1,
        spindles=None,
        spdl_speed=None,
        tpi=None,
        efficiency=None,
        std_hank=None,
        allocated_count_id=None
    )

# Mill D → 12 machines
for i in range(1, 13):
    add_once(
        Machine,
        machine_name=f"D{i:02d}",
        mill_id=mills["Mill D"].id,
        department_id=1,
        spindles=None,
        spdl_speed=None,
        tpi=None,
        efficiency=None,
        std_hank=None,
        allocated_count_id=None
    )


print("\n========================================")
print("✅ SEED COMPLETED SUCCESSFULLY")
print("👉 You may now add Counts via Count Master")
print("👉 You may now add speed/tpi via Machine Master")
print("========================================\n")
