public class AlertWebhookService {

    public static void fetchAndStoreAlerts() {
        Http http = new Http();
        HttpRequest req = new HttpRequest();

        req.setMethod('POST');
        req.setEndpoint('https://swift-cloud.ephlux.com/api-swift/ned/workflow/xuRob0A4mf?SWIFT_API_KEY=YOUR_SWIFT_KEY_ALERTS');
        req.setHeader('Content-Type', 'application/json');
        req.setBody('{}');

        HttpResponse res = http.send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> fullResponse = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> actions = (List<Object>) fullResponse.get('actions');

            if (!actions.isEmpty()) {
                Map<String, Object> action = (Map<String, Object>) actions[0];
                List<Object> alertList = (List<Object>) action.get('obj');

                Set<String> alertIds = new Set<String>();
                for (Object a : alertList) {
                    Map<String, Object> alert = (Map<String, Object>) a;
                    alertIds.add(String.valueOf(alert.get('alert_id')));
                }

                Map<String, Vehicle_Alert__c> existingAlerts = new Map<String, Vehicle_Alert__c>();
                for (Vehicle_Alert__c existing : [
                    SELECT Alert_ID__c FROM Vehicle_Alert__c
                    WHERE Alert_ID__c IN :alertIds
                ]) {
                    existingAlerts.put(existing.Alert_ID__c, existing);
                }

                List<Vehicle_Alert__c> toInsert = new List<Vehicle_Alert__c>();
                for (Object a : alertList) {
                    Map<String, Object> alert = (Map<String, Object>) a;
                    String alertId = String.valueOf(alert.get('alert_id'));

                    if (!existingAlerts.containsKey(alertId)) {
                        Vehicle_Alert__c va = new Vehicle_Alert__c();
                        va.Alert_ID__c     = alertId;
                        va.Vehicle_ID__c   = String.valueOf(alert.get('vehicle_id'));
                        va.Sensor_ID__c    = String.valueOf(alert.get('sensor_id'));
                        va.Reading_ID__c   = String.valueOf(alert.get('reading_id'));
                        va.Status__c       = String.valueOf(alert.get('status'));
                        va.Alert_Type__c   = String.valueOf(alert.get('alert_type'));
                        va.Severity__c     = String.valueOf(alert.get('severity'));
                        va.Description__c  = String.valueOf(alert.get('description'));
                        toInsert.add(va);
                    }
                }

                if (!toInsert.isEmpty()) {
                    insert toInsert;
                    System.debug('Inserted alerts: ' + toInsert.size());
                } else {
                    System.debug('No new alerts to insert.');
                }
            } else {
                System.debug('No actions found in response.');
            }
        } else {
            System.debug('Callout failed with status code: ' + res.getStatusCode());
        }
    }
}