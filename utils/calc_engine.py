# ----------------------------------------------------------
# CALCULATION ENGINE (Shared across all modules)
# ----------------------------------------------------------

def safe_float(v):
    """Safely convert any input to float."""
    try:
        return float(v or 0)
    except:
        return 0.0


# ----------------------------------------------------------
# COUNT MASTER CALCULATIONS
# ----------------------------------------------------------

def calc_conversion_factor(actual_count, eff_base):
    """
    Conversion Factor = (1 / actual_count) * 0.4536 * (eff_base / 100)
    """

    actual_count = safe_float(actual_count)
    eff = safe_float(eff_base) / 100

    if actual_count == 0:
        return 0.0

    return round((1 / actual_count) * 0.4536 * eff, 6)


# ----------------------------------------------------------
# MACHINE MASTER CALCULATIONS
# ----------------------------------------------------------

def calc_std_hank(spdl_speed, tpi, efficiency):
    """
    STD_HANK = (Speed / TPI) * 0.01587394 * (Efficiency% / 100)
    """

    spd = safe_float(spdl_speed)
    tpi = safe_float(tpi)
    eff = safe_float(efficiency) / 100

    if tpi == 0:
        return 0.0

    return round((spd / tpi) * 0.01587394 * eff, 6)


# ----------------------------------------------------------
# DAILY ENTRY CALCULATIONS
# ----------------------------------------------------------

def calc_worked_spindles(spindles, stop_min):
    """
    Worked Spindles = Spindles - StopMin * (Spindles / 480)
    """

    sp = safe_float(spindles)
    sm = safe_float(stop_min)

    return round(sp - sm * (sp / 480), 4)


def calc_actual_production(prod_kgs, pne_bondas):
    """Actual Production = Prod Kgs - Pneumafil"""
    return round(safe_float(prod_kgs) - safe_float(pne_bondas), 4)


def calc_waste_percent(pne_bondas, prod_kgs):
    """Waste % = (Pneumafil / Production) * 100"""

    pne = safe_float(pne_bondas)
    prod = safe_float(prod_kgs)

    if prod == 0:
        return 0.0

    return round((pne / prod) * 100, 2)


def calc_efficiency(act_hank, std_hank):
    """Efficiency = (ACT_HANK / STD_HANK) * 100"""

    act = safe_float(act_hank)
    std = safe_float(std_hank)

    if std == 0:
        return 0.0

    return round((act / std) * 100, 2)


def calc_availability(run_hours, stop_min):
    """
    Availability = (RunHours - StopMin/60) / RunHours
    """

    hrs = safe_float(run_hours)
    sm = safe_float(stop_min)

    if hrs == 0:
        return 0.0

    return (hrs - (sm / 60)) / hrs


def calc_oee(efficiency_percent, run_hours, stop_min):
    """
    OEE = Availability × (Efficiency% / 100) × 100
    """

    eff = safe_float(efficiency_percent) / 100
    availability = calc_availability(run_hours, stop_min)

    return round(availability * eff * 100, 2)


# ----------------------------------------------------------
# TARGET CALCULATION
# ----------------------------------------------------------

def calc_target_kgs(std_hank, spindles, run_hours, conversion_factor):
    """
    TARGET KG = ConversionFactor × Spindles × STD_HANK × RunHours
    """

    std = safe_float(std_hank)
    sp = safe_float(spindles)
    hrs = safe_float(run_hours)
    cf = safe_float(conversion_factor)

    return round(cf * sp * std * hrs, 4)