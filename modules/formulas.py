# -----------------------------
# Spinning Mill Formula Engine
# -----------------------------

def calc_efficiency(actual, target):
    """Efficiency % = (Actual / Target) * 100"""
    if not target or target == 0:
        return 0
    return round((actual / target) * 100, 2)


def calc_availability(run_hr, total_shift_hr=8):
    """Availability = Run Hours / Total Shift Hours"""
    if total_shift_hr == 0:
        return 0
    return round(run_hr / total_shift_hr, 2)


def calc_performance(actual, speed, tpi, std_hank):
    """Performance = Actual output vs theoretical"""
    try:
        if speed == 0 or tpi == 0 or std_hank == 0:
            return 0
        theoretical_prod = (speed / (tpi * std_hank))
        if theoretical_prod == 0:
            return 0
        return round(actual / theoretical_prod, 2)
    except:
        return 0


def calc_quality(actual, waste):
    """Quality = Good Output / Total Production"""
    total = actual + waste
    if total == 0:
        return 0
    good_output = actual
    return round(good_output / total, 2)


def calc_oee(availability, performance, quality):
    """OEE = A * P * Q"""
    return round(availability * performance * quality * 100, 2)