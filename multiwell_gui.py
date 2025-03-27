###################################################
# LED Illumination System for Multiwell Plates GUI
###################################################

######################################
# Imports
######################################
import argparse
from itertools import chain
import serial
import sys
import time
import jsons

import numpy as np

######################################
# Global Constants
######################################
GUI_VERSION = 1.0

LED_CNT = 12
COL_CNT = 4
ROW_CNT = 3
assert COL_CNT*ROW_CNT==LED_CNT, 'Invalid LED array configuration'

######################################
# Classes
######################################
class LedSettings:
    def __init__(self, brightness=0, hue=0):
        self.brightness = brightness
        self.hue = hue
    def reset(self):
        self.brightness = 0
        self.hue = 0
    def __repr__(self):
        return f"LedSettings(brightness={self.brightness}, hue={self.hue})"

class Led:
    def __init__(self, index):
        self.index = index
        self.settings = LedSettings()
    def reset(self):
        self.settings.reset()
    def get_settings(self):
        return self.settings
    def __repr__(self):
        return f"Led(index={self.index}, settings={self.settings})"

class LedArray:
    def __init__(self, rows=ROW_CNT, cols=COL_CNT, led_count=LED_CNT):
        self.array = [Led(i) for i in range(led_count)]
    def reset_all(self):
        for led in self.array:
            led.reset()
    def get_led(self, index):
        if 0 <= index < len(self.array):
            return self.array[index]
        else:
            return None
    def set_led_settings(self, index, settings):
      targetLed = self.get_led(index)
      if targetLed:
        targetLed.settings = settings
    def get_tx_array(self):
        ret_dict = dict()
        for i,led in enumerate(self.array):
            ret_dict[i] = led.settings
        return ret_dict
    def __repr__(self):
      return f"LedArray(led_count={len(self.array)})"

######################################
# Global Variables
######################################
mLedArray = LedArray()

######################################
# Command Line Arguments
######################################
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=str, help='COM port of Arduino ex: COM3', default=None)
parser.add_argument('--gui_only', action='store_true',help='Disables connecting to Arduino for GUI development.')
args = parser.parse_args()

######################################
# Functions
######################################

######################################
# Main
######################################
def main():
    print('LED Illumination System for Multiwell Plates GUI')
    print(f'Version: {GUI_VERSION}')

    # Check variables
    if not args.gui_only:
        arduino_port = args.port
        if arduino_port is None:
            arduino_port = input("Enter COM port: ")

    while(True):

        if not args.gui_only:
            # Open Serial port to Arduino
            try:
                arduino = serial.Serial(arduino_port, 9600, timeout=1)
            except serial.serialutil.SerialException:
                print('COM port not found. Verify COM number or use --help for formatting')
                sys.exit(-1)
            time.sleep(2)  # Allow time for the serial port to initialize

        # lightNumber = int(input("Light Number: "))
        # brightnessNumber = int(input("Brightness: "))
        # hueNumbers = 0

        # lightObj = lightDict[lightNumber]
        # lightObj.brightness = brightnessNumber
        # lightObj.hue = hueNumbers

        json_dump = jsons.dumps(mLedArray.get_tx_array()).encode()

        if not args.gui_only:
            try:
                arduino.write(json_dump)  # Send data to Arduino
                time.sleep(2)

                if arduino.in_waiting > 0 :
                    received_data = arduino.readline().decode().rstrip()
                    print(f"From Arduino: {received_data}")

            except ValueError:
                print("i bet you didn't give me numbers, bitch")
            arduino.close()
        else:
            print(f'json_dump: {json_dump}')
        sys.exit()

if __name__=="__main__":
    main()




