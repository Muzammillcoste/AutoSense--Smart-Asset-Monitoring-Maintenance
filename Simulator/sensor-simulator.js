const axios = require('axios')

// Configuration
const POST_SENSOR_READING_WEBHOOK =
  'https://swift-cloud.ephlux.com/api-swift/ned/integration/n1EBuKoSmc?SWIFT_API_KEY=Bc4JfnH9ht5FMKxTNXQZKL_8WsSDR+'
const POST_ALERT_WEBHOOK =
  'https://swift-cloud.ephlux.com/api-swift/ned/workflow/fzuttyO91i?SWIFT_API_KEY=6rrI6H1.VrbGvAjCEfTr-xXW'

// Vehicle and Sensor Details
const vehicles = [
  { vehicle_id: 1, make: 'Kia', model: 'Sportage', status: 'active' },
  { vehicle_id: 2, make: 'Toyota', model: 'Corolla', status: 'active' },
  { vehicle_id: 3, make: 'Honda', model: 'Civic', status: 'critical' },
  { vehicle_id: 4, make: 'Suzuki', model: 'Cultus', status: 'active' },
  { vehicle_id: 5, make: 'Toyota', model: 'Fortuner', status: 'active' }
]

// Distinct starting points for vehicles
const initialVehicleLocations = [
  { lat: 24.8223, lng: 67.0356 }, // Near Teen Talwar
  { lat: 24.8147, lng: 67.0482 }, // Near PNS Shifa
  { lat: 24.8334, lng: 67.0237 }, // Near Clifton Bridge
  { lat: 24.8471, lng: 67.0281 }, // Near Dolmen Mall
  { lat: 24.8395, lng: 67.0439 } // Near Frere Hall
]

// Initialize vehicle positions with distinct starting points
const vehiclePositions = {}
vehicles.forEach((vehicle, index) => {
  vehiclePositions[vehicle.vehicle_id] = {
    lat: initialVehicleLocations[index % initialVehicleLocations.length].lat,
    lng: initialVehicleLocations[index % initialVehicleLocations.length].lng
  }
})

const sensors = vehicles.flatMap((vehicle) => [
  {
    sensor_id: vehicle.vehicle_id * 10 + 1,
    vehicle_id: vehicle.vehicle_id,
    sensor_type_id: 1
  }, // GPS
  {
    sensor_id: vehicle.vehicle_id * 10 + 2,
    vehicle_id: vehicle.vehicle_id,
    sensor_type_id: 2
  }, // TPMS
  {
    sensor_id: vehicle.vehicle_id * 10 + 3,
    vehicle_id: vehicle.vehicle_id,
    sensor_type_id: 3
  } // Fuel
])

// State Management
const fuelLevels = {},
  tyrePressureLevels = {},
  temperatureLevels = {}
vehicles.forEach((v) => {
  fuelLevels[v.vehicle_id] = 20 + Math.random() * 10 // Lower starting fuel
  tyrePressureLevels[v.vehicle_id] = 150 + Math.random() * 50 // Lower starting tyre pressure
  temperatureLevels[v.vehicle_id] = 40 // Slightly higher starting temperature
})

// Alert Counter
let readingCounter = 1
let alertCounter = 1

// Utility Functions
async function sendAlert({
  vehicle_id,
  sensor_id,
  alert_type,
  severity,
  description
}) {
  const alert = {
    alert_id: alertCounter++,
    vehicle_id,
    sensor_id,
    alert_type,
    severity,
    description,
    status: 'Active',
    timestamp: new Date().toISOString()
  }
  try {
    await axios.post(POST_ALERT_WEBHOOK, alert, {
      headers: { 'Content-Type': 'application/json' }
    })
    console.log(`Alert Sent: ${JSON.stringify(alert)}`)
  } catch (error) {
    console.error('Failed to send alert:', error.message)
  }
}

async function sendReading(reading) {
  try {
    await axios.post(POST_SENSOR_READING_WEBHOOK, reading, {
      headers: { 'Content-Type': 'application/json' }
    })
    console.log(
      `Sent reading ${reading.reading_id} for sensor ${reading.sensor_id}`
    )
  } catch (error) {
    console.error(
      `Failed to send reading ${reading.reading_id}:`,
      error.message
    )
  }
}

// Sensor Reading Generators
function generateFuelReading(sensor_id, vehicle_id) {
  let fuelLevel = fuelLevels[vehicle_id]
  fuelLevel -= Number((Math.random() * 5 + 2).toFixed(2)) // Faster drop in fuel
  if (fuelLevel <= 10) {
    sendAlert({
      vehicle_id,
      sensor_id,
      alert_type: 'Fuel Level',
      severity: 'Critical',
      description: 'Fuel level critically low'
    })
    fuelLevel = 20 + Math.random() * 10 // Refill for simulation
  }
  fuelLevels[vehicle_id] = fuelLevel

  return {
    reading_id: readingCounter++,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: { fuel_level: fuelLevel.toFixed(2) }
  }
}

function generateTPMSReading(sensor_id, vehicle_id) {
  let tyrePressure = tyrePressureLevels[vehicle_id]
  let temperature = temperatureLevels[vehicle_id]

  tyrePressure -= Number((Math.random() * 10 + 2).toFixed(2)) // Faster tyre pressure drop
  if (tyrePressure <= 100) {
    sendAlert({
      vehicle_id,
      sensor_id,
      alert_type: 'Tyre Pressure',
      severity: 'High',
      description: 'Tyre pressure critically low'
    })
    tyrePressure = 150 + Math.random() * 50 // Reset pressure for simulation
  }

  temperature += Number((Math.random() * 3).toFixed(2)) // Faster temperature rise
  if (temperature >= 45) {
    sendAlert({
      vehicle_id,
      sensor_id,
      alert_type: 'Temperature',
      severity: 'Medium',
      description: 'Temperature critically high'
    })
    temperature = 35 + Math.random() * 5 // Reset temperature for simulation
  }

  tyrePressureLevels[vehicle_id] = tyrePressure
  temperatureLevels[vehicle_id] = temperature

  return {
    reading_id: readingCounter++,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: {
      tyre_pressure: tyrePressure.toFixed(2),
      temperature: temperature.toFixed(2)
    }
  }
}

// Updated getNextPosition function to simulate movements
function getNextPosition(vehicle_id) {
  const currentPosition = vehiclePositions[vehicle_id]
  const currentLat = currentPosition.lat
  const currentLng = currentPosition.lng

  // Generate random small increments for latitude and longitude
  const latChange = (Math.random() * 0.02 - 0.01).toFixed(6) // Random change between -0.01 and 0.01
  const lngChange = (Math.random() * 0.02 - 0.01).toFixed(6) // Random change between -0.01 and 0.01

  const newLat = parseFloat((currentLat + parseFloat(latChange)).toFixed(6))
  const newLng = parseFloat((currentLng + parseFloat(lngChange)).toFixed(6))

  // Update the vehicle's position with the new location
  vehiclePositions[vehicle_id] = {
    lat: newLat,
    lng: newLng
  }

  return {
    lat: newLat,
    lng: newLng
  }
}

function generateGPSReading(sensor_id, vehicle_id) {
  const position = getNextPosition(vehicle_id)
  return {
    reading_id: readingCounter++,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: {
      latitude: position.lat,
      longitude: position.lng,
      speed: Number((Math.random() * 60 + 40).toFixed(2)) // Speed between 40 and 100 km/h
    }
  }
}

const sensorGenerators = {
  1: generateGPSReading,
  2: generateTPMSReading,
  3: generateFuelReading
}

// Simulate Sensor Readings
function simulateSensorReadings() {
  vehicles.forEach((vehicle) => {
    sensors
      .filter((sensor) => sensor.vehicle_id === vehicle.vehicle_id)
      .forEach((sensor) => {
        const generator = sensorGenerators[sensor.sensor_type_id]
        if (generator) {
          const reading = generator(sensor.sensor_id, vehicle.vehicle_id)
          sendReading(reading)
        }
      })
  })
}

setInterval(simulateSensorReadings, 3000)
console.log('Sensor simulator is running...')
