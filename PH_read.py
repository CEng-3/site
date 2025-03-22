import sys
import time
from DFRobot_ADS1115 import ADS1115

class DFRobot_PH():
	def begin(self):
		''' Open & read data from .txt file and create variables '''
		global acidVoltage
		global neutralVoltage
		
		try:
			with open('static/data/phdata.txt','r') as f:
				neutralVoltageLine = f.readline()
				neutralVoltageLine = neutralVoltageLine.strip('neutralVoltage=')
				neutralVoltage    = float(neutralVoltageLine)
				
				acidVoltageLine    = f.readline()
				acidVoltageLine    = acidVoltageLine.strip('acidVoltage=')
				acidVoltage       = float(acidVoltageLine)
		except :
			print ("phdata.txt ERROR ! Please verify file contains... \nneutralVoltage=2013.0 \nacidVoltage=1801.0")
			sys.exit(1)
			
	def read_PH(self,voltage):
		''' Convert voltage to PH '''
		global acidVoltage
		global neutralVoltage
		
		# Calculates how much the PH changes per unit change in the scaled voltage
		slope     = (7.0-4.0)/((neutralVoltage-1500.0)/3.0 - (acidVoltage-1500.0)/3.0)
		# voltage corresponds to the neutral buffer solution
		intercept = 7.0 - slope*(neutralVoltage-1500.0)/3.0
		# Ph result calculated based on the raw volatge and the calibration config
		phValue  = slope*(voltage-1500.0)/3.0+intercept
		round(phValue,2)
		
		return phValue
	
	
def read_ph():
    ADS1115_REG_CONFIG_PGA_6_144V        = 0x00 # 6.144V range = Gain 2/3
    ads1115 = ADS1115()
    ph      = DFRobot_PH()
    
    ph.begin()
    #Set the IIC address
    ads1115.setAddr_ADS1115(0x48)
    #Sets the gain and input voltage range.
    ads1115.setGain(ADS1115_REG_CONFIG_PGA_6_144V)
    #Get the Digital Value of Analog of selected channel
    adc0 = ads1115.readVoltage(0)
    #Convert voltage to PH with temperature compensation
    PH = ph.read_PH(adc0['r'])
    
    ph_value = float("%.1f" % PH) 
    return ph_value
