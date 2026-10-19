public class VehicleStatusService {
    @future(callout=true)
    public static void sendStatusToSwift(List<String> vehicleIds, List<String> statuses) {
        for (Integer i = 0; i < vehicleIds.size(); i++) {
            String vehicleId = vehicleIds[i];
            String status = statuses[i];

            HttpRequest req = new HttpRequest();
            req.setEndpoint('https://swift-cloud.ephlux.com/api-swift/ned/workflow/LWSNalCzP_?SWIFT_API_KEY=YOUR_SWIFT_KEY_UPDATE_STATUS');
            req.setMethod('POST');
            req.setHeader('Content-Type', 'application/x-www-form-urlencoded');

            String payload = 'vehicle_id=' + EncodingUtil.urlEncode(vehicleId, 'UTF-8') +
                             '&status=' + EncodingUtil.urlEncode(status, 'UTF-8');

            req.setBody(payload);

            Http http = new Http();
            try {
                HttpResponse res = http.send(req);
                System.debug('Response: ' + res.getBody());
            } catch (Exception e) {
                System.debug('Error in callout: ' + e.getMessage());
            }
        }
    }
}