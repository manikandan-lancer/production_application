def calc_efficiency(actual, target):
    if not target or target == 0:
        return 0
    return round((actual / target) * 100, 2)


def calc_availability(run_hours, total_hours=8):
    if not total_hours or total_hours == 0:
        return 0
    return round(run_hours / total_hours, 2)


def calc_performance(actual, speed=None, tpi=None, hank=None):
    if not actual:
        return 0
    # Simple placeholder formula → you must tell me final formula!
    return 1.0  


def calc_quality(actual, waste):
    total = actual + waste
    if total == 0:
        return 0
    return round(actual / total, 2)


def calc_oee(availability, performance, quality):
    return round(availability * performance * quality, 3)