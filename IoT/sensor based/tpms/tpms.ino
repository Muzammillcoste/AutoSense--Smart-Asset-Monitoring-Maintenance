#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// Function to extract a byte from the string and convert it to an integer
int retByte(String Data, int index) {
    return strtol(Data.substring(index, index + 2).c_str(), NULL, 16);
}

// Function to get a long value from 4 bytes using little-endian conversion
long returnData(String Data, int start) {
    return retByte(Data, start) | 
           (retByte(Data, start + 2) << 8) | 
           (retByte(Data, start + 4) << 16) | 
           (retByte(Data, start + 6) << 24);
}

// Known TPMS sensor addresses
String knownAddresses[] = {"80:EA:CA:13:36:92", "81:EA:CA:23:2E:6C", "80:EA:CA:13:36:0D", "81:ea:ca:23:31:56"};

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    String deviceAddress = advertisedDevice.getAddress().toString().c_str();
    // Check if the scanned device is one of our known devices
    for (int i = 0; i < (sizeof(knownAddresses) / sizeof(knownAddresses[0])); i++) {
      if (deviceAddress.equalsIgnoreCase(knownAddresses[i])) {
        Serial.println("---- Known Device Found ----");
        Serial.print("Address: ");
        Serial.println(deviceAddress);
        Serial.print("RSSI: ");
        Serial.println(advertisedDevice.getRSSI());
        Serial.println("Advertisement Data:");
        
        String deviceInfo = advertisedDevice.toString().c_str();
        // Extract Name
        int nameStart = deviceInfo.indexOf("Name: ") + 6;
        int nameEnd = deviceInfo.indexOf(",", nameStart);
        String deviceName = deviceInfo.substring(nameStart, nameEnd);

        // Extract Address
        int addrStart = deviceInfo.indexOf("Address: ") + 9;
        int addrEnd = deviceInfo.indexOf(",", addrStart);
        String deviceAddress = deviceInfo.substring(addrStart, addrEnd);

        // Extract Manufacturer Data
        int manuStart = deviceInfo.indexOf("manufacturer data: ") + 19;
        int manuEnd = deviceInfo.indexOf(",", manuStart);
        String manufacturerData = deviceInfo.substring(manuStart, manuEnd);

        // Extract Pressure (Little Endian) and Convert to PSI
        long pressureRaw = returnData(manufacturerData, 16);
        float pressurePSI = (pressureRaw / 100000.0) * 14.5038;

        // Extract Temperature (Little Endian) and Convert to °C
        long temperatureRaw = returnData(manufacturerData, 24);
        float temperatureC = temperatureRaw / 100.0;

        // Extract Battery Percentage
        int batteryPercentage = retByte(manufacturerData, 32);

        // Extract Alarm Flag
        int alarmFlag = retByte(manufacturerData, 34);

        

        // Extract Service UUID
        int uuidStart = deviceInfo.indexOf("serviceUUID: ") + 13;
        int uuidEnd = deviceInfo.indexOf(",", uuidStart);
        String serviceUUID = deviceInfo.substring(uuidStart, uuidEnd);

        // Extract RSSI
        int rssiStart = deviceInfo.indexOf("rssi: ") + 6;
        String rssiValue = deviceInfo.substring(rssiStart);

        // Print extracted values
        Serial.println("Device Name: " + deviceName);
        Serial.println("Device Address: " + deviceAddress);
        Serial.println("Service UUID: " + serviceUUID);
        Serial.println("RSSI: " + rssiValue);
        Serial.println("----------------------------");
        // Print extracted values
        Serial.println("Extracted Data:");
        Serial.print("Pressure (PSI): ");
        Serial.println(pressurePSI, 2); // Print with 2 decimal places
        Serial.print("Temperature (°C): ");
        Serial.println(temperatureC, 2);
        Serial.print("Battery Percentage: ");
        Serial.println(batteryPercentage);
        Serial.print("Alarm Flag: ");
        Serial.println(alarmFlag == 0 ? "OK" : "No Pressure Alarm");
      }
    }
  }
};

BLEScan* pBLEScan;

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE scan...");

  // Initialize BLE device
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); // Create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);  // Active scan to get scan response data
}

void loop() {
  // Use a pointer to receive the scan results
  BLEScanResults* foundDevices = pBLEScan->start(5, false);

  // Free memory used by results
  pBLEScan->clearResults();

  // Wait a bit before starting the next scan
  delay(1000);
}
