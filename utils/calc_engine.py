# -----------------------------------------------------------
# SAFE CONVERSION
# -----------------------------------------------------------
def safe(v):
    try:
        if v is None:
            return 0.0
        return float(v)
    except:
        return 0.0


# -----------------------------------------------------------
# COUNT MASTER
# -----------------------------------------------------------
def calc_conversion_factor(actual_count, eff_base):
    ac = safe(actual_count)
    eff = safe(eff_base) / 100

    if ac == 0:
        return 0.0

    return round((1 / ac) * 0.4536 * eff, 2)


# -----------------------------------------------------------
# MACHINE MASTER
# -----------------------------------------------------------
def calc_std_hank(speed, tpi, efficiency):
    sp = safe(speed)
    t = safe(tpi)
    eff = safe(efficiency) / 100

    if t == 0:
        return 0.0

    return round((sp / t) * 0.01587394 * eff, 2)


# -----------------------------------------------------------
# DAILY ENTRY CALCULATIONS
# -----------------------------------------------------------
def calc_worked_spindles(spindles, stop_min):
    sp = safe(spindles)
    st = safe(stop_min)
    return round(sp - (st * (sp / 480)), 4)


def calc_target_kgs(std_hank, spindles, run_hours, conv_factor):
    std = safe(std_hank)
    sp = safe(spindles)
    hrs = safe(run_hours)
    cf = safe(conv_factor)

    return round(std * sp * hrs * cf, 6)


def calc_production_kgs(spindles, act_hank, conv_factor):
    sp = safe(spindles)
    hank = safe(act_hank)
    cf = safe(conv_factor)

    return round(sp * hank * cf, 4)


def calc_actual_prodn(prod_kgs, pne):
    return round(safe(prod_kgs) - safe(pne), 4)


def calc_waste_percent(waste, prod):
    p = safe(prod)
    if p == 0:
        return 0.0
    return round((safe(waste) / p) * 100, 2)


def calc_efficiency(act_hank, std_hank):
    std = safe(std_hank)
    if std == 0:
        return 0.0
    return round((safe(act_hank) / std) * 100, 2)


def calc_oee(eff, run_hours, stop_min):
    rh = safe(run_hours)
    if rh == 0:
        return 0.0

    availability = (rh - (safe(stop_min) / 60)) / rh
    performance = safe(eff) / 100

    return round(availability * performance * 100, 2)