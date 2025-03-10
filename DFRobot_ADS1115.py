'''!
Interfaces with DFRobot ADS1115 analog-to-digital converter using the I2C bus on the raspberry pi.
The ADS1115 writes values to the register (memory location on the ADS1115) over the I2C bus.

It uses the script to build the correct configuration...
    - input channel (0-3)
    - voltage range (gain)
    - conversion mode and data rate
    
Converts the analog voltage into a digital number by reading 2 bytes from the ADS1115 using
a 16-bit resolution (0 - 65,535) and depedning on the gain setting determines the voltage range when
it is changed from a raw digital value to voltage value.
'''

import smbus
import time

# Get I2C bus
bus = smbus.SMBus(1)

# I2C address of the device
ADS1115_IIC_ADDRESS0 = 0x48
ADS1115_IIC_ADDRESS1 = 0x49

# ADS1115 Register Map
ADS1115_REG_POINTER_CONVERT = 0x00  # Conversion register
ADS1115_REG_POINTER_CONFIG = 0x01   # Configuration register
ADS1115_REG_POINTER_LOWTHRESH = 0x02  # Lo_thresh register
ADS1115_REG_POINTER_HITHRESH = 0x03  # Hi_thresh register

# ADS1115 Configuration Register
ADS1115_REG_CONFIG_OS_NOEFFECT = 0x00  # No effect
ADS1115_REG_CONFIG_OS_SINGLE = 0x80    # Begin a single conversion
ADS1115_REG_CONFIG_MUX_DIFF_0_1 = 0x00  # Differential P = AIN0, N = AIN1 (default)
ADS1115_REG_CONFIG_MUX_DIFF_0_3 = 0x10  # Differential P = AIN0, N = AIN3
ADS1115_REG_CONFIG_MUX_DIFF_1_3 = 0x20  # Differential P = AIN1, N = AIN3
ADS1115_REG_CONFIG_MUX_DIFF_2_3 = 0x30  # Differential P = AIN2, N = AIN3
ADS1115_REG_CONFIG_MUX_SINGLE_0 = 0x40  # Single-ended P = AIN0, N = GND
ADS1115_REG_CONFIG_MUX_SINGLE_1 = 0x50  # Single-ended P = AIN1, N = GND
ADS1115_REG_CONFIG_MUX_SINGLE_2 = 0x60  # Single-ended P = AIN2, N = GND
ADS1115_REG_CONFIG_MUX_SINGLE_3 = 0x70  # Single-ended P = AIN3, N = GND
ADS1115_REG_CONFIG_PGA_6_144V = 0x00    # +/-6.144V range = Gain 2/3
ADS1115_REG_CONFIG_PGA_4_096V = 0x02    # +/-4.096V range = Gain 1
ADS1115_REG_CONFIG_PGA_2_048V = 0x04    # +/-2.048V range = Gain 2 (default)
ADS1115_REG_CONFIG_PGA_1_024V = 0x06    # +/-1.024V range = Gain 4
ADS1115_REG_CONFIG_PGA_0_512V = 0x08    # +/-0.512V range = Gain 8
ADS1115_REG_CONFIG_PGA_0_256V = 0x0A    # +/-0.256V range = Gain 16
ADS1115_REG_CONFIG_MODE_CONTIN = 0x00    # Continuous conversion mode
ADS1115_REG_CONFIG_MODE_SINGLE = 0x01   # Power-down single-shot mode (default)
ADS1115_REG_CONFIG_DR_8SPS = 0x00        # 8 samples per second
ADS1115_REG_CONFIG_DR_16SPS = 0x20       # 16 samples per second
ADS1115_REG_CONFIG_DR_32SPS = 0x40       # 32 samples per second
ADS1115_REG_CONFIG_DR_64SPS = 0x60       # 64 samples per second
ADS1115_REG_CONFIG_DR_128SPS = 0x80      # 128 samples per second (default)
ADS1115_REG_CONFIG_DR_250SPS = 0xA0      # 250 samples per second
ADS1115_REG_CONFIG_DR_475SPS = 0xC0      # 475 samples per second
ADS1115_REG_CONFIG_DR_860SPS = 0xE0      # 860 samples per second
ADS1115_REG_CONFIG_CMODE_TRAD = 0x00     # Traditional comparator with hysteresis (default)
ADS1115_REG_CONFIG_CMODE_WINDOW = 0x10   # Window comparator
ADS1115_REG_CONFIG_CPOL_ACTVLOW = 0x00   # ALERT/RDY pin is low when active (default)
ADS1115_REG_CONFIG_CPOL_ACTVHI = 0x08    # ALERT/RDY pin is high when active
ADS1115_REG_CONFIG_CLAT_NONLAT = 0x00    # Non-latching comparator (default)
ADS1115_REG_CONFIG_CLAT_LATCH = 0x04     # Latching comparator
ADS1115_REG_CONFIG_CQUE_1CONV = 0x00     # Assert ALERT/RDY after one conversions
ADS1115_REG_CONFIG_CQUE_2CONV = 0x01     # Assert ALERT/RDY after two conversions
ADS1115_REG_CONFIG_CQUE_4CONV = 0x02     # Assert ALERT/RDY after four conversions
ADS1115_REG_CONFIG_CQUE_NONE = 0x03      # Disable the comparator and put ALERT/RDY in high state (default)

mygain = 0x02                    # Default gain setting
coefficient = 0.125              # Conversion factor for the default gain
addr_G = ADS1115_IIC_ADDRESS0    # Default I2C address for the ADS1115


class ADS1115():
    def setGain(self, gain):
        ''' Set ADC gain and conversion coefficient based on the gain value '''
        global mygain
        global coefficient

        mygain = gain
        if mygain == ADS1115_REG_CONFIG_PGA_6_144V:
            coefficient = 0.1875
        elif mygain == ADS1115_REG_CONFIG_PGA_4_096V:
            coefficient = 0.125
        elif mygain == ADS1115_REG_CONFIG_PGA_2_048V:
            coefficient = 0.0625
        elif mygain == ADS1115_REG_CONFIG_PGA_1_024V:
            coefficient = 0.03125
        elif mygain == ADS1115_REG_CONFIG_PGA_0_512V:
            coefficient = 0.015625
        elif mygain == ADS1115_REG_CONFIG_PGA_0_256V:
            coefficient = 0.0078125
        else:
            coefficient = 0.125

    def setAddr_ADS1115(self, addr):
        ''' Set I2C address of the ADS1115 '''
        global addr_G
        addr_G = addr

    def setChannel(self, channel):
        ''' Set the ADC input channel for measurement (0-3) '''
        global mygain

        self.channel = channel
        if self.channel > 3:
            self.channel = 0
        return self.channel

    def setSingle(self):
        ''' Configure ADS1115 for conversion on the selected channel '''
        global addr_G

        if self.channel == 0:
            CONFIG_REG = [ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_0 | mygain | ADS1115_REG_CONFIG_MODE_CONTIN,
                           ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif self.channel == 1:
            CONFIG_REG = [ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_1 | mygain | ADS1115_REG_CONFIG_MODE_CONTIN,
                           ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif self.channel == 2:
            CONFIG_REG = [ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_2 | mygain | ADS1115_REG_CONFIG_MODE_CONTIN,
                           ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        elif self.channel == 3:
            CONFIG_REG = [ADS1115_REG_CONFIG_OS_SINGLE | ADS1115_REG_CONFIG_MUX_SINGLE_3 | mygain | ADS1115_REG_CONFIG_MODE_CONTIN,
                           ADS1115_REG_CONFIG_DR_128SPS | ADS1115_REG_CONFIG_CQUE_NONE]
        # Write configuration to the ADS1115
        bus.write_i2c_block_data(addr_G, ADS1115_REG_POINTER_CONFIG, CONFIG_REG)

    def readValue(self):
        """ Read data from conversion register and convert to voltage """
        global coefficient
        global addr_G

        data = bus.read_i2c_block_data(addr_G, ADS1115_REG_POINTER_CONVERT, 2)
        raw_adc = data[0] * 256 + data[1]

        if raw_adc > 32767:
            raw_adc -= 65535
        raw_adc = int(float(raw_adc) * coefficient)

        return {'r': raw_adc}

    def readVoltage(self, channel):
        ''' Quick method to setup and read voltage from a channel '''
        self.setChannel(channel)
        self.setSingle()
        time.sleep(0.1)
        return self.readValue()