#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// -------------------------
// Global Variables & Setup
// -------------------------

unsigned long reading_counter = 0;
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 300000; // 5 minutes (in milliseconds)

// Global variables for tyre pressures
float tpms_front_left = 0;
float tpms_front_right = 0;
float tpms_rear_left = 0;
float tpms_rear_right = 0;

// Global variable for DS18B20 temperature sensor
float ds18b20_temperature = 0;

// Known TPMS sensor addresses (assumed order: front_left, front_right, rear_left, rear_right)
String knownAddresses[] = {
  "80:EA:CA:13:36:92",
  "81:EA:CA:23:2E:6C",
  "80:EA:CA:13:36:0D",
  "81:ea:ca:23:31:56"
};

// -------------------------
// Helper Functions
// -------------------------

// Extract a byte from the string and convert it to an integer (hex)
int retByte(String Data, int index) {
  return strtol(Data.substring(index, index + 2).c_str(), NULL, 16);
}

// Extract 4 bytes (little-endian) from a string to return a long value
long returnData(String Data, int start) {
  return retByte(Data, start) |
         (retByte(Data, start + 2) << 8) |
         (retByte(Data, start + 4) << 16) |
         (retByte(Data, start + 6) << 24);
}

// -------------------------
// BLE Callback Class
// -------------------------

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    String deviceAddress = advertisedDevice.getAddress().toString().c_str();
    // Loop through our known addresses
    for (int i = 0; i < (sizeof(knownAddresses) / sizeof(knownAddresses[0])); i++) {
      if (deviceAddress.equalsIgnoreCase(knownAddresses[i])) {
        // Get the advertised data as a string
        String deviceInfo = advertisedDevice.toString().c_str();
        // Extract Manufacturer Data
        int manuStart = deviceInfo.indexOf("manufacturer data: ") + 19;
        int manuEnd = deviceInfo.indexOf(",", manuStart);
        if (manuStart < 19 || manuEnd < manuStart) continue;
        String manufacturerData = deviceInfo.substring(manuStart, manuEnd);
        
        // Extract Pressure (assumes pressure data starts at index 16 in manufacturerData)
        long pressureRaw = returnData(manufacturerData, 16);
        float pressurePSI = (pressureRaw / 100000.0) * 14.5038;
        
        // Update the corresponding global variable based on the sensor order
        switch(i) {
          case 0:
            tpms_front_left = pressurePSI;
            break;
          case 1:
            tpms_front_right = pressurePSI;
            break;
          case 2:
            tpms_rear_left = pressurePSI;
            break;
          case 3:
            tpms_rear_right = pressurePSI;
            break;
        }
        
        // Optional: Debug print for each sensor update
        Serial.println("Updated pressure from sensor: " + deviceAddress);
        Serial.print("Pressure (PSI): ");
        Serial.println(pressurePSI, 2);
      }
    }
  }
};

BLEScan* pBLEScan;

// -------------------------
// DS18B20 Sensor Setup
// -------------------------

const int oneWireBus = 4; // GPIO pin for DS18B20
OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);

// -------------------------
// Setup Function
// -------------------------

void setup() {
  Serial.begin(115200);
  Serial.println("Initializing sensors...");

  // Initialize BLE
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);  // Active scan to receive scan responses

  // Initialize DS18B20 sensor
  sensors.begin();
  
  lastSendTime = millis();
}

// -------------------------
// Main Loop
// -------------------------

void loop() {
  // Run a short BLE scan (1 second) to update TPMS values
  BLEScanResults* foundDevices = pBLEScan->start(1, false);
  pBLEScan->clearResults();

  // Check if it is time to send (print) the JSON data
  if (millis() - lastSendTime >= sendInterval) {
    reading_counter++;
    unsigned long currentTimestamp = millis(); // Using millis() as a stand-in for current timestamp
    
    // Read DS18B20 temperature
    sensors.requestTemperatures(); 
    ds18b20_temperature = sensors.getTempCByIndex(0);
    
    // Build JSON string for TPMS data
    String tpmsJson = "{";
    tpmsJson += "\"reading_id\": " + String(reading_counter) + ", ";
    tpmsJson += "\"sensor_id\": 102, ";
    tpmsJson += "\"vehicle_id\": 1, ";
    tpmsJson += "\"timestamp\": " + String(currentTimestamp) + ", ";
    tpmsJson += "\"value\": {";
    tpmsJson += "\"tyre_pressure\": {";
    tpmsJson += "\"front_left\": " + String(tpms_front_left, 2) + ", ";
    tpmsJson += "\"front_right\": " + String(tpms_front_right, 2) + ", ";
    tpmsJson += "\"rear_left\": " + String(tpms_rear_left, 2) + ", ";
    tpmsJson += "\"rear_right\": " + String(tpms_rear_right, 2);
    tpmsJson += "}";
    tpmsJson += "}";
    tpmsJson += "}";
    
    // Build JSON string for DS18B20 temperature sensor data
    String tempJson = "{";
    tempJson += "\"reading_id\": " + String(reading_counter) + ", ";
    tempJson += "\"sensor_id\": 103, ";
    tempJson += "\"vehicle_id\": 1, ";
    tempJson += "\"timestamp\": " + String(currentTimestamp) + ", ";
    tempJson += "\"value\": {";
    tempJson += "\"temperature\": " + String(ds18b20_temperature, 2);
    tempJson += "}";
    tempJson += "}";
    
    // Print JSON data to Serial (this is where you would send it via HTTP)
    Serial.println("TPMS JSON Data:");
    Serial.println(tpmsJson);
    Serial.println("Temperature Sensor JSON Data:");
    Serial.println(tempJson);
    
    // Update last send time
    lastSendTime = millis();
  }
  
  // Short delay to avoid an overly tight loop
  delay(1000);
}
