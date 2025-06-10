public with sharing class VehicleWebhookService {

    public static void fetchAndStoreVehicles() {
        // Build HTTP request
        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1');
        req.setMethod('POST');

        Http http = new Http();
        HttpResponse res;

        try {
            res = http.send(req);
            if (res.getStatusCode() == 200) {
                parseAndStoreVehicles(res.getBody());
            } else {
                System.debug('Failed response: ' + res.getStatus());
            }
        } catch (Exception e) {
            System.debug('Callout error: ' + e.getMessage());
        }
    }

    private static void parseAndStoreVehicles(String responseBody) {
        // Deserialize the JSON into a wrapper
        VehicleResponseWrapper parsed = (VehicleResponseWrapper) JSON.deserialize(responseBody, VehicleResponseWrapper.class);

        if (parsed != null && !parsed.isError && parsed.actions != null && !parsed.actions.isEmpty()) {
            List<VehicleObj> vehicleData = parsed.actions[0].obj;
            if (vehicleData != null && !vehicleData.isEmpty()) {
                
                // Collect all incoming vehicle IDs
                Set<Decimal> incomingIds = new Set<Decimal>();
                for (VehicleObj v : vehicleData) {
                    if (v.vehicle_id != null) incomingIds.add(Decimal.valueOf(v.vehicle_id));
                }

                // Query existing vehicles by Vehicle_id__c
                Map<Decimal, Vehicle__c> existingMap = new Map<Decimal, Vehicle__c>();
                for (Vehicle__c v : [
                    SELECT Id, Vehicle_id__c, Make__c, Model__c, Year__c, Vin__c, License_plate__c, Status__c
                    FROM Vehicle__c
                    WHERE Vehicle_id__c IN :incomingIds
                ]) {
                    existingMap.put(v.Vehicle_id__c, v);
                }

                // Prepare lists for insert and update
                List<Vehicle__c> toInsert = new List<Vehicle__c>();
                List<Vehicle__c> toUpdate = new List<Vehicle__c>();

                for (VehicleObj v : vehicleData) {
                    Decimal vehicleId = Decimal.valueOf(v.vehicle_id);
                    
                    if (existingMap.containsKey(vehicleId)) {
                        // 🔁 UPDATE logic: Update existing vehicle
                        Vehicle__c existing = existingMap.get(vehicleId);
                        existing.Make__c = v.make;
                        existing.Model__c = v.model;
                        existing.Year__c = Decimal.valueOf(v.year);
                        existing.Vin__c = v.vin;
                        existing.License_plate__c = v.license_plate;
                        existing.Status__c = v.status;
                        toUpdate.add(existing);
                    } else {
                        // ✅ INSERT logic: New vehicle
                        Vehicle__c newVehicle = new Vehicle__c(
                            Vehicle_id__c = vehicleId,
                            Make__c = v.make,
                            Model__c = v.model,
                            Year__c = Decimal.valueOf(v.year),
                            Vin__c = v.vin,
                            License_plate__c = v.license_plate,
                            Status__c = v.status
                        );
                        toInsert.add(newVehicle);
                    }
                }

                // DML operations
                if (!toInsert.isEmpty()) {
                    insert toInsert;
                    System.debug('Inserted ' + toInsert.size() + ' new vehicles.');
                }
                if (!toUpdate.isEmpty()) {
                    update toUpdate;
                    System.debug('Updated ' + toUpdate.size() + ' existing vehicles.');
                }
                if (toInsert.isEmpty() && toUpdate.isEmpty()) {
                    System.debug('No changes detected.');
                }
            }
        }
    }

    // Wrapper classes for JSON parsing
    public class VehicleResponseWrapper {
        public Boolean isError;
        public Integer status;
        public String message;
        public List<ActionWrapper> actions;
    }

    public class ActionWrapper {
        public Boolean isError;
        public List<VehicleObj> obj;
        public Integer records;
    }

    public class VehicleObj {
        public String vehicle_id;
        public String make;
        public String model;
        public String year;
        public String vin;
        public String license_plate;
        public String status;
        public String createdAt;
        public String lastModified;
        public String createdBy;
        public String updatedBy;
    }
}