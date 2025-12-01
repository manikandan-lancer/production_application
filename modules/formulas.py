def calc_efficiency(actual, target):
    if not target or target == 0:
        return 0
    return round((actual / target) * 100, 2)

def calc_oee(availability, performance, quality):
    return round(availability * performance * quality, 2)
