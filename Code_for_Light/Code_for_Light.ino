#include <Adafruit_NeoPixel.h>

// Pin to use to send signals to WS2812B
#define LED_PIN 6

// Number of WS2812B LEDs attached to the Arduino
#define LED_COUNT 12

// Setting up the NeoPixel library
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();           // Initialize NeoPixel object
  strip.setBrightness(255); // Set BRIGHTNESS to about 4% (max = 255)
}

void loop() {
  strip.clear(); // Set all pixel colors to 'off'

  // The first NeoPixel in a strand is #0, second is 1, all the way up
  // to the count of pixels minus one.
  for(int i=0; i<LED_COUNT; i++) {
    // Set the i-th LED to pure green:
    strip.setPixelColor(i, 0, 255, 0);
  
    strip.show();   // Send the updated pixel colors to the hardware.
  1
    delay(500); // Pause before next pass through loop
  }
}
