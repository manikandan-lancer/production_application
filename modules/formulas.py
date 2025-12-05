# -----------------------------
#   Spinning Mill Formula Engine
# -----------------------------

def calc_efficiency(actual, target):
    """Efficiency % = (Actual / Target) * 100"""
    if not target or target == 0:
        return 0
    return round((actual / target) * 100, 2)


def calc_availability(run_hours, total_hours=8):
    """Availability = Run Hours / Total Shift Hours"""
    if not total_hours or total_hours == 0:
        return 0
    if not run_hours:
        return 0
    return round(run_hours / total_hours, 2)


def calc_performance(actual, speed=None, tpi=None, hank=None):
    """
    Performance (new simplified logic):
    - Old system used machine-speed-based formula
    - New design uses count-based production
    - For now: Performance = Actual Output (normalized)
    """

    if not actual or actual == 0:
        return 0

    # Future-proof hook for advanced formula when count-master is expanded
    return 1.0   # Placeholder = 100%


def calc_quality(actual, waste):
    """Quality = Good Output / Total Production"""
    if not actual and not waste:
        return 0

    total = (actual or 0) + (waste or 0)
    if total == 0:
        return 0

    return round((actual or 0) / total, 2)


def calc_oee(availability, performance, quality):
    """OEE = A * P * Q * 100"""
    if availability is None: availability = 0
    if performance is None: performance = 0
    if quality is None: quality = 0

    return round(availability * performance * quality * 100, 2)
