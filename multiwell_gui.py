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

VIEW_OPTIONS = ["Grid", "Column", "Row", "Uniform"]

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
    def __init__(self, index, parent_array):
        self.index = index
        self.parent_array = parent_array
        self.settings = LedSettings()
    def reset(self):
        self.settings.reset()
    def get_settings(self):
        return self.settings
    def update_brightness(self, br):
        self.settings.brightness = br
    def get_row(self):
        return self.index // self.parent_array.cols
    def get_col(self):
        return self.index % self.parent_array.cols
    def __repr__(self):
        return f"Led(index={self.index}, settings={self.settings})"

class LedArray:
    def __init__(self, rows=ROW_CNT, cols=COL_CNT, led_count=LED_CNT):
        self.array = [Led(i, self) for i in range(led_count)]
        self.rows = rows
        self.cols = cols
        self.led_count = led_count
    def reset_all(self):
        for led in self.array:
            led.reset()
    def get_col_idxs(self, col_num):
        col_idxs = []
        for idx in range(self.led_count):
            if self.get_led(idx).get_col() == col_num:
                col_idxs.append(idx)
        return col_idxs
    def get_row_idxs(self, row_num):
        row_idxs = []
        for idx in range(self.led_count):
            if self.get_led(idx).get_row() == row_num:
                row_idxs.append(idx)
        return row_idxs
    def get_led(self, index):
        assert index >= 0 and index < len(self.array), "Invalid LED index"
        return self.array[index]
    def get_led_settings(self, index):
        return self.get_led(index).get_settings()
    def set_led_settings(self, index, settings):
        self.get_led(index).settings = settings
    def get_tx_array(self):
        ret_dict = dict()
        for i,led in enumerate(self.array):
            ret_dict[i] = led.settings
        return ret_dict
    def updt_grid(self, updt_array):
        for idx, up in enumerate(updt_array):
            self.get_led(idx).update_brightness(up.get())
    def updt_cols(self, updt_array):
        for idx, up in enumerate(updt_array):
            led_idxs = self.get_col_idxs(idx)
            for led in led_idxs:
                self.get_led(led).update_brightness(up.get())
    def updt_rows(self, updt_array):
        for idx, up in enumerate(updt_array):
            led_idxs = self.get_row_idxs(idx)
            for led in led_idxs:
                self.get_led(led).update_brightness(up.get())
    def updt_all(self, updt_array):
        for led in self.array:
            led.update_brightness(updt_array[0].get())
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

mFrame = None
mEntries = []
mButton = None
mViewMode = "Grid"

mUiRowCnt = ROW_CNT
mUiColCnt = COL_CNT

######################################
# Functions
######################################
def switch_view(vm):
    global mUiRowCnt, mUiColCnt, mViewMode
    mViewMode = vm
    if mViewMode == "Grid":
        mUiColCnt = COL_CNT
        mUiRowCnt = ROW_CNT
    elif mViewMode == "Column":
        mUiColCnt = COL_CNT
        mUiRowCnt = 1
    elif mViewMode == "Row":
        mUiColCnt = 1
        mUiRowCnt = ROW_CNT
    elif mViewMode == "Uniform":
        mUiColCnt = 1
        mUiRowCnt = 1
    redraw_ui()

def get_view_mode_label_text(i):
    if mViewMode == "Grid":
        return f"LED {i+1}"
    elif mViewMode == "Column":
        return f"Column {i+1}"
    elif mViewMode == "Row":
        return f"Row {i+1}"
    elif mViewMode == "Uniform":
        return "All LEDs"

def redraw_ui():
    global mFrame, mEntries, mButton, mUiRowCnt, mUiColCnt, mViewMode, VIEW_OPTIONS

    # Destroy old widgets
    for widget in mFrame.winfo_children():
        widget.destroy()

    # Recreate LED labels and entry fields
    mEntries = []
    for i in range(mUiColCnt*mUiRowCnt):
        col = i % mUiColCnt
        row = i // mUiColCnt * 2

        label = ttk.Label(mFrame, text=get_view_mode_label_text(i))
        label.grid(row=row, column=col, padx=5, pady=5)

        entry = ttk.Entry(mFrame, width=10)
        entry.insert(0, 0)
        entry.grid(row=row + 1, column=col, padx=5, pady=5)
        mEntries.append(entry)

    # Recreate button
    mButton = ttk.Button(mFrame, text="Update LEDs", command=lambda: updateLEDs(mEntries))
    mButton.grid(row=mUiRowCnt * 2 + 1, column=0, columnspan=mUiColCnt, pady=20)

    # Reconfigure grid
    for i in range(mUiColCnt):
        mFrame.columnconfigure(i, weight=1)
    for i in range(mUiRowCnt * 2 + 1):
        mFrame.rowconfigure(i, weight=1)

    # Dropdown menu for view mode
    view_var = tk.StringVar()
    view_var.set(mViewMode)  # Default view

    # Corrected OptionMenu command to use a lambda function
    view_menu = ttk.OptionMenu(mFrame, view_var, view_var.get(), *VIEW_OPTIONS, command=lambda value: switch_view(value))
    view_menu.grid(row=0, column=mUiColCnt, padx=10, pady=10, sticky=tk.NE)

def updateLEDs( updates ):
    if mViewMode == "Grid":
        mLedArray.updt_grid(updates)
    elif mViewMode == "Column":
        mLedArray.updt_cols(updates)
    elif mViewMode == "Row":
        mLedArray.updt_rows(updates)
    elif mViewMode == "Uniform":
        mLedArray.updt_all(updates)
    else:
        assert False, "Invalid view mode"

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
    global mFrame

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
    mFrame = ttk.Frame(window, padding="20")
    mFrame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    mFrame.configure(borderwidth=2, relief="groove")

    # Initial UI setup
    redraw_ui()

    window.mainloop()

if __name__=="__main__":
    main()




