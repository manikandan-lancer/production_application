# ----------------------------------------------------------
# SAFE FLOAT
# ----------------------------------------------------------

def safe_float(v):
    """Safely convert to float; return 0 if invalid."""
    try:
        return float(v or 0)
    except:
        return 0.0


# ----------------------------------------------------------
# COUNT MASTER — Conversion Factor
# ----------------------------------------------------------
def calc_conversion_factor(actual_count, spinning_eff):
    """
    conversion_factor = (1 / actual_count) * 0.4536 * (spinning_eff / 100)
    """
    ac = safe_float(actual_count)
    eff = safe_float(spinning_eff) / 100

    if ac == 0:
        return 0.0

    return round((1 / ac) * 0.4536 * eff, 2)


# ----------------------------------------------------------
# MACHINE MASTER — STD HANK
# ----------------------------------------------------------
def calc_std_hank(speed, tpi, std_hank_eff):
    """
    STD_HANK = (Speed / TPI) * 0.01587394 * (StdHankEfficiency / 100)
    """
    sp = safe_float(speed)
    t = safe_float(tpi)
    eff = safe_float(std_hank_eff) / 100

    if t == 0:
        return 0.0

    return round((sp / t) * 0.01587394 * eff, 2)


# ----------------------------------------------------------
# DAILY ENTRY — Worked Spindles
# ----------------------------------------------------------
def calc_worked_spindles(spindles, stop_min):
    """
    Worked = Spindles - (StopMin × Spindles/480)
    """
    sp = safe_float(spindles)
    st = safe_float(stop_min)

    return round(sp - (st * (sp / 480)), 4)


# ----------------------------------------------------------
# DAILY ENTRY — Target Kgs
# ----------------------------------------------------------
def calc_target_kgs(conversion_factor, spindles, std_hank):
    """
    Target = CF × Spindles × StdHank
    """
    return round(
        safe_float(conversion_factor)
        * safe_float(spindles)
        * safe_float(std_hank),
        4,
    )


# ----------------------------------------------------------
# DAILY ENTRY — Production Kgs
# ----------------------------------------------------------
def calc_production_kgs(conversion_factor, spindles, act_hank):
    """
    Production_Kgs = CF × Spindles × ActHank
    """
    return round(
        safe_float(conversion_factor)
        * safe_float(spindles)
        * safe_float(act_hank),
        4,
    )


# ----------------------------------------------------------
# DAILY ENTRY — Actual Production
# ----------------------------------------------------------
def calc_actual_production(prodn_kgs, pne_bondas):
    """
    Actual = Production - Pneumafil
    """
    return round(
        safe_float(prodn_kgs) - safe_float(pne_bondas),
        4,
    )


# ----------------------------------------------------------
# DAILY ENTRY — Waste Percent
# ----------------------------------------------------------
def calc_waste_percent(pne_bondas, prodn_kgs):
    """
    Waste% = (Pneumafil / Production) × 100
    """
    p = safe_float(prodn_kgs)
    if p == 0:
        return 0.0

    return round((safe_float(pne_bondas) / p) * 100, 2)

