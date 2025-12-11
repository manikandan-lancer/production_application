# utils/calc_engine.py

def safe_float(v):
    try:
        return float(v or 0)
    except:
        return 0.0


# -------------------------------------------
# MACHINE MASTER
# -------------------------------------------
def calc_std_hank(spdl_speed, tpi, std_hank_efficiency):
    """
    STD =
    (Speed / TPI) * 0.01587394 * (StdHankEfficiency / 100)
    """
    sp = safe_float(spdl_speed)
    t = safe_float(tpi)
    eff = safe_float(std_hank_efficiency) / 100

    if t == 0:
        return 0.0

    return round((sp / t) * 0.01587394 * eff, 2)


# -------------------------------------------
# COUNT MASTER
# -------------------------------------------
def calc_conversion_factor(actual_count, spinning_efficiency):
    """
    CF = (1 / actual_count) * 0.4536 * (SpinningEfficiency / 100)
    """

    ac = safe_float(actual_count)
    eff = safe_float(spinning_efficiency) / 100

    if ac == 0:
        return 0.0

    return round((1 / ac) * 0.4536 * eff, 2)


# -------------------------------------------
# DAILY ENTRY CALCULATIONS
# -------------------------------------------
def calc_worked_spindles(spindles, stop_min):
    sp = safe_float(spindles)
    st = safe_float(stop_min)

    return round(sp - st * (sp / 480), 4)


def calc_target_kgs(std_hank, worked_spindles, run_hours, cf):
    return round(
        safe_float(std_hank)
        * safe_float(worked_spindles)
        * safe_float(run_hours)
        * safe_float(cf),
        4
    )


def calc_actual_production(prod_kgs, pne):
    return round(safe_float(prod_kgs) - safe_float(pne), 4)


def calc_waste_percent(waste, prod_kgs):
    w = safe_float(waste)
    p = safe_float(prod_kgs)

    if p == 0:
        return 0.0

    return round((w / p) * 100, 2)


def calc_efficiency(act_hank, std_hank):
    std = safe_float(std_hank)
    if std == 0:
        return 0.0

    return round((safe_float(act_hank) / std) * 100, 2)


def calc_availability(run_hours, stop_min):
    rh = safe_float(run_hours)
    if rh == 0:
        return 0.0

    return (rh - (safe_float(stop_min) / 60)) / rh


def calc_oee(efficiency, run_hours, stop_min):
    availability = calc_availability(run_hours, stop_min)
    return round(availability * (safe_float(efficiency) / 100) * 100, 2)