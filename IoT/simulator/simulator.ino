/**************************************************************************
 * ESP32 S3 Sensor Simulator
 *
 * This sketch simulates sensor readings for 5 vehicles, each with 3 sensors:
 *   - Sensor Type 1: GPS
 *   - Sensor Type 2: TPMS (tyre pressure and temperature)
 *   - Sensor Type 3: Fuel Level
 *
 * The simulator sends readings and alerts via HTTPS POST requests to the 
 * following webhooks (with the exact same endpoints and API keys as provided):
 *   - POST_SENSOR_READING_WEBHOOK
 *   - POST_ALERT_WEBHOOK
 *   - UPDATE_STATUS_WEBHOOK
 *
 * The simulation logic (including state updates and alert triggering) is 
 * identical to your Node.js code.
 *
 * Libraries required:
 *   - WiFi (built-in with ESP32 board support)
 *   - WiFiClientSecure (for HTTPS connections)
 *   - HTTPClient (for HTTP/HTTPS requests)
 *   - ArduinoJson (for JSON serialization)
 *   - time.h (for timestamp generation using NTP)
 *
 * Make sure to install the ArduinoJson library via the Library Manager.
 *
 * Created: 2025-02-06
 **************************************************************************/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>

// WiFi credentials – replace with your actual SSID and password
const char* ssid     = "TP-Link_F00C";
const char* password = "YOUR_WIFI_PASSWORD";

// Webhook endpoints (exact same URLs as in your Node.js code)
const char* POST_SENSOR_READING_WEBHOOK = "https://swift-cloud.ephlux.com/api-swift/ned/integration/n1EBuKoSmc?SWIFT_API_KEY=YOUR_SWIFT_KEY_POST_SENSOR_READING";
const char* POST_ALERT_WEBHOOK          = "https://swift-cloud.ephlux.com/api-swift/ned/workflow/fzuttyO91i?SWIFT_API_KEY=YOUR_SWIFT_KEY_POST_ALERT";
const char* UPDATE_STATUS_WEBHOOK       = "https://swift-cloud.ephlux.com/api-swift/ned/workflow/LWSNalCzP_?SWIFT_API_KEY=YOUR_SWIFT_KEY_UPDATE_STATUS";

// --------------------------------------------------------------------------
// Data Structures and Global Variables
// --------------------------------------------------------------------------

#define NUM_VEHICLES 5
#define NUM_SENSORS  (NUM_VEHICLES * 3)  // Each vehicle has 3 sensors

// Structure to represent a vehicle
struct Vehicle {
  int    vehicle_id;
  String make;
  String model;
  String status;
  int    alerts;
};

// Array of vehicles – same as your Node.js simulator
Vehicle vehicles[NUM_VEHICLES] = {
  {1, "Kia",    "Sportage", "active", 0},
  {2, "Toyota", "Corolla",  "active", 0},
  {3, "Honda",  "Civic",    "active", 0},
  {4, "Suzuki", "Cultus",   "active", 0},
  {5, "Toyota", "Fortuner", "active", 0}
};

// Structure to represent a geographic position
struct Position {
  float lat;
  float lng;
};

// Initial vehicle locations in Houston (same as provided)
Position initialVehicleLocations[NUM_VEHICLES] = {
  {29.7604, -95.3698}, // Near Downtown Houston
  {29.7499, -95.3584}, // Near Houston Museum District
  {29.7321, -95.3420}, // Near Texas Medical Center
  {29.7602, -95.4025}, // Near Memorial Park
  {29.7188, -95.4260}  // Near NRG Stadium
};

// Vehicle positions (indexed by vehicle_id; index 0 is unused)
Position vehiclePositions[NUM_VEHICLES + 1];

// Structure to represent a sensor
struct Sensor {
  int sensor_id;
  int vehicle_id;
  int sensor_type_id; // 1: GPS, 2: TPMS, 3: Fuel
};

// Array to hold all sensors (total of 15 sensors)
Sensor sensors[NUM_SENSORS];

// Sensor state arrays (indexed by vehicle_id)
float fuelLevels[NUM_VEHICLES + 1];
float tyrePressureLevels[NUM_VEHICLES + 1];
float temperatureLevels[NUM_VEHICLES + 1];

// Global counters for reading and alert IDs
unsigned long readingCounter = 1;
unsigned long alertCounter   = 1;

// For timing the sensor simulation (every 5000 ms)
unsigned long lastReadingTime = 0;

// --------------------------------------------------------------------------
// Helper Functions
// --------------------------------------------------------------------------

/**
 * @brief Returns a random float between min and max.
 */
float randomFloat(float min, float max) {
  return min + ((float)random(0, 10000) / 10000.0) * (max - min);
}

/**
 * @brief Rounds a float value to 2 decimal places.
 */
float round2(float value) {
  return round(value * 100) / 100.0;
}

/**
 * @brief Returns the current time as an ISO 8601 formatted string.
 *
 * This function uses NTP (configured in setup) and the time.h library.
 */
String getISOTimestamp() {
  time_t now;
  struct tm timeinfo;
  time(&now);
  gmtime_r(&now, &timeinfo);
  char buffer[30];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buffer);
}

// --------------------------------------------------------------------------
// Functions for Sending Data Over HTTPS
// --------------------------------------------------------------------------

/**
 * @brief Sends an alert to the POST_ALERT_WEBHOOK.
 *
 * @param vehicle_id   The vehicle identifier.
 * @param sensor_id    The sensor identifier.
 * @param alert_type   The type of alert (e.g., "Fuel Level").
 * @param severity     The alert severity.
 * @param description  A description of the alert.
 */
void sendAlert(int vehicle_id, int sensor_id, String alert_type, String severity, String description) {
  StaticJsonDocument<256> doc;
  doc["alert_id"]   = alertCounter++;
  doc["vehicle_id"] = vehicle_id;
  doc["sensor_id"]  = sensor_id;
  doc["alert_type"] = alert_type;
  doc["severity"]   = severity;
  doc["description"]= description;
  doc["status"]     = "Active";
  doc["timestamp"]  = getISOTimestamp();

  String payload;
  serializeJson(doc, payload);

  // Use WiFiClientSecure for HTTPS. setInsecure() disables certificate validation.
  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  http.begin(client, POST_ALERT_WEBHOOK);
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(payload);
  if (httpResponseCode > 0) {
    Serial.print("Alert Sent: ");
    Serial.println(payload);
    // After sending an alert, update the vehicle's alert count and status.
    // (This function will call updateVehicleStatus.)
    // Note: updateVehicleAlerts() will search the vehicles array by vehicle_id.
    for (int i = 0; i < NUM_VEHICLES; i++) {
      if (vehicles[i].vehicle_id == vehicle_id) {
        vehicles[i].alerts++;
        if (vehicles[i].alerts > 2) {
          vehicles[i].status = "Critical";
        } else if (vehicles[i].alerts >= 1) {
          vehicles[i].status = "Warning";
        }
        // Send updated status to the webhook.
        StaticJsonDocument<128> statusDoc;
        statusDoc["vehicle_id"] = vehicle_id;
        statusDoc["status"] = vehicles[i].status;
        String statusPayload;
        serializeJson(statusDoc, statusPayload);

        WiFiClientSecure statusClient;
        statusClient.setInsecure();
        HTTPClient statusHttp;
        statusHttp.begin(statusClient, UPDATE_STATUS_WEBHOOK);
        statusHttp.addHeader("Content-Type", "application/json");
        int statusCode = statusHttp.POST(statusPayload);
        if (statusCode > 0) {
          Serial.print("Vehicle ");
          Serial.print(vehicle_id);
          Serial.print(" status updated to ");
          Serial.println(vehicles[i].status);
        } else {
          Serial.print("Failed to update vehicle ");
          Serial.print(vehicle_id);
          Serial.print(" status: ");
          Serial.println(statusHttp.errorToString(statusCode));
        }
        statusHttp.end();
        break;
      }
    }
  } else {
    Serial.print("Failed to send alert: ");
    Serial.println(http.errorToString(httpResponseCode));
  }
  http.end();
}

/**
 * @brief Sends a sensor reading to the POST_SENSOR_READING_WEBHOOK.
 *
 * @param reading The JSON document containing the reading data.
 */
void sendReading(JsonDocument &reading) {
  String payload;
  serializeJson(reading, payload);

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  http.begin(client, POST_SENSOR_READING_WEBHOOK);
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(payload);
  if (httpResponseCode > 0) {
    Serial.print("Sent reading ");
    Serial.print(reading["reading_id"].as<unsigned long>());
    Serial.print(" for sensor ");
    Serial.println(reading["sensor_id"].as<int>());
  } else {
    Serial.print("Failed to send reading ");
    Serial.print(reading["reading_id"].as<unsigned long>());
    Serial.print(": ");
    Serial.println(http.errorToString(httpResponseCode));
  }
  http.end();
}

// --------------------------------------------------------------------------
// Sensor Reading Generator Functions
// --------------------------------------------------------------------------

/**
 * @brief Generates a fuel sensor reading.
 *
 * Decreases the fuel level; if it falls below the threshold, triggers an alert
 * and resets the fuel level.
 *
 * @param sensor_id  The sensor identifier.
 * @param vehicle_id The vehicle identifier.
 * @param doc        A JSON document to populate with the reading.
 */
void generateFuelReading(int sensor_id, int vehicle_id, JsonDocument &doc) {
  float fuelLevel = fuelLevels[vehicle_id];
  // Decrease fuel level by a random amount in the range [2, 7]
  float consumption = randomFloat(2, 7);
  fuelLevel -= consumption;
  fuelLevel = round2(fuelLevel);

  if (fuelLevel <= 10) {
    // Trigger alert for critically low fuel
    sendAlert(vehicle_id, sensor_id, "Fuel Level", "Critical", "Fuel level critically low");
    // Reset fuel level to a value in the range [20, 30]
    fuelLevel = 20.0 + randomFloat(0.0, 10.0);
    fuelLevel = round2(fuelLevel);
  }
  fuelLevels[vehicle_id] = fuelLevel;

  // Build JSON reading payload
  doc["reading_id"]  = readingCounter++;
  doc["sensor_id"]   = sensor_id;
  doc["vehicle_id"]  = vehicle_id;
  doc["timestamp"]   = getISOTimestamp();
  JsonObject value = doc.createNestedObject("value");
  char buffer[10];
  dtostrf(fuelLevel, 1, 2, buffer);
  value["fuel_level"] = buffer;
}

/**
 * @brief Generates a TPMS (tyre pressure and temperature) sensor reading.
 *
 * Decreases tyre pressure and increases temperature with random variations.
 * Triggers alerts when tyre pressure or temperature cross critical thresholds.
 *
 * @param sensor_id  The sensor identifier.
 * @param vehicle_id The vehicle identifier.
 * @param doc        A JSON document to populate with the reading.
 */
void generateTPMSReading(int sensor_id, int vehicle_id, JsonDocument &doc) {
  float tyrePressure = tyrePressureLevels[vehicle_id];
  float temperature  = temperatureLevels[vehicle_id];

  // Decrease tyre pressure by a random value in the range [2, 12]
  float pressureDrop = randomFloat(2, 12);
  tyrePressure -= pressureDrop;
  tyrePressure = round2(tyrePressure);

  if (tyrePressure <= 100) {
    sendAlert(vehicle_id, sensor_id, "Tyre Pressure", "High", "Tyre pressure critically low");
    // Reset tyre pressure to a value in the range [150, 200]
    tyrePressure = 150.0 + randomFloat(0.0, 50.0);
    tyrePressure = round2(tyrePressure);
  }

  // Increase temperature by a random value up to 3 degrees
  float tempIncrease = randomFloat(0, 3);
  temperature += tempIncrease;
  temperature = round2(temperature);

  if (temperature >= 45) {
    sendAlert(vehicle_id, sensor_id, "Temperature", "Medium", "Temperature critically high");
    // Reset temperature to a value in the range [35, 40]
    temperature = 35.0 + randomFloat(0, 5);
    temperature = round2(temperature);
  }

  tyrePressureLevels[vehicle_id] = tyrePressure;
  temperatureLevels[vehicle_id]  = temperature;

  // Build JSON reading payload
  doc["reading_id"]  = readingCounter++;
  doc["sensor_id"]   = sensor_id;
  doc["vehicle_id"]  = vehicle_id;
  doc["timestamp"]   = getISOTimestamp();
  JsonObject value = doc.createNestedObject("value");
  char bufferPressure[10];
  char bufferTemp[10];
  dtostrf(tyrePressure, 1, 2, bufferPressure);
  dtostrf(temperature, 1, 2, bufferTemp);
  value["tyre_pressure"] = bufferPressure;
  value["temperature"]   = bufferTemp;
}

/**
 * @brief Computes the next GPS position for the vehicle.
 *
 * Randomly adjusts the latitude and longitude by up to ±0.01.
 *
 * @param vehicle_id The vehicle identifier.
 * @return Position  The updated position.
 */
Position getNextPosition(int vehicle_id) {
  Position currentPosition = vehiclePositions[vehicle_id];
  float latChange = randomFloat(-0.01, 0.01);
  float lngChange = randomFloat(-0.01, 0.01);
  float newLat  = round2(currentPosition.lat + latChange);
  float newLng  = round2(currentPosition.lng + lngChange);
  vehiclePositions[vehicle_id].lat = newLat;
  vehiclePositions[vehicle_id].lng = newLng;
  Position newPos = { newLat, newLng };
  return newPos;
}

/**
 * @brief Generates a GPS sensor reading.
 *
 * Retrieves the next position and a simulated speed.
 *
 * @param sensor_id  The sensor identifier.
 * @param vehicle_id The vehicle identifier.
 * @param doc        A JSON document to populate with the reading.
 */
void generateGPSReading(int sensor_id, int vehicle_id, JsonDocument &doc) {
  Position pos = getNextPosition(vehicle_id);
  doc["reading_id"]  = readingCounter++;
  doc["sensor_id"]   = sensor_id;
  doc["vehicle_id"]  = vehicle_id;
  doc["timestamp"]   = getISOTimestamp();
  JsonObject value = doc.createNestedObject("value");
  value["latitude"]  = pos.lat;
  value["longitude"] = pos.lng;
  // Simulate speed in the range [40, 100]
  float speed = round2(randomFloat(40, 100));
  char bufferSpeed[10];
  dtostrf(speed, 1, 2, bufferSpeed);
  value["speed"] = bufferSpeed;
}

// --------------------------------------------------------------------------
// Simulation Loop: Generate and Send Sensor Readings
// --------------------------------------------------------------------------

/**
 * @brief Iterates over each vehicle and its sensors, generating and sending
 * sensor readings.
 */
void simulateSensorReadings() {
  // Loop through all vehicles
  for (int i = 0; i < NUM_VEHICLES; i++) {
    int vehicle_id = vehicles[i].vehicle_id;
    // Loop through all sensors and filter those belonging to this vehicle
    for (int j = 0; j < NUM_SENSORS; j++) {
      if (sensors[j].vehicle_id == vehicle_id) {
        int sensor_id      = sensors[j].sensor_id;
        int sensor_type_id = sensors[j].sensor_type_id;
        // Create a JSON document for the reading (size: 256 bytes)
        StaticJsonDocument<256> readingDoc;
        switch (sensor_type_id) {
          case 1: // GPS
            generateGPSReading(sensor_id, vehicle_id, readingDoc);
            break;
          case 2: // TPMS
            generateTPMSReading(sensor_id, vehicle_id, readingDoc);
            break;
          case 3: // Fuel
            generateFuelReading(sensor_id, vehicle_id, readingDoc);
            break;
          default:
            break;
        }
        sendReading(readingDoc);
      }
    }
  }
}

// --------------------------------------------------------------------------
// Setup and Loop
// --------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nStarting ESP32 S3 Sensor Simulator");

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi.");

  // Configure NTP for time synchronization (required for ISO timestamp)
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  // Wait until time is set
  time_t now = time(nullptr);
  while (now < 8 * 3600 * 2) {
    delay(500);
    now = time(nullptr);
  }
  Serial.println("Time synchronized.");

  // Seed the random number generator using an unconnected analog pin
  randomSeed(analogRead(0));

  // Initialize vehicle positions based on initial locations
  for (int i = 0; i < NUM_VEHICLES; i++) {
    int vehicle_id = vehicles[i].vehicle_id;
    vehiclePositions[vehicle_id].lat = initialVehicleLocations[i].lat;
    vehiclePositions[vehicle_id].lng = initialVehicleLocations[i].lng;
  }

  // Initialize sensors for each vehicle:
  // Each vehicle gets 3 sensors: 
  //   - Sensor type 1: GPS  (sensor_id = vehicle_id * 10 + 1)
  //   - Sensor type 2: TPMS (sensor_id = vehicle_id * 10 + 2)
  //   - Sensor type 3: Fuel (sensor_id = vehicle_id * 10 + 3)
  int sensorIndex = 0;
  for (int i = 0; i < NUM_VEHICLES; i++) {
    int vehicle_id = vehicles[i].vehicle_id;
    sensors[sensorIndex++] = { vehicle_id * 10 + 1, vehicle_id, 1 };
    sensors[sensorIndex++] = { vehicle_id * 10 + 2, vehicle_id, 2 };
    sensors[sensorIndex++] = { vehicle_id * 10 + 3, vehicle_id, 3 };
  }

  // Initialize sensor state values for each vehicle
  for (int i = 0; i < NUM_VEHICLES; i++) {
    int vehicle_id = vehicles[i].vehicle_id;
    fuelLevels[vehicle_id]       = 20.0 + randomFloat(0.0, 10.0);
    tyrePressureLevels[vehicle_id] = 150.0 + randomFloat(0.0, 50.0);
    temperatureLevels[vehicle_id]  = 40.0;
  }

  Serial.println("Sensor simulator is running...");
}

void loop() {
  // Every 5000 milliseconds (5 seconds), simulate sensor readings.
  // if (millis() - lastReadingTime >= 5000) {
  //   simulateSensorReadings();
  //   lastReadingTime = millis();
  // }
}
