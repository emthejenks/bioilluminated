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
import tkinter as tk
from tkinter import ttk
import jsons

######################################
# Global Constants
######################################
GUI_VERSION = 1.0
GUI_INFO_STR = f'LED Illumination System for Multiwell Plates GUI\nVersion: {GUI_VERSION}'

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
    def get_led_settings(self, index):
        if index >= len(self.array):
            return None
        return self.array[index].get_settings()
    def set_led_settings(self, index, settings):
        targetLed = self.get_led(index)
        if targetLed:
            targetLed.settings = settings
    def get_tx_array(self):
        ret_dict = dict()
        for i,led in enumerate(self.array):
            ret_dict[i] = led.settings
        return ret_dict
    def updt_from_entry_array(self, updt_array):
        for idx, up in enumerate(updt_array):
            print(f'{idx}: {up.get()}')
            sets = self.get_led_settings(idx)
            sets.brightness = up.get()
            self.set_led_settings(idx, sets )
    def __repr__(self):
      return f"LedArray(led_count={len(self.array)})"

######################################
# Command Line Arguments
######################################
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=str, help='COM port of Arduino ex: COM3', default=None)
parser.add_argument('--gui_only', action='store_true',help='Disables connecting to Arduino for GUI development.')
args = parser.parse_args()

######################################
# Global Variables
######################################
mLedArray = LedArray()

if not args.gui_only:
    mArduinoPort = args.port
    if mArduinoPort  is None:
        mArduinoPort  = input("Enter COM port: ")

######################################
# Functions
######################################
def updateLEDs( updates ):
    mLedArray.updt_from_entry_array(updates)

    if not args.gui_only:
        # Open Serial port to Arduino
        try:
            arduino = serial.Serial(mArduinoPort, 9600, timeout=1)
        except serial.serialutil.SerialException:
            print('COM port not found. Verify COM number or use --help for formatting')
            sys.exit(-1)
        time.sleep(2)  # Allow time for the serial port to initialize

    json_dump = jsons.dumps(mLedArray.get_tx_array()).encode()

    if not args.gui_only:
        try:
            arduino.write(json_dump)  # Send data to Arduino
            time.sleep(2)

            if arduino.in_waiting > 0 :
                received_data = arduino.readline().decode().rstrip()
                print(f"From Arduino: {received_data}")

        except ValueError:
            print("No values from Arduino")
        arduino.close()
    else:
        print(f'json_dump: {json_dump}')

######################################
# Main
######################################
def main():
    print(GUI_INFO_STR)

    window = tk.Tk()
    window.title(GUI_INFO_STR)

    # Modern styling
    style = ttk.Style()
    style.theme_use("clam")

    # Set background color for the main window
    window.configure(bg="#f0f0f0")

    # Configure root window to expand
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    # Create a frame to hold the entries and labels
    frame = ttk.Frame(window, padding="20")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    frame.configure(borderwidth=2, relief="groove")

    # LED labels and entry fields
    led_labels = [f"LED {i+1}" for i in range(LED_CNT)]
    entries = []

    for i in range(LED_CNT):
        col = i % COL_CNT
        row = i // COL_CNT * 2

        label = ttk.Label(frame, text=led_labels[i])
        label.grid(row=row, column=col, padx=5, pady=5)

        entry = ttk.Entry(frame, width=10)
        entry.insert(0, 0)
        entry.grid(row=row + 1, column=col, padx=5, pady=5)
        entries.append(entry)

    # Corrected button command
    button = ttk.Button(frame, text="Update LEDs", command=lambda: updateLEDs(entries))
    button.grid(row=ROW_CNT * 2 + 1, column=0, columnspan=COL_CNT, pady=20)

    for i in range(COL_CNT):
        frame.columnconfigure(i, weight=1)
    for i in range(ROW_CNT * 2 + 1):
        frame.rowconfigure(i, weight=1)

    window.mainloop()

if __name__=="__main__":
    main()




