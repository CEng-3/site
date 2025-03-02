# water_level.py
import time
import csv
import os
from DFRobot_ADS1115 import ADS1115

# Configuration constants
TARGET_DEPTH = 227.0       # mm (target depth for a full tank)
REFILL_THRESHOLD = 10.0    # % change needed to register a refill event
SAMPLE_INTERVAL = 0.5        #5 seconds between sensor readings
CYCLE_DURATION = 30    #5* 5-minute cycle (300 seconds)
NUM_SAMPLES = int(CYCLE_DURATION / SAMPLE_INTERVAL)

# File that the website reads for current water percentage
CURRENT_WATER_FILE = "current_water.txt"

# Sensor calibration/constants
RESISTOR = 120.0       # ohms
CURRENT_INIT = 3.15    # mA, calibrated current (no water)
RANGE = 5000           # mm (used in depth calculation)

# Global variable for water display (starts at 100%)
last_displayed_percentage = 100.0

# Create the ADS1115 instance and configure it
ads1115 = ADS1115()
ads1115.setAddr_ADS1115(0x48)
ads1115.setGain(0x00)  # 6.144V range

def get_depth():
    """
    Read sensor voltage and compute depth (in mm).
    Calculation:
       depth = max(0, (current - CURRENT_INIT) * (RANGE/16))
    """
    voltage_data = ads1115.readVoltage(1)  # using channel 1
    voltage_mv = voltage_data['r']
    current_ma = voltage_mv / RESISTOR
    depth = max(0, (current_ma - CURRENT_INIT) * (RANGE / 16.0))
    return depth

def convert_to_percentage(depth):
    """
    Convert a depth measurement (mm) to a percentage based on TARGET_DEPTH.
    The percentage is capped at 100%.
    """
    percent = (depth / TARGET_DEPTH) * 100.0
    return min(percent, 100.0)

def update_displayed_percentage(new_percent, current_display):
    """
    Update the displayed water level percentage.
    - If the new percentage is lower, update immediately.
    - If it is higher, update only if the increase is at least REFILL_THRESHOLD.
    """
    if new_percent < current_display:
        return new_percent
    elif new_percent - current_display >= REFILL_THRESHOLD:
        return new_percent
    else:
        return current_display

def write_current_percentage(percent):
    """Write the current water percentage to a file (read by the website)."""
    with open(CURRENT_WATER_FILE, "w") as f:
        f.write(f"{percent:.1f}")

def record_water_cycle():
    """
    Collect water sensor readings every 5 seconds for a 5-minute cycle,
    compute the average water percentage over the cycle,
    and update the website with the computed average.
    """
    readings = []
    for _ in range(NUM_SAMPLES):
        depth = get_depth()
        percent = convert_to_percentage(depth)
        readings.append(percent)
        time.sleep(SAMPLE_INTERVAL)

    # Compute the 5-minute average.
    avg_percent = sum(readings) / len(readings)
    # Write the computed average directly to the website.
    write_current_percentage(avg_percent)
    # Also return the lowest reading (if needed for logging)
    cycle_low = min(readings)
    return avg_percent, cycle_low

# Allow water_level.py to be run on its own for testing/monitoring:
if __name__ == '__main__':
    csv_filename = "ph_hourly.csv"
    last_csv_time = time.time()
    while True:
        avg, low = record_water_cycle()
        print(f"Cycle complete: Average Water Level = {avg:.1f}%, Lowest = {low:.1f}%")
        if time.time() - last_csv_time >= 3600:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(csv_filename, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([timestamp, "", f"{low:.1f}"])
            last_csv_time = time.time()
