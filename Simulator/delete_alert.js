// Import the Axios library for making HTTP requests
const axios = require('axios')

// Define the webhook URL
const DELETE_ALERT_WEBHOOK =
  'https://swift-cloud.ephlux.com/api-swift/ned/workflow/jseji3JgMB?SWIFT_API_KEY=S~G6Py/S.wGnIxFdLq7uW2WX'

// Function to delete an alert
async function deleteAlert(alertId) {
  try {
    // Define the payload with the alert ID
    const payload = {
      alert_id: alertId // The ID of the alert to be deleted
    }

    // Make the DELETE request to the webhook URL
    const response = await axios.delete(DELETE_ALERT_WEBHOOK, { data: payload })

    // Log the success response
    console.log(`Alert with ID ${alertId} deleted successfully:`, response.data)
  } catch (error) {
    // Handle and log errors
    console.error(
      `Error deleting alert with ID ${alertId}:`,
      error.response?.data || error.message
    )
  }
}

// Example: Delete an alert with a specific ID
deleteAlert('675fde77da29ce4c1fcb9d99')
