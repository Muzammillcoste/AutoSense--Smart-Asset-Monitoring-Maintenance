// Import the Axios library for making HTTP requests
const axios = require('axios')

// Define the webhook URL and the API key
const WEBHOOK_URL =
  'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LWSNalCzP_?SWIFT_API_KEY=BBtf-pvchwljttPIrm300xCJRzb93'

// Function to update the vehicle status
async function updateVehicleStatus(vehicleId, status) {
  try {
    // Define the payload to be sent in the POST request
    const payload = {
      vehicle_id: vehicleId, // Vehicle ID to update
      status: status // New status
    }

    // Make the POST request to the webhook URL
    const response = await axios.post(WEBHOOK_URL, payload)

    // Log the success response
    console.log(
      `Vehicle ID ${vehicleId} status updated successfully:`,
      response.data
    )
  } catch (error) {
    // Handle and log errors
    console.error(
      `Error updating vehicle ID ${vehicleId} status:`,
      error.response?.data || error.message
    )
  }
}

// Function to update the status of multiple vehicles
async function updateMultipleVehiclesStatus(startId, endId, status) {
  for (let vehicleId = startId; vehicleId <= endId; vehicleId++) {
    vehicleId = String(vehicleId) // Ensure vehicleId is a string
    await updateVehicleStatus(vehicleId, status) // Update each vehicle status
  }
}

// Update the status of vehicles from ID 1 to 5 to 'Active'
updateMultipleVehiclesStatus(1, 4, 'Active')
