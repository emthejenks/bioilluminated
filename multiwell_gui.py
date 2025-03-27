###################################################
# LED Illumination System for Multiwell Plates GUI
###################################################

######################################
# Imports
######################################
import argparse
import serial
import sys
import time
import jsons

######################################
# Global Constants
######################################
GUI_VERSION = 1.0

######################################
# Command Line Arguments
######################################
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=str, help='COM port of Arduino ex: COM3', default=None)
parser.add_argument('--gui_only', action='store_true',help='Disables connecting to Arduino for GUI development.')
args = parser.parse_args()

######################################
# Classes
######################################
class light:
    def __init__(self, brightness, hue):
       self.brightness = brightness
       self.hue = hue

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

    lightDict = dict()
    for i in range(12):
        lightDict[i] = light(0,0)

    while(True):

        if not args.gui_only:
            # Open Serial port to Arduino
            try:
                arduino = serial.Serial(arduino_port, 9600, timeout=1)
            except serial.serialutil.SerialException:
                print('COM port not found. Verify COM number or use --help for formatting')
                sys.exit(-1)
            time.sleep(2)  # Allow time for the serial port to initialize

        lightNumber = int(input("Gimmie a light number"))
        brightnessNumber = int(input("Gimmie a brightness"))
        hueNumbers = 0

        lightObj = lightDict[lightNumber]
        lightObj.brightness = brightnessNumber
        lightObj.hue = hueNumbers

        json_dump = jsons.dumps(lightDict).encode()

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

if __name__=="__main__":
    main()




