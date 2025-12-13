# utils/calc_engine.py

def safe_float(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


# -------------------------------
# MASTER CALCULATIONS
# -------------------------------
def calc_std_hank(spdl_speed, tpi, std_hank_eff):
    sp = safe_float(spdl_speed)
    t = safe_float(tpi)
    eff = safe_float(std_hank_eff) / 100

    if t == 0:
        return 0.0

    # ❌ NO ROUNDING
    return (sp / t) * 0.01587394 * eff


def calc_conversion_factor(actual_count, spinning_eff):
    ac = safe_float(actual_count)
    eff = safe_float(spinning_eff) / 100

    if ac == 0:
        return 0.0

    return (1 / ac) * 0.4536 * eff


# -------------------------------
# DAILY ENTRY CALCULATIONS
# -------------------------------
def calc_worked_spindles(spindles, stop_min):
    sp = safe_float(spindles)
    stop = safe_float(stop_min)
    return sp - (stop * sp / 480)


def calc_target_kgs(cf, spindles, std_hank):
    return safe_float(cf) * safe_float(spindles) * safe_float(std_hank)


def calc_prod_kgs(cf, spindles, act_hank):
    return safe_float(cf) * safe_float(spindles) * safe_float(act_hank)


def calc_actual_prdn(prod_kgs, pne_bondas):
    return safe_float(prod_kgs) - safe_float(pne_bondas)


def calc_waste_percent(pne_bondas, prod_kgs):
    prod = safe_float(prod_kgs)
    if prod == 0:
        return 0.0
    return (safe_float(pne_bondas) / prod) * 100