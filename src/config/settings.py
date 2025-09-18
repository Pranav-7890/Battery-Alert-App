low_battery = 20
full_battery = 95

def get_battery_thresholds():
    return low_battery, full_battery

def set_battery_thresholds(low, full):
    global low_battery, full_battery
    low_battery = low
    full_battery = full