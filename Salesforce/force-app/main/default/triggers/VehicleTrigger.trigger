trigger VehicleTrigger on Vehicle__c (after update) {
    List<Vehicle__c> changedVehicles = new List<Vehicle__c>();

    for (Integer i = 0; i < Trigger.new.size(); i++) {
        Vehicle__c oldRec = Trigger.old[i];
        Vehicle__c newRec = Trigger.new[i];

        if (oldRec.Status__c != newRec.Status__c) {
            changedVehicles.add(newRec);
        }
    }

    if (!changedVehicles.isEmpty()) {
        // Extract required data (vehicle_id and status)
        List<String> vehicleIds = new List<String>();
        List<String> statuses = new List<String>();

        for (Vehicle__c v : changedVehicles) {
            vehicleIds.add(String.valueOf(v.Vehicle_id__c));
            statuses.add(v.Status__c);
        }

        VehicleStatusService.sendStatusToSwift(vehicleIds, statuses);
    }
}