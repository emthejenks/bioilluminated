import serial
import time
import jsons





##while True:
##    arduino = serial.Serial('COM3', 9600, timeout=1) # timeout added.
##    time.sleep(2)  # Allow time for the serial port to initialize
##    data = input("Enter data to send: ")
##    
##    arduino.write(data.encode())  # Send data to Arduino
##    time.sleep(2) # small delay to prevent issues.
##    print('done waiting')
##    #Optional read from the arduino.
##    if arduino.in_waiting > 0 :
##        received_data = arduino.readline().decode().rstrip()
##        print(f"From Arduino: {received_data}")
##        
##
##    arduino.close()



class light:
    def __init__(self, brightness, hue):
       self.brightness = brightness
       self.hue = hue

lightDict = dict()
for i in range(12):
    lightDict[i] = light(0,0)

while(True):
    arduino = serial.Serial('COM3', 9600, timeout=1) # timeout added.
    time.sleep(2)  # Allow time for the serial port to initialize

    try:
        lightNumber = int(input("Gimmie a light number"))
        brightnessNumber = int(input("Gimmie a brightness"))
        #hueNumbers = int(input("Gimmie a hue"))
        hueNumbers = 0

        lightObj = lightDict[lightNumber]
        lightObj.brightness = brightnessNumber
        lightObj.hue = hueNumbers

                         
        arduino.write((jsons.dumps(lightDict)).encode())  # Send data to Arduino
        time.sleep(2)

        if arduino.in_waiting > 0 :
            received_data = arduino.readline().decode().rstrip()
            print(f"From Arduino: {received_data}")

                      
    except ValueError:
        print("i bet you didn't give me numbers, bitch")
    arduino.close()
