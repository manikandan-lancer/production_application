# ----------------------------------------------------------
# CALC ENGINE (Shared across all modules)
# ----------------------------------------------------------

def safe_float(v):
    """Safely convert values to float."""
    try:
        return float(v or 0)
    except:
        return 0.0


# ----------------------------------------------------------
# MACHINE MASTER CALCULATIONS
# ----------------------------------------------------------

def calc_std_hank(spdl_speed, tpi, efficiency):
    """
    STD HANK = (Speed / TPI) * 0.01587394 * (Efficiency % / 100)
    """

    spd = safe_float(spdl_speed)
    tpi = safe_float(tpi)
    eff = safe_float(efficiency) / 100

    if tpi == 0:
        return 0.0

    return round((spd / tpi) * 0.01587394 * eff, 6)


# ----------------------------------------------------------
# COUNT MASTER CALCULATIONS
# ----------------------------------------------------------

def calc_conversion_factor(actual_count, eff_base):
    """
    ConversionFactor = (1/ActualCount) * 0.4536 * (EffBase % / 100)
    """

    ac = safe_float(actual_count)
    eff = safe_float(eff_base) / 100

    if ac == 0:
        return 0.0

    return round((1 / ac) * 0.4536 * eff, 8)


# ----------------------------------------------------------
# DAILY ENTRY CALCULATIONS
# ----------------------------------------------------------

def calc_worked_spindles(spindles, stop_min):
    """
    Worked Spindles = Spindles - (StopMin * (Spindles / 480))
    """
    spd = safe_float(spindles)
    stop = safe_float(stop_min)

    if spd == 0:
        return 0.0

    return round(spd - (stop * (spd / 480)), 6)


def calc_actual_production(prod_kgs, pne_bondas):
    """ Actual Production = Prod - Pneumafil """
    return round(safe_float(prod_kgs) - safe_float(pne_bondas), 4)


def calc_waste_percent(waste, prod_kgs):
    """ Waste % = Waste / Production """
    w = safe_float(waste)
    p = safe_float(prod_kgs)

    if p == 0:
        return 0.0

    return round((w / p) * 100, 2)


def calc_efficiency(act_hank, std_hank):
    """
    Efficiency = (ACT_HANK / STD_HANK) * 100
    """
    a = safe_float(act_hank)
    s = safe_float(std_hank)

    if s == 0:
        return 0.0

    return round((a / s) * 100, 2)


def calc_availability(run_hours, stop_min):
    """
    Availability = (Run Hours - StopMin/60) / Run Hours
    """

    rh = safe_float(run_hours)
    stop = safe_float(stop_min)

    if rh == 0:
        return 0.0

    avail = (rh - (stop / 60)) / rh
    return max(0, min(avail, 1))  # Bound between 0 and 1


def calc_oee(efficiency_percent, run_hours, stop_min):
    """
    OEE = Availability × (Efficiency / 100)
    """

    eff = safe_float(efficiency_percent) / 100
    availability = calc_availability(run_hours, stop_min)

    return round(availability * eff * 100, 2)


def calc_target_kgs(std_hank, worked_spindles, run_hours, conversion_factor):
    """
    TARGET KGS = STD_HANK × WorkedSpindles × RunHours × ConversionFactor
    """
    sh = safe_float(std_hank)
    ws = safe_float(worked_spindles)
    rh = safe_float(run_hours)
    cf = safe_float(conversion_factor)

    return round(sh * ws * rh * cf, 4)