import time
from DFRobot_ADS1115 import ADS1115

TARGET_DEPTH = 227.0    # full tank (mm)
SAMPLE_INTERVAL = 5     # sample time for average
CYCLE_DURATION = 300    # total time cycle for average
NUM_SAMPLES = int(CYCLE_DURATION / SAMPLE_INTERVAL) # average for stable result

# Required variables from DFRobot
RESISTOR = 120.0       # ohms
CURRENT_INIT = 3.15    # mA, calibrated current (no water)
RANGE = 5000           # mm (used in depth calculation)

# Create the ADS1115 (ADC) instance to access the sensor
ads1115 = ADS1115()
ads1115.setAddr_ADS1115(0x48)
ads1115.setGain(0x00)  # 6.144V range

def get_depth():
    """
    Read sensor voltage and calculate the depth in mm.
    """
    voltage_data = ads1115.readVoltage(1)  # using channel 1
    voltage_mv = voltage_data['r']
    current_ma = voltage_mv / RESISTOR
    depth = max(0, (current_ma - CURRENT_INIT) * (RANGE / 16.0)) # depth calculation, 

    return depth

def record_water_cycle():
    """
    Collect water level readings every 5 seconds for 5 minutes,
    return the lowest reading.
    """
    readings = []
    # Collect samples until the cycle duration is reached
    for _ in range(NUM_SAMPLES):
        depth = get_depth()
        # Convert depth to percentage
        percent = min((depth / TARGET_DEPTH) * 100.0, 100.0)
        readings.append(percent)
        
        time.sleep(SAMPLE_INTERVAL)

    cycle_low = min(readings) # lowest reading

    return cycle_low
