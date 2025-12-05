# -----------------------------
# Production Formula Engine
# -----------------------------

def calc_efficiency(actual, target):
    if not target or target == 0:
        return 0
    return round((actual / target) * 100, 2)


def calc_availability(run_hours, total_hours=8):
    if not total_hours or total_hours == 0:
        return 0
    return round(run_hours / total_hours, 2)


def calc_performance(actual, production_factor):
    if not production_factor or production_factor == 0:
        return 0
    return round(actual / production_factor, 2)


def calc_quality(actual, waste):
    total = (actual or 0) + (waste or 0)
    if total == 0:
        return 0
    return round(actual / total, 2)


def calc_oee(availability, performance, quality):
    return round(availability * performance * quality * 100, 2)