def safe(v):
    try:
        return float(v or 0)
    except:
        return 0.0


# ----------------------------
# COUNT MASTER
# ----------------------------
def calc_conversion_factor(actual_count, efficiency_base):
    ac = safe(actual_count)
    eff = safe(efficiency_base) / 100

    if ac == 0:
        return 0.0

    return round((1 / ac) * 0.4536 * eff, 6)


# ----------------------------
# MACHINE MASTER
# ----------------------------
def calc_std_hank(spdl_speed, tpi, efficiency):
    spd = safe(spdl_speed)
    tpi = safe(tpi)
    eff = safe(efficiency) / 100

    if tpi == 0:
        return 0.0

    return round((spd / tpi) * 0.01587394 * eff, 6)


# ----------------------------
# DAILY ENTRY
# ----------------------------
def calc_worked_spindles(spindles, stop_min):
    sp = safe(spindles)
    st = safe(stop_min)
    return round(sp - (st * (sp / 480)), 4)


def calc_target_kgs(conv_factor, spindles, std_hank):
    return round(safe(conv_factor) * safe(spindles) * safe(std_hank), 4)


def calc_prodn_kgs(conv_factor, spindles, act_hank):
    return round(safe(conv_factor) * safe(spindles) * safe(act_hank), 4)


def calc_actual_prdn(prod_kgs, pne):
    return round(safe(prod_kgs) - safe(pne), 4)


def calc_waste_percent(pne, prod_kgs):
    if safe(prod_kgs) == 0:
        return 0.0
    return round((safe(pne) / safe(prod_kgs)) * 100, 2)


def calc_efficiency(act_hank, std_hank):
    if safe(std_hank) == 0:
        return 0.0
    return round((safe(act_hank) / safe(std_hank)) * 100, 2)


def calc_oee(efficiency):
    return round(safe(efficiency), 2)