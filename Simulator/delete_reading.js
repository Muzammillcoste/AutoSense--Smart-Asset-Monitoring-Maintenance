// Import the Axios library for making HTTP requests
const axios = require('axios')

// Define the webhook URL
const DELETE_READING_WEBHOOK =
  'https://swift-cloud.ephlux.com/api-swift/ned/workflow/jseji3JgMB?SWIFT_API_KEY=S~G6Py/S.wGnIxFdLq7uW2WX'

// Function to delete a reading by reading_id
async function deleteReading(readingId) {
  try {
    // Define the payload with the reading ID
    const payload = {
      reading_id: readingId // The ID of the reading to be deleted
    }

    // Make the DELETE request to the webhook URL
    const response = await axios.delete(DELETE_READING_WEBHOOK, {
      data: payload
    })

    // Log the success response
    console.log(
      `Reading with ID ${readingId} deleted successfully:`,
      response.data
    )
  } catch (error) {
    // Handle and log errors
    console.error(
      `Error deleting reading with ID ${readingId}:`,
      error.response?.data || error.message
    )
  }
}

// Example: Delete a reading with a specific ID
deleteReading(1, 100) // Replace 789 with the actual reading ID
