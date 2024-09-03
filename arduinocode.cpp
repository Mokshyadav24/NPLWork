#include <ESP8266WiFi.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads1; // Address 0x48
Adafruit_ADS1115 ads2; // Address 0x49

const char* ssid = "KRC-IST128";
const char* password = "128istrc@";
const char* server = "172.16.18.25";  // XAMPP server's IP address
int serverPort = 80;

WiFiClient client;

unsigned long measureStartTime;
bool measuring = false;

void setup() {
  Serial.begin(9600);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  if (!ads1.begin(0x48)) {
    Serial.println("Failed to initialize ADS1.");
    while (1);
  }
  if (!ads2.begin(0x49)) {
    Serial.println("Failed to initialize ADS2.");
    while (1);
  }

  measureStartTime = millis();
  measuring = true;
}

void loop() {
  static int16_t minAdc[8] = {INT16_MAX, INT16_MAX, INT16_MAX, INT16_MAX, INT16_MAX, INT16_MAX, INT16_MAX, INT16_MAX};
  unsigned long currentTime = millis();

  if (measuring) {
    // Measure ADC values for 50 seconds
    if (currentTime - measureStartTime < 50000) {
      for (int channel = 0; channel < 8; channel++) {
        int16_t adcValue;
        if (channel < 4) {
          adcValue = ads1.readADC_SingleEnded(channel);
        } else {
          adcValue = ads2.readADC_SingleEnded(channel - 4);
        }
        if (adcValue < minAdc[channel]) {
          minAdc[channel] = adcValue;
        }
      }
    } else {
      measuring = false; // Stop measuring after 50 seconds
      measureStartTime = currentTime; // Reset timer for sending data
    }
  } else {
    // Pause for 10 seconds to send data
    if (currentTime - measureStartTime < 10000) {
      // Do nothing, just wait
    } else {
      float voltage[8];
      for (int i = 0; i < 8; i++) {
        voltage[i] = (minAdc[i] == INT16_MAX) ? 0.0 : abs(minAdc[i]) * 0.1875;
      }
      float X1 = voltage[0], X2 = voltage[1], Y1 = voltage[2], Y2 = voltage[3];
      float D1 = voltage[4], D2 = voltage[5], Z1 = voltage[6], Z2 = voltage[7];

      Serial.println("Attempting to connect to server...");
      if (client.connect(server, serverPort)) {
        Serial.println("Connected to server");

        String url = "/phpfiles/save_data.php";
        String postData = "X1=" + String(X1) + "&X2=" + String(X2) +
                          "&Y1=" + String(Y1) + "&Y2=" + String(Y2) +
                          "&D1=" + String(D1) + "&D2=" + String(D2) +
                          "&Z1=" + String(Z1) + "&Z2=" + String(Z2);

        client.print("POST ");
        client.print(url);
        client.println(" HTTP/1.1");
        client.print("Host: ");
        client.println(server);
        client.println("Content-Type: application/x-www-form-urlencoded");
        client.print("Content-Length: ");
        client.println(postData.length());
        client.println();
        client.println(postData);

        while (client.connected() || client.available()) {
          if (client.available()) {
            String line = client.readStringUntil('\n');
            Serial.println(line);
          }
        }
        client.stop();
        Serial.println("Data sent");

        // Reset minAdc array for the next measurement cycle
        for (int i = 0; i < 8; i++) {
          minAdc[i] = INT16_MAX;
        }

        // After sending data, start measuring again
        measuring = true;
        measureStartTime = currentTime;
      } else {
        Serial.println("Connection to server failed, retrying in 1 second...");
        client.stop();
        delay(1000);
      }
    }
  }
}