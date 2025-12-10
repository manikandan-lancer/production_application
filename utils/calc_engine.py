# ----------------------------------------------------------
# CALCULATION ENGINE  (Shared across all modules)
# ----------------------------------------------------------

def safe_float(v):
    """Convert any value to float safely."""
    try:
        return float(v or 0)
    except:
        return 0.0


# ----------------------------------------------------------
# MACHINE MASTER CALCULATIONS
# ----------------------------------------------------------

def calc_std_hank(spdl_speed, tpi, efficiency):
    """
    STD_HANK = (Speed / TPI) * 0.01587394 * (Efficiency / 100)
    """
    spdl_speed = safe_float(spdl_speed)
    tpi = safe_float(tpi)
    eff = safe_float(efficiency) / 100

    if tpi == 0:
        return 0.0

    return round((spdl_speed / tpi) * 0.01587394 * eff, 2)


# ----------------------------------------------------------
# COUNT MASTER CALCULATIONS
# ----------------------------------------------------------

def calc_conversion_factor(actual_count, eff_base):
    """
    conversion_factor = (1 / actual_count) * 0.4536 * (eff_base / 100)
    """
    actual_count = safe_float(actual_count)
    eff = safe_float(eff_base) / 100

    if actual_count == 0:
        return 0.0

    return round((1 / actual_count) * 0.4536 * eff, 2)


# ----------------------------------------------------------
# DAILY ENTRY CALCULATIONS
# ----------------------------------------------------------

def calc_actual_production(prod_kgs, pne_bondas):
    """Actual = Prod − Pneumafil"""
    return round(safe_float(prod_kgs) - safe_float(pne_bondas), 4)


def calc_worked_spindles(spindles, stop_min):
    """
    Worked Spindles = Spindles – StopMin * (Spindles / 480)
    """
    sp = safe_float(spindles)
    st = safe_float(stop_min)

    deduction = st * (sp / 480)
    return round(sp - deduction, 4)


def calc_efficiency(act_hank, std_hank):
    """ Efficiency % = (ACT / STD) × 100 """
    act = safe_float(act_hank)
    std = safe_float(std_hank)

    if std == 0:
        return 0.0

    return round((act / std) * 100, 2)


def calc_availability(run_hours, stop_min):
    """ Availability = (RunHours - StopMin/60) / RunHours """
    rh = safe_float(run_hours)
    st = safe_float(stop_min)

    if rh == 0:
        return 0.0

    return (rh - (st / 60)) / rh


def calc_oee(eff_percent, run_hours, stop_min):
    """OEE = Availability × (Efficiency/100) * 100"""
    availability = calc_availability(run_hours, stop_min)
    eff = safe_float(eff_percent) / 100

    return round(availability * eff * 100, 2)


def calc_target_kgs(std_hank, worked_spindles, run_hours, conversion_factor):
    """Target = STD_HANK × WorkedSpindles × RunHours × ConversionFactor"""
    return round(
        safe_float(std_hank)
        * safe_float(worked_spindles)
        * safe_float(run_hours)
        * safe_float(conversion_factor),
        4,
    )


def calc_waste_percent(waste, prod_kgs):
    """Waste % = Waste / Prod × 100"""
    w = safe_float(waste)
    p = safe_float(prod_kgs)

    if p == 0:
        return 0.0

    return round((w / p) * 100, 2)
