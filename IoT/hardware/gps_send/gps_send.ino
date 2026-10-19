#include <WiFi.h>
#include <HTTPClient.h>
#include <TinyGPS++.h>

// WiFi credentials
const char* ssid = "Huzaifa";
const char* password = "YOUR_WIFI_PASSWORD";

// Webhook URL (given)
const char* POST_SENSOR_READING_WEBHOOK = "https://swift-cloud.ephlux.com/api-swift/ned/integration/n1EBuKoSmc?SWIFT_API_KEY=YOUR_SWIFT_KEY_POST_SENSOR_READING";

// Define GPS serial pins and baud rate
#define RXD2 16
#define TXD2 17
#define GPS_BAUD 9600

TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// A simple counter for reading_id
unsigned long reading_id = 1;

void setup() {
  // Start Serial Monitor
  Serial.begin(115200);

  // Initialize Serial2 for GPS communication
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, RXD2, TXD2);
  Serial.println("Serial 2 started at 9600 baud rate");

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
}

void sendReading(double latitude, double longitude, double speed) {
  // Build the JSON string manually ensuring numeric values are not quoted
  String jsonPayload = "{";
  jsonPayload += "\"reading_id\": \"" + String(reading_id) + "\",";
  jsonPayload += "\"sensor_id\": \"101\",";
  jsonPayload += "\"vehicle_id\": \"1\",";
  
  // Use the current time since boot as timestamp (consider using an NTP library for UTC time)
  String timestamp = String(millis());
  jsonPayload += "\"timestamp\": \"" + timestamp + "\",";
  
  jsonPayload += "\"value\": {";
  jsonPayload += "\"latitude\": " + String(latitude, 6) + ",";
  jsonPayload += "\"longitude\": " + String(longitude, 6) + ",";
  jsonPayload += "\"speed\": " + String(speed, 2);
  jsonPayload += "}";
  jsonPayload += "}";

  Serial.println("Posting JSON:");
  Serial.println(jsonPayload);

  // Check WiFi connection status
  if(WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(POST_SENSOR_READING_WEBHOOK);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(jsonPayload);
    
    if(httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      String response = http.getString();
      Serial.println("Response from server:");
      Serial.println(response);
    } else {
      Serial.print("Error in HTTP request: ");
      Serial.println(httpResponseCode);
    }
    
    http.end(); // Close connection
  } else {
    Serial.println("WiFi not connected");
  }

  reading_id++;  // Increment the reading ID for the next reading
}

void loop() {
  unsigned long start = millis();
  
  // Read data from the GPS module for 1 second
  while (millis() - start < 1000) {
    while (gpsSerial.available() > 0) {
      gps.encode(gpsSerial.read());
    }
  }

  // If a new location has been updated, print and post the data
  if (gps.location.isUpdated()) {
    double lat = gps.location.lat();
    double lng = gps.location.lng();
    double speedVal = gps.speed.kmph();
    
    Serial.print("LAT: ");
    Serial.println(lat, 6);
    Serial.print("LONG: ");
    Serial.println(lng, 6);
    Serial.print("SPEED (km/h) = ");
    Serial.println(speedVal, 2);

    // Send the GPS data to the webhook
    sendReading(lat, lng, speedVal);
  }
}
