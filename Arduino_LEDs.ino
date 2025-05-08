#include <Adafruit_NeoPixel.h>
#include <Arduino.h>
#include <ArduinoJson.h>


// Pin to use to send signals to WS2812B
#define LED_PIN 6

// Number of WS2812B LEDs attached to the Arduino
#define LED_COUNT 12

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(9600); // Initialize serial communication at 9600 baud
  strip.begin();           // Initialize NeoPixel object
  strip.setBrightness(255); // Set BRIGHTNESS to about 4% (max = 255);
}


void loop() {
 
 StaticJsonDocument<512> MyData; //allocate memory for JSON parsing
 
  
  while (Serial.available()>0) { // Check if data is available
    String receivedByte = Serial.readString(); // Read the byte
    DeserializationError err1=deserializeJson(MyData,receivedByte);
    if(err1){
      Serial.print("JSON deserialization failed:");
      Serial.println(err1.c_str());
      return;
    }
    
    for(int i=0; i<LED_COUNT; i++) {
      int brightness=MyData[String(i)]["brightness"];
      int hue=MyData[String(i)]["hue"];
      switch(hue){
        case 0:
             // Set the i-th LED to pure green:
            strip.setPixelColor(i, 0, brightness, 0);
            break;
        case 1:
             // Set the i-th LED to pure red:
            strip.setPixelColor(i, brightness, 0, 0);
            break;
        case 2:
             // Set the i-th LED to pure blue:
            strip.setPixelColor(i, 0, 0, brightness);
            break;
        default:
            strip.setPixelColor(i, 0,0,0);    
            break;
      }
   
      
  }
   strip.show();
  }

  }