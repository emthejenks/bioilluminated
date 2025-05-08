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
import json
from serial.tools import list_ports

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
        try:
            # Convert the input to an integer
            br = int(br)
        except ValueError:
            # Handle invalid input by setting brightness to 0
            print(f"Invalid brightness value: {br}. Setting to 0.")
            br = 0
        #Check range
        if br < 0:
            br=0
        elif br > 255:
            br=255
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
    def to_json_dict(self):
        """
        Converts the LED array's settings into a JSON-serializable dictionary.
        """
        return {
            i: {
                "brightness": led.settings.brightness,
                "hue": led.settings.hue
            }
            for i, led in enumerate(self.array)
        }
    def __repr__(self):
      return f"LedArray(led_count={len(self.array)})"

######################################
# Command Line Arguments
######################################
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=str, help='COM port of Arduino ex: COM3', default=None)
parser.add_argument('--gui_only', action='store_true', help='Disables connecting to Arduino for GUI development.')
args = parser.parse_args()

######################################
# Global Variables
######################################
mLedArray = LedArray()

# Remove user prompt for COM port
mArduinoPort = args.port if not args.gui_only else None

mFrame = None
mEntries = []
mButton = None
mViewMode = "Grid"

mUiRowCnt = ROW_CNT
mUiColCnt = COL_CNT
mColorVar = None

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
    global mFrame, mEntries, mButton, mUiRowCnt, mUiColCnt, mViewMode, VIEW_OPTIONS, mColorVar

    # Destroy old widgets
    for widget in mFrame.winfo_children():
        widget.destroy()

    # Remove color statement and keep value range text
    range_label = ttk.Label(mFrame, text="Enter brightness between 0 and 100", font=("Arial", 10), foreground="gray")
    range_label.grid(row=0, column=0, columnspan=mUiColCnt, pady=5)

    # Recreate LED labels and entry fields
    mEntries = []
    for i in range(mUiColCnt * mUiRowCnt):
        col = i % mUiColCnt
        row = i // mUiColCnt * 2 + 1  # Adjust row to account for the added label

        label = ttk.Label(mFrame, text=get_view_mode_label_text(i))
        label.grid(row=row, column=col, padx=5, pady=5)

        entry = ttk.Entry(mFrame, width=10)
        entry.insert(0, 0)
        entry.grid(row=row + 1, column=col, padx=5, pady=5)
        mEntries.append(entry)

    # Recreate button
    mButton = ttk.Button(mFrame, text="Update LEDs", command=lambda: updateLEDs(mEntries))
    mButton.grid(row=mUiRowCnt * 2 + 1, column=0, columnspan=2, padx=5, pady=20, sticky=tk.EW)

    # Recreate Timers Button
    add_timer_button = ttk.Button(mFrame, text="Add Timer", command=lambda: add_timer(mEntries))
    add_timer_button.grid(row=mUiRowCnt * 2 + 1, column=2, columnspan=2, padx=5, pady=20, sticky=tk.EW)

    # Reconfigure grid
    for i in range(mUiColCnt):
        mFrame.columnconfigure(i, weight=1)
    for i in range(mUiRowCnt * 2 + 2):  # Adjust row count for added label
        mFrame.rowconfigure(i, weight=1)

    # Dropdown menu for view mode
    view_var = tk.StringVar()
    view_var.set(mViewMode)  # Default view

    view_menu = ttk.OptionMenu(mFrame, view_var, view_var.get(), *VIEW_OPTIONS, command=lambda value: switch_view(value))
    view_menu.grid(row=0, column=mUiColCnt, padx=10, pady=10, sticky=tk.NE)

    # Dropdown menu for global color selection
    color_menu = ttk.OptionMenu(
        mFrame, mColorVar, mColorVar.get(), "Green", "Red", "Blue",
        command=lambda value: update_all_hues(value)
    )
    color_menu.grid(row=1, column=mUiColCnt, padx=10, pady=10, sticky=tk.NE)

def update_all_hues(color):
    """
    Updates the hue value for all LEDs based on the selected color.
    Green corresponds to hue=0, Red corresponds to hue=1, and Blue corresponds to hue=2.
    """
    hue_value = 0 if color == "Green" else 1 if color == "Red" else 2 if color == "Blue" else 0
    for led in mLedArray.array:
        led.settings.hue = hue_value
    print(f"All LEDs hue updated to {hue_value} ({color})")

def find_arduino_serial_port():
    ports = list_ports.comports()
    for port in ports:
        if "Arduino" in port.description or "ttyACM" in port.device or "ttyUSB" in port.device:
            return port.device
    return None

def scale_brightness(value):
    """
    Scales a value from the range 0-100 to 0-255 linearly.
    """
    try:
        value = int(value)
        if value < 0:
            value = 0
        elif value > 100:
            value = 100

        # Scale linearly from 0-100 to 0-255
        return int((value / 100.0) * 255)
    except ValueError:
        print(f"Invalid brightness value: {value}. Defaulting to 0.")
        return 0

def updateLEDs(updates):
    global mViewMode, mLedArray, args  # Ensure these are accessible if used globally

    # Scale brightness values before updating LEDs
    scaled_updates = [tk.StringVar(value=str(scale_brightness(entry.get()))) for entry in updates]

    if mViewMode == "Grid":
        mLedArray.updt_grid(scaled_updates)
    elif mViewMode == "Column":
        mLedArray.updt_cols(scaled_updates)
    elif mViewMode == "Row":
        mLedArray.updt_rows(scaled_updates)
    elif mViewMode == "Uniform":
        mLedArray.updt_all(scaled_updates)
    else:
        assert False, "Invalid view mode"

    if not args.gui_only:
        # Auto-detect Arduino port
        try:
            arduino_port = find_arduino_serial_port()
            if arduino_port is None:
                print("Arduino not found. Please check the connection.")
                sys.exit(1)

            # Attempt to open serial connection
            try:
                ser = serial.Serial(arduino_port, 9600, timeout=1)
                print(f"Connected to Arduino on {arduino_port}")
                time.sleep(2)  # Allow time for the serial port to initialize

                # Send LED data over serial
                json_data = json.dumps(mLedArray.to_json_dict()) + "\n"
                print(f"Sending JSON data: {json_data}")  # Output JSON data to the terminal
                ser.write(json_data.encode('utf-8'))
                ser.flush()
                ser.close()

            except serial.SerialException as e:
                print(f"Failed to connect to {arduino_port}: {e}")
                sys.exit(1)

        except serial.serialutil.SerialException:
            print('COM port not found. Verify COM number or use --help for formatting')
            sys.exit(-1)

        
def add_timer(updates):
    def start_timer():
        try:
            hours = int(entry_hours.get()) if entry_hours.get() else 0
            minutes = int(entry_minutes.get()) if entry_minutes.get() else 0
            seconds = int(entry_seconds.get()) if entry_seconds.get() else 0

            # Convert total time to seconds
            duration = hours * 3600 + minutes * 60 + seconds

            if duration > 0:
                timer_window.destroy()  # Close input window

                # Turn on the LEDs by sending JSON data over serial
                updateLEDs(updates)

                # Start countdown
                countdown_window(duration)
            else:
                lbl_error.config(text="Please enter a positive duration.")
        except ValueError:
            lbl_error.config(text="Invalid input! Enter numbers only.")

    # Create a new window to input time
    timer_window = tk.Toplevel()
    timer_window.title("Set Timer")

    ttk.Label(timer_window, text="Enter time (hours, minutes, seconds):", font=("Arial", 12)).pack(pady=5)

    # Input fields for hours, minutes, and seconds
    frame_time = ttk.Frame(timer_window)
    frame_time.pack(pady=5)

    ttk.Label(frame_time, text="Hours:").grid(row=0, column=0, padx=5)
    entry_hours = ttk.Entry(frame_time, width=5)
    entry_hours.grid(row=0, column=1, padx=5)

    ttk.Label(frame_time, text="Minutes:").grid(row=0, column=2, padx=5)
    entry_minutes = ttk.Entry(frame_time, width=5)
    entry_minutes.grid(row=0, column=3, padx=5)

    ttk.Label(frame_time, text="Seconds:").grid(row=0, column=4, padx=5)
    entry_seconds = ttk.Entry(frame_time, width=5)
    entry_seconds.grid(row=0, column=5, padx=5)

    lbl_error = ttk.Label(timer_window, text="", foreground="red")
    lbl_error.pack()

    start_button = ttk.Button(timer_window, text="Start Timer", command=start_timer)
    start_button.pack(pady=10)

def countdown_window(duration):
    def update_countdown(time_left):
        if time_left > 0 and not timer_canceled[0]:
            # Convert time_left to hours, minutes, and seconds
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            seconds = time_left % 60
            lbl_timer.config(text=f"Time remaining: {hours:02d}:{minutes:02d}:{seconds:02d}")
            countdown_window.after(1000, update_countdown, time_left - 1)
        elif timer_canceled[0]:
            lbl_timer.config(text="Timer canceled. LEDs turned off.")
            turn_off_leds()
        else:
            lbl_timer.config(text="Time's up!")
            turn_off_leds()

    def cancel_timer():
        timer_canceled[0] = True
        lbl_timer.config(text="Timer canceled. LEDs turned off.")
        turn_off_leds()
        countdown_window.destroy()

    def turn_off_leds():
        # Set all LED brightness to 0
        for led in mLedArray.array:
            led.update_brightness(0)  # Set brightness to 0

        # Send the updated LED values
        updates = [tk.StringVar(value="0") for _ in range(len(mLedArray.array))]
        updateLEDs(updates)  # Send the updated values to the LEDs

    # Create a new window to display the countdown
    countdown_window = tk.Toplevel()
    countdown_window.title("Timer Countdown")

    # Variable to track if the timer is canceled
    timer_canceled = [False]

    # Initial display of the countdown
    hours = duration // 3600
    minutes = (duration % 3600) // 60
    seconds = duration % 60
    lbl_timer = ttk.Label(countdown_window, text=f"Time remaining: {hours:02d}:{minutes:02d}:{seconds:02d}", font=("Arial", 14))
    lbl_timer.pack(padx=20, pady=20)

    # Add "Cancel Timer" button
    cancel_button = ttk.Button(countdown_window, text="Cancel Timer", command=cancel_timer)
    cancel_button.pack(pady=10)

    # Start the countdown
    countdown_window.after(1000, update_countdown, duration)
######################################
# Main
######################################
def main():
    global mFrame, mColorVar  # Declare mColorVar as global

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

    # Initialize mColorVar after the root window is created
    mColorVar = tk.StringVar(value="Green")

    # Create a frame to hold the entries and labels
    mFrame = ttk.Frame(window, padding="20")
    mFrame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    mFrame.configure(borderwidth=2, relief="groove")

    # Initial UI setup
    redraw_ui()

    window.mainloop()

if __name__=="__main__":
    main()




