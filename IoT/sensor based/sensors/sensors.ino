#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>
#include <math.h>

// -------------------------
// WiFi & NTP Configuration
// -------------------------
struct WiFiCred {
    const char* ssid;
    const char* password;
};

const int numNetworks = 2;
WiFiCred wifiCreds[numNetworks] = {
    {"Huzaifa", "huzaifa123567"},
    {"Sparx Ultra 11", "1234567890"},
    {"realme C1", "12345678"}
};

const char* POST_SENSOR_READING_WEBHOOK = "https://swift-cloud.ephlux.com/api-swift/ned/integration/n1EBuKoSmc?SWIFT_API_KEY=Bc4JfnH9ht5FMKxTNXQZKL_8WsSDR+";
const char* ntpServer1 = "pool.ntp.org";
const char* ntpServer2 = "time.nist.gov";
const long  gmtOffset_sec = 0;
const int   daylightOffset_sec = 0;

// -------------------------
// Global Variables & Timing
// -------------------------
unsigned long reading_counter = 0;
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 300000; // 5 minutes

// Tyre Pressure Global Variables
float tpms_front_left = 0;
float tpms_front_right = 0;
float tpms_rear_left = 0;
float tpms_rear_right = 0;
// Tyre Temperature Global Variables
float tpms_front_left_temp = 0;
float tpms_front_right_temp = 0;
float tpms_rear_left_temp = 0;
float tpms_rear_right_temp = 0;

float ds18b20_temperature = 0;

// -------------------------
// Helper Function: Round to 2 Decimal Places
// -------------------------
float round2(float value) {
    return floor(value * 100 + 0.5) / 100.0;
}

// -------------------------
// Helper Function: Check if SSID is Available
// -------------------------
bool isSSIDAvailable(const char* ssid, String availableSSIDs[], int numAvailable) {
    for (int i = 0; i < numAvailable; i++) {
        if (availableSSIDs[i] == ssid) {
            return true;
        }
    }
    return false;
}

// -------------------------
// WiFi Connection Function
// -------------------------
void connectToWiFi() {
    WiFi.mode(WIFI_STA); // Set to station mode
    while (WiFi.status() != WL_CONNECTED) {
        Serial.println("Scanning for WiFi networks...");
        int numAvailable = WiFi.scanNetworks();
        if (numAvailable == 0) {
            Serial.println("No networks found. Retrying in 10 seconds...");
            delay(10000);
            continue;
        }
        Serial.print(numAvailable);
        Serial.println(" networks found.");

        // Store available SSIDs
        String availableSSIDs[numAvailable];
        for (int i = 0; i < numAvailable; i++) {
            availableSSIDs[i] = WiFi.SSID(i);
        }

        // Try connecting to each known network
        for (int i = 0; i < numNetworks; i++) {
            const char* targetSSID = wifiCreds[i].ssid;
            if (isSSIDAvailable(targetSSID, availableSSIDs, numAvailable)) {
                Serial.print("Attempting to connect to ");
                Serial.println(targetSSID);
                WiFi.begin(wifiCreds[i].ssid, wifiCreds[i].password);
                int attempt = 0;
                while (WiFi.status() != WL_CONNECTED && attempt < 20) { // Timeout around 10 sec
                    delay(500);
                    Serial.print(".");
                    attempt++;
                }
                if (WiFi.status() == WL_CONNECTED) {
                    Serial.println();
                    Serial.println("WiFi connected.");
                    return;
                } else {
                    Serial.println();
                    Serial.println("Failed to connect to " + String(targetSSID));
                }
            }
        }
        Serial.println("Could not connect to any known WiFi network. Retrying in 10 seconds...");
        delay(10000);
    }
}

// -------------------------
// NTP Initialization
// -------------------------
void initTime() {
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer1, ntpServer2);
    time_t now = time(nullptr);
    while (now < 8 * 3600 * 2) {
        delay(500);
        now = time(nullptr);
    }
    Serial.println("Time synchronized.");
}

// -------------------------
// BLE TPMS Sensor Code
// -------------------------
String knownAddresses[] = {
    "80:EA:CA:13:36:92",
    "81:EA:CA:23:2E:6C",
    "80:EA:CA:13:36:0D",
    "81:ea:ca:23:31:56"
};

String tyreNames[] = {"front_left", "front_right", "rear_left", "rear_right"};

// Helper Functions for Data Extraction
int retByte(String Data, int index) {
    return strtol(Data.substring(index, index + 2).c_str(), NULL, 16);
}

long returnData(String Data, int start) {
    return retByte(Data, start) |
           (retByte(Data, start + 2) << 8) |
           (retByte(Data, start + 4) << 16) |
           (retByte(Data, start + 6) << 24);
}

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        String deviceAddress = advertisedDevice.getAddress().toString().c_str();
        for (int i = 0; i < (sizeof(knownAddresses) / sizeof(knownAddresses[0])); i++) {
            if (deviceAddress.equalsIgnoreCase(knownAddresses[i])) {
                String deviceInfo = advertisedDevice.toString().c_str();
                int manuStart = deviceInfo.indexOf("manufacturer data: ") + 19;
                int manuEnd = deviceInfo.indexOf(",", manuStart);
                if (manuStart < 19 || manuEnd < manuStart) continue;
                String manufacturerData = deviceInfo.substring(manuStart, manuEnd);

                // Extract pressure data
                long pressureRaw = returnData(manufacturerData, 16);
                float pressurePSI = (pressureRaw / 100000.0) * 14.5038;

                // Extract Temperature (Little Endian) and Convert to °C
                long temperatureRaw = returnData(manufacturerData, 24);
                float temperatureC = temperatureRaw / 100.0;

                // Update global variables for pressure and temperature
                switch(i) {
                    case 0:
                        tpms_front_left = pressurePSI;
                        tpms_front_left_temp = temperatureC;
                        break;
                    case 1:
                        tpms_front_right = pressurePSI;
                        tpms_front_right_temp = temperatureC;
                        break;
                    case 2:
                        tpms_rear_left = pressurePSI;
                        tpms_rear_left_temp = temperatureC;
                        break;
                    case 3:
                        tpms_rear_right = pressurePSI;
                        tpms_rear_right_temp = temperatureC;
                        break;
                }
                Serial.println("Updated reading from sensor: " + deviceAddress + " (" + tyreNames[i] + ")");
                Serial.print("Pressure (PSI): ");
                Serial.println(pressurePSI, 2);
                Serial.print("Temperature (°C): ");
                Serial.println(temperatureC, 2);
            }
        }
    }
};

BLEScan* pBLEScan;

// -------------------------
// DS18B20 Sensor Setup
// -------------------------
const int oneWireBus = 4;
OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);

// -------------------------
// HTTP POST Helper Function
// -------------------------
String getISOTimestamp() {
    time_t now;
    time(&now);
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    char buf[25];
    sprintf(buf, "%04d-%02d-%02dT%02d:%02d:%02dZ",
            timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
            timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
    return String(buf);
}

void sendHTTPPost(String jsonPayload) {
    HTTPClient http;
    http.begin(POST_SENSOR_READING_WEBHOOK);
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(jsonPayload);
    if (httpResponseCode > 0) {
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
        Serial.println("Response: " + http.getString());
    } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
    }
    http.end();
}

// -------------------------
// Setup Function
// -------------------------
void setup() {
    Serial.begin(115200);
    Serial.println("Initializing sensors and network...");
    connectToWiFi();
    initTime();
    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pBLEScan->setActiveScan(true);
    sensors.begin();
    randomSeed(analogRead(0));
    lastSendTime = millis();
}

// -------------------------
// Main Loop
// -------------------------
void loop() {
    BLEScanResults* foundDevices = pBLEScan->start(1, false);
    pBLEScan->clearResults();

    if (millis() - lastSendTime >= sendInterval) {
        reading_counter++;
        String isoTimestamp = getISOTimestamp();

        sensors.requestTemperatures();
        ds18b20_temperature = sensors.getTempCByIndex(0);

        // Create a JSON document with the new structure for tyre reading
        DynamicJsonDocument tpmsDoc(512);
        String tpmsReadingId = "tpms" + String(random(100000, 999999));
        tpmsDoc["reading_id"] = tpmsReadingId;
        tpmsDoc["sensor_id"] = 102;
        tpmsDoc["vehicle_id"] = 1;
        tpmsDoc["timestamp"] = isoTimestamp;
        JsonObject value = tpmsDoc.createNestedObject("value");

        JsonObject frontLeft = value.createNestedObject("front_left");
        frontLeft["pressure"] = round2(tpms_front_left);
        frontLeft["temperature"] = round2(tpms_front_left_temp);

        JsonObject frontRight = value.createNestedObject("front_right");
        frontRight["pressure"] = round2(tpms_front_right);
        frontRight["temperature"] = round2(tpms_front_right_temp);

        JsonObject rearLeft = value.createNestedObject("rear_left");
        rearLeft["pressure"] = round2(tpms_rear_left);
        rearLeft["temperature"] = round2(tpms_rear_left_temp);

        JsonObject rearRight = value.createNestedObject("rear_right");
        rearRight["pressure"] = round2(tpms_rear_right);
        rearRight["temperature"] = round2(tpms_rear_right_temp);

        String tpmsPayload;
        serializeJson(tpmsDoc, tpmsPayload);

        // Temperature reading from DS18B20 remains unchanged
        DynamicJsonDocument tempDoc(128);
        String tempReadingId = "temp" + String(random(100000, 999999));
        tempDoc["reading_id"] = tempReadingId;
        tempDoc["sensor_id"] = 103;
        tempDoc["vehicle_id"] = 1;
        tempDoc["timestamp"] = isoTimestamp;
        JsonObject tempValue = tempDoc.createNestedObject("value");
        tempValue["temperature"] = round2(ds18b20_temperature);

        String tempPayload;
        serializeJson(tempDoc, tempPayload);

        Serial.println("Sending TPMS JSON Payload:");
        Serial.println(tpmsPayload);
        Serial.println("Sending Temperature JSON Payload:");
        Serial.println(tempPayload);

        sendHTTPPost(tpmsPayload);
        sendHTTPPost(tempPayload);

        lastSendTime = millis();
    }

    delay(100);
}
