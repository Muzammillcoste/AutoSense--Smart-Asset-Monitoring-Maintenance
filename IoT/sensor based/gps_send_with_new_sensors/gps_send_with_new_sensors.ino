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
#include <TinyGPS++.h>

// -------------------------
// WiFi & NTP Configuration
// -------------------------
struct WiFiCred {
    const char* ssid;
    const char* password;
};

const int numNetworks = 4;
WiFiCred wifiCreds[numNetworks] = {
    {"Sparx Ultra 11", "1234567890"},
    {"Huzaifa", "huzaifa123567"},
    {"TP-Link_F00C", "google@1234"},
    {"realme C1", "12345678"},
};

const char* POST_SENSOR_READING_WEBHOOK = "https://swift-cloud.ephlux.com/api-swift/ned/integration/n1EBuKoSmc?SWIFT_API_KEY=Bc4JfnH9ht5FMKxTNXQZKL_8WsSDR+";
const char* POST_ALERT_WEBHOOK = "https://swift-cloud.ephlux.com/api-swift/ned/workflow/fzuttyO91i?SWIFT_API_KEY=6rrI6H1.VrbGvAjCEfTr-xXW";
const char* UPDATE_STATUS_WEBHOOK = "https://swift-cloud.ephlux.com/api-swift/ned/workflow/LWSNalCzP_?SWIFT_API_KEY=BBtf-pvchwljttPIrm300xCJRzb93";

const char* ntpServer1 = "pool.ntp.org";
const char* ntpServer2 = "time.nist.gov";
const long  gmtOffset_sec = 0;
const int   daylightOffset_sec = 0;

// -------------------------
// GPS Configuration
// -------------------------
#define RXD2 16
#define TXD2 17
#define GPS_BAUD 9600
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// -------------------------
// Global Variables & Timing
// -------------------------
unsigned long reading_counter = 0;
unsigned long lastSendTime = 0;
unsigned long lastGPSSendTime = 0;
const unsigned long sendInterval = 300000; // 5 minutes
const unsigned long gpsSendInterval = 5000; // 5 seconds
int vehicle_alert_count = 0;

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
// GPS Global Variables
double gps_latitude = 0.0;
double gps_longitude = 0.0;
double gps_speed = 0.0;

// -------------------------
// Helper Function: Round to 2 Decimal Places
// -------------------------
float round2(float value) {
    return floor(value * 100 + 0.5) / 100;
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
    WiFi.mode(WIFI_STA);
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

        String availableSSIDs[numAvailable];
        for (int i = 0; i < numAvailable; i++) {
            availableSSIDs[i] = WiFi.SSID(i);
        }
        for (int i = 0; i < numNetworks; i++) {
            const char* targetSSID = wifiCreds[i].ssid;
            if (isSSIDAvailable(targetSSID, availableSSIDs, numAvailable)) {
                Serial.print("Attempting to connect to ");
                Serial.println(targetSSID);
                WiFi.begin(wifiCreds[i].ssid, wifiCreds[i].password);
                int attempt = 0;
                while (WiFi.status() != WL_CONNECTED && attempt < 20) {
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
        Serial.println("Could not connect to any known WiFi network. Retrying in 10 seconds");
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

                long pressureRaw = returnData(manufacturerData, 16);
                float pressurePSI = (pressureRaw / 100000.0) * 14.5038;

                long temperatureRaw = returnData(manufacturerData, 24);
                float temperatureC = temperatureRaw / 100.0;

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
// HTTP POST Helper Functions
// -------------------------
void sendHTTPPostToUrl(String jsonPayload, const char* url) {
    HTTPClient http;
    http.begin(url);
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

void sendHTTPPost(String jsonPayload) {
    sendHTTPPostToUrl(jsonPayload, POST_SENSOR_READING_WEBHOOK);
}

// -------------------------
// Timestamp Function
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

// -------------------------
// Setup Function
// -------------------------
void setup() {
    Serial.begin(115200);
    Serial.println("Initializing sensors and network...");

    // Initialize GPS
    gpsSerial.begin(GPS_BAUD, SERIAL_8N1, RXD2, TXD2);
    Serial.println("GPS Serial started at 9600 baud rate");

    connectToWiFi();
    initTime();
    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pBLEScan->setActiveScan(true);
    sensors.begin();
    randomSeed(analogRead(0));
    lastSendTime = millis();
    lastGPSSendTime = millis();
}

// -------------------------
// Main Loop
// -------------------------
void loop() {
    // Read GPS data for 1 second
    unsigned long start = millis();
    while (millis() - start < 1000) {
        while (gpsSerial.available() > 0) {
            gps.encode(gpsSerial.read());
        }
    }

    // BLE TPMS scan
    BLEScanResults* foundDevices = pBLEScan->start(1, false);
    pBLEScan->clearResults();

    // Update GPS variables if data is available
    if (gps.location.isValid()) {
        gps_latitude = gps.location.lat();
        gps_longitude = gps.location.lng();
    }
    if (gps.speed.isValid()) {
        gps_speed = gps.speed.kmph();
    }

    // Send GPS location and speed every 5 seconds
    if (millis() - lastGPSSendTime >= gpsSendInterval) {
        if (gps.location.isValid()) {
            DynamicJsonDocument gpsDoc(128);
            String gpsReadingId = "gps" + String(random(100000, 999999));
            gpsDoc["reading_id"] = gpsReadingId;
            gpsDoc["sensor_id"] = 101;
            gpsDoc["vehicle_id"] = 1;
            gpsDoc["timestamp"] = getISOTimestamp();
            JsonObject value = gpsDoc.createNestedObject("value");
            value["latitude"] = round2(gps_latitude);
            value["longitude"] = round2(gps_longitude);
            value["speed"] = round2(gps_speed);

            String gpsPayload;
            serializeJson(gpsDoc, gpsPayload);
            Serial.println("Sending GPS Location JSON Payload:");
            Serial.println(gpsPayload);
            sendHTTPPost(gpsPayload);
        } else {
            Serial.println("GPS location not valid, skipping send.");
        }
        lastGPSSendTime = millis();
    }

    // Main sensor readings every 5 minutes
    if (millis() - lastSendTime >= sendInterval) {
        reading_counter++;
        String isoTimestamp = getISOTimestamp();

        // Request DS18B20 temperature
        sensors.requestTemperatures();
        ds18b20_temperature = sensors.getTempCByIndex(0);

        // --- Build TPMS JSON Payload ---
        DynamicJsonDocument tpmsDoc(512);
        String tpmsReadingId = "tpms" + String(random(100000, 999999));
        tpmsDoc["reading_id"] = tpmsReadingId;
        tpmsDoc["sensor_id"] = 102;
        tpmsDoc["vehicle_id"] = 1;
        tpmsDoc["timestamp"] = isoTimestamp;
        JsonObject tpmsValue = tpmsDoc.createNestedObject("value");

        JsonObject frontLeft = tpmsValue.createNestedObject("front_left");
        frontLeft["pressure"] = round2(tpms_front_left);
        frontLeft["temperature"] = round2(tpms_front_left_temp);

        JsonObject frontRight = tpmsValue.createNestedObject("front_right");
        frontRight["pressure"] = round2(tpms_front_right);
        frontRight["temperature"] = round2(tpms_front_right_temp);

        JsonObject rearLeft = tpmsValue.createNestedObject("rear_left");
        rearLeft["pressure"] = round2(tpms_rear_left);
        rearLeft["temperature"] = round2(tpms_rear_left_temp);

        JsonObject rearRight = tpmsValue.createNestedObject("rear_right");
        rearRight["pressure"] = round2(tpms_rear_right);
        rearRight["temperature"] = round2(tpms_rear_right_temp);

        String tpmsPayload;
        serializeJson(tpmsDoc, tpmsPayload);

        // --- Build Temperature JSON Payload (DS18B20) ---
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

        // --- Build GPS Speed JSON Payload ---
        DynamicJsonDocument gpsSpeedDoc(128);
        String gpsSpeedReadingId = "gps_speed" + String(random(100000, 999999));
        gpsSpeedDoc["reading_id"] = gpsSpeedReadingId;
        gpsSpeedDoc["sensor_id"] = 101;
        gpsSpeedDoc["vehicle_id"] = 1;
        gpsSpeedDoc["timestamp"] = isoTimestamp;
        JsonObject gpsSpeedValue = gpsSpeedDoc.createNestedObject("value");
        gpsSpeedValue["speed"] = round2(gps_speed);

        String gpsSpeedPayload;
        serializeJson(gpsSpeedDoc, gpsSpeedPayload);

        // Print and send payloads
        Serial.println("Sending TPMS JSON Payload:");
        Serial.println(tpmsPayload);
        Serial.println("Sending Temperature JSON Payload:");
        Serial.println(tempPayload);
        Serial.println("Sending GPS Speed JSON Payload:");
        Serial.println(gpsSpeedPayload);

        sendHTTPPost(tpmsPayload);
        sendHTTPPost(tempPayload);
        sendHTTPPost(gpsSpeedPayload);

        // --- Alert Generation ---
        vehicle_alert_count = 0;

        // Tyre pressure alerts
        if (tpms_front_left > 32) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tpmsReadingId;
            alertDoc["sensor_id"] = 102;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Tyre Pressure (front_left)";
            alertDoc["severity"] = "High";
            alertDoc["description"] = "Tyre pressure high in front_left";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Alert (front_left high):");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }
        if (tpms_front_left <= 25) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tpmsReadingId;
            alertDoc["sensor_id"] = 102;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Tyre Pressure (front_left)";
            alertDoc["severity"] = "High";
            alertDoc["description"] = "Tyre pressure low in front_left";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Alert (front_left low):");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }
        if (tpms_front_right > 32) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tpmsReadingId;
            alertDoc["sensor_id"] = 102;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Tyre Pressure (front_right)";
            alertDoc["severity"] = "High";
            alertDoc["description"] = "Tyre pressure high in front_right";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Alert (front_right high):");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }
        if (tpms_front_right <= 25) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tpmsReadingId;
            alertDoc["sensor_id"] = 102;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Tyre Pressure (front_right)";
            alertDoc["severity"] = "High";
            alertDoc["description"] = "Tyre pressure low in front_right";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Alert (front_right low):");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }
        if (tpms_rear_left > 32) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tpmsReadingId;
            alertDoc["sensor_id"] = 102;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Tyre Pressure (rear_left)";
            alertDoc["severity"] = "High";
            alertDoc["description"] = "Tyre pressure high in rear_left";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Alert (rear_left high):");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }
        if (tpms_rear_left <= 25) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tpmsReadingId;
            alertDoc["sensor_id"] = 102;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Tyre Pressure (rear_left)";
            alertDoc["severity"] = "High";
            alertDoc["description"] = "Tyre pressure low in rear_left";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Alert (rear_left low):");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }
        if (tpms_rear_right > 32) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tpmsReadingId;
            alertDoc["sensor_id"] = 102;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Tyre Pressure (rear_right)";
            alertDoc["severity"] = "High";
            alertDoc["description"] = "Tyre pressure high in rear_right";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Alert (rear_right high):");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }
        if (tpms_rear_right <= 25) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tpmsReadingId;
            alertDoc["sensor_id"] = 102;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Tyre Pressure (rear_right)";
            alertDoc["severity"] = "High";
            alertDoc["description"] = "Tyre pressure low in rear_right";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Alert (rear_right low):");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }
        if (ds18b20_temperature >= 80) {
            DynamicJsonDocument alertDoc(256);
            String alertId = "alert" + String(random(100000, 999999));
            alertDoc["alert_id"] = alertId;
            alertDoc["vehicle_id"] = 1;
            alertDoc["reading_id"] = tempReadingId;
            alertDoc["sensor_id"] = 103;
            alertDoc["status"] = "Active";
            alertDoc["alert_type"] = "Temperature";
            alertDoc["severity"] = "Medium";
            alertDoc["description"] = "Engine Temperature High";
            String alertPayload;
            serializeJson(alertDoc, alertPayload);
            Serial.println("Sending Engine Temperature Alert:");
            Serial.println(alertPayload);
            sendHTTPPostToUrl(alertPayload, POST_ALERT_WEBHOOK);
            vehicle_alert_count++;
        }

        // --- Update Vehicle Status ---
        String vehicleStatus;
        if (vehicle_alert_count >= 2) {
            vehicleStatus = "Critical";
        } else if (vehicle_alert_count == 1) {
            vehicleStatus = "Warning";
        } else {
            vehicleStatus = "Active";
        }

        if (vehicle_alert_count > 0 || vehicleStatus == "Active") {
            DynamicJsonDocument statusDoc(128);
            statusDoc["vehicle_id"] = 1;
            statusDoc["status"] = vehicleStatus;
            String statusPayload;
            serializeJson(statusDoc, statusPayload);
            Serial.println("Updating Vehicle Status:");
            Serial.println(statusPayload);
            sendHTTPPostToUrl(statusPayload, UPDATE_STATUS_WEBHOOK);
        }

        lastSendTime = millis();
    }

    delay(100);
}