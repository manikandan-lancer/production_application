# -------------------------------------------------------------
# CALC ENGINE — FINAL VERSION (100% aligned with new structure)
# -------------------------------------------------------------

def safe_float(v):
    """Safely convert to float (None → 0)."""
    try:
        return float(v or 0)
    except:
        return 0.0


# -------------------------------------------------------------
# COUNT MASTER CALCULATION
# -------------------------------------------------------------
def calc_conversion_factor(actual_count, spinning_efficiency):
    """
    Formula:
        CF = (1 / actual_count) * 0.4536 * (spinning_efficiency / 100)
    """

    ac = safe_float(actual_count)
    eff = safe_float(spinning_efficiency) / 100

    if ac == 0:
        return 0.0

    return round((1 / ac) * 0.4536 * eff, 2)


# -------------------------------------------------------------
# MACHINE MASTER — STD HANK
# -------------------------------------------------------------
def calc_std_hank(spdl_speed, tpi, std_hank_efficiency):
    """
    Formula:
        StdHank = (Speed / TPI) * 0.01587394 * (StdHankEfficiency / 100)
    """
    sp = safe_float(spdl_speed)
    t = safe_float(tpi)
    eff = safe_float(std_hank_efficiency) / 100

    if t == 0:
        return 0.0

    return round((sp / t) * 0.01587394 * eff, 2)


# -------------------------------------------------------------
# DAILY ENTRY — WORKED SPINDLES
# -------------------------------------------------------------
def calc_worked_spindles(spindles, stop_min):
    """
    Formula:
        Worked Spindles = Spindles - (StopMin * (Spindles / 480))
    """
    sp = safe_float(spindles)
    st = safe_float(stop_min)

    return round(sp - st * (sp / 480), 4)


# -------------------------------------------------------------
# DAILY ENTRY — TARGET KGS
# -------------------------------------------------------------
def calc_target_kgs(conversion_factor, spindles, std_hank):
    """
    NEW FORMULA:
        Target Kgs = Conversion Factor × Spindles × Std Hank
    """
    cf = safe_float(conversion_factor)
    sp = safe_float(spindles)
    std = safe_float(std_hank)

    return round(cf * sp * std, 4)


# -------------------------------------------------------------
# DAILY ENTRY — ACTUAL PRODUCTION
# -------------------------------------------------------------
def calc_actual_production(prod_kgs, pne_bondas):
    """
    Formula:
        Actual Prdn = Prod Kgs - Pneumafil
    """
    return round(safe_float(prod_kgs) - safe_float(pne_bondas), 4)


# -------------------------------------------------------------
# DAILY ENTRY — WASTE PERCENT
# -------------------------------------------------------------
def calc_waste_percent(pne_bondas, prod_kgs):
    """
    Formula:
        Waste % = (Pneumafil / Prod Kgs) × 100
    """
    p = safe_float(prod_kgs)
    pne = safe_float(pne_bondas)

    if p == 0:
        return 0.0

    return round((pne / p) * 100, 2)
