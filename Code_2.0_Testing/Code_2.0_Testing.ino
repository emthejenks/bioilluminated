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
 
 JsonDocument MyData;
 
  
  while (Serial.available()>0) { // Check if data is available
    String receivedByte = Serial.readString(); // Read the byte
    deserializeJson(MyData,receivedByte);
    int test = MyData["0"]["brightness"];
    Serial.println(test);
    
    for(int i=0; i<LED_COUNT; i++) {
      
    // Set the i-th LED to pure green:
      strip.setPixelColor(i, 0, MyData[String(i)]["brightness"], 0);
       strip.show();
    
  }
  }

  }
