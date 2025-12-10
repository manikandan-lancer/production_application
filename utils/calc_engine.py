# ----------------------------------------------------------
# CALCULATION ENGINE  (Shared by Masters + Daily Entry + Dashboard)
# ----------------------------------------------------------

def safe_float(v):
    """Convert safely to float."""
    try:
        return float(v or 0)
    except:
        return 0.0


# ----------------------------------------------------------
# MACHINE MASTER CALCULATIONS
# ----------------------------------------------------------

def calc_std_hank(spdl_speed, tpi, efficiency):
    """
    STD_HANK = (Speed / TPI) * 0.01587394 * (Efficiency % / 100)
    """
    spdl_speed = safe_float(spdl_speed)
    tpi = safe_float(tpi)
    eff = safe_float(efficiency) / 100

    if tpi == 0:
        return 0.0

    return round((spdl_speed / tpi) * 0.01587394 * eff, 4)


# ----------------------------------------------------------
# COUNT MASTER CALCULATIONS
# ----------------------------------------------------------

def calc_conversion_factor(actual_count, eff_base):
    """
    (1 / actual_count) * 0.4536 * (eff_base / 100)
    """
    actual_count = safe_float(actual_count)
    eff = safe_float(eff_base) / 100

    if actual_count == 0:
        return 0.0

    return round((1 / actual_count) * 0.4536 * eff, 2)


# ----------------------------------------------------------
# DAILY ENTRY CALCULATIONS
# ----------------------------------------------------------

def calc_worked_spindles(spindles, stop_min):
    """
    Worked Spindles = Spindles - StopMin * (Spindles / 480)
    """
    spd = safe_float(spindles)
    stop_min = safe_float(stop_min)

    return round(spd - (stop_min * (spd / 480.0)), 2)


def calc_target_kgs(std_hank, worked_spindles, run_hours, conversion_factor):
    """
    TARGET = STD_HANK * Worked_Spindles * Run_Hours * ConversionFactor
    """
    std = safe_float(std_hank)
    wsp = safe_float(worked_spindles)
    hrs = safe_float(run_hours)
    cf = safe_float(conversion_factor)

    return round(std * wsp * hrs * cf, 4)


def calc_actual_production(prod_kgs, pne_bondas):
    """
    ACTUAL_PRODUCTION = Prod_kgs - Pne_bondas
    """
    return round(safe_float(prod_kgs) - safe_float(pne_bondas), 4)


def calc_waste_percent(waste, prod_kgs):
    """
    Waste% = (Waste / Prod_kgs) * 100
    """
    waste = safe_float(waste)
    prod = safe_float(prod_kgs)

    if prod == 0:
        return 0.0

    return round((waste / prod) * 100, 2)


def calc_efficiency(act_hank, std_hank):
    """
    Efficiency = (ACT_HANK / STD_HANK) * 100
    """
    act = safe_float(act_hank)
    std = safe_float(std_hank)

    if std == 0:
        return 0.0

    return round((act / std) * 100, 2)


def calc_availability(run_hours, stop_min):
    """
    Availability = (Run Hours - StopMin/60) / Run Hours
    """
    run_hours = safe_float(run_hours)
    stop_min = safe_float(stop_min)

    if run_hours == 0:
        return 0.0

    return (run_hours - (stop_min / 60)) / run_hours


def calc_oee(efficiency_percent, run_hours, stop_min):
    """
    OEE = Availability × (Efficiency / 100)
    """
    eff = safe_float(efficiency_percent) / 100
    availability = calc_availability(run_hours, stop_min)

    return round(availability * eff * 100, 2)