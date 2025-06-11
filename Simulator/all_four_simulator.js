const axios = require('axios')

// ### Configuration
const POST_SENSOR_READING_WEBHOOK =
  'https://swift-cloud.ephlux.com/api-swift/ned/integration/n1EBuKoSmc?SWIFT_API_KEY=Bc4JfnH9ht5FMKxTNXQZKL_8WsSDR+'
const POST_ALERT_WEBHOOK =
  'https://swift-cloud.ephlux.com/api-swift/ned/workflow/fzuttyO91i?SWIFT_API_KEY=6rrI6H1.VrbGvAjCEfTr-xXW'
const UPDATE_STATUS_WEBHOOK =
  'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LWSNalCzP_?SWIFT_API_KEY=BBtf-pvchwljttPIrm300xCJRzb93'

// ### Vehicle and Sensor Details
const vehicles = [
  {
    vehicle_id: 1,
    make: 'Toyota',
    model: 'Yaris',
    status: 'active',
    alerts: 0
  },
  {
    vehicle_id: 2,
    make: 'Toyota',
    model: 'Corolla',
    status: 'active',
    alerts: 0
  },
  {
    vehicle_id: 3,
    make: 'Suzuki',
    model: 'Cultus',
    status: 'active',
    alerts: 0
  },
  {
    vehicle_id: 4,
    make: 'Toyota',
    model: 'Fortuner',
    status: 'active',
    alerts: 0
  }
]

// Distinct starting points for vehicles in Houston
const initialVehicleLocations = [
  { lat: 24.93, lng: 67.1453 },
  { lat: 24.931, lng: 67.1383 },
  { lat: 24.9402, lng: 67.1053 },
  { lat: 24.9203, lng: 67.1113 },
  { lat: 24.9104, lng: 67.1253 }
]

// Initialize vehicle positions
const vehiclePositions = {}
vehicles.forEach((vehicle, index) => {
  vehiclePositions[vehicle.vehicle_id] = {
    lat: initialVehicleLocations[index % initialVehicleLocations.length].lat,
    lng: initialVehicleLocations[index % initialVehicleLocations.length].lng
  }
})

// Sensors include GPS, TPMS, and Temperature for each vehicle
const sensors = vehicles.flatMap((vehicle) => [
  {
    sensor_id: vehicle.vehicle_id * 10 + 1,
    vehicle_id: vehicle.vehicle_id,
    sensor_type_id: 1
  },
  {
    sensor_id: vehicle.vehicle_id * 10 + 2,
    vehicle_id: vehicle.vehicle_id,
    sensor_type_id: 2
  },
  {
    sensor_id: vehicle.vehicle_id * 10 + 3,
    vehicle_id: vehicle.vehicle_id,
    sensor_type_id: 3
  }
])

// ### State Management
const tyrePressureLevels = {}
const temperatureLevels = {}
vehicles.forEach((v) => {
  tyrePressureLevels[v.vehicle_id] = {
    front_left: {
      pressure: 20 + Math.random() * 12,
      temperature: 20 + Math.random() * 70
    },
    front_right: {
      pressure: 20 + Math.random() * 12,
      temperature: 20 + Math.random() * 70
    },
    rear_left: {
      pressure: 20 + Math.random() * 12,
      temperature: 20 + Math.random() * 70
    },
    rear_right: {
      pressure: 20 + Math.random() * 12,
      temperature: 20 + Math.random() * 70
    }
  }
  temperatureLevels[v.vehicle_id] = 30 + Math.random() * 70 // 30 to 100°C
})

// Counters
let readingCounter = 1
let alertCounter = 1

// ### Utility Functions
async function sendAlert(alertData) {
  const alert = {
    alert_id: alertCounter++,
    ...alertData,
    status: 'Active',
    timestamp: new Date().toISOString()
  }
  try {
    await axios.post(POST_ALERT_WEBHOOK, alert)
    console.log(`Alert Sent: ${JSON.stringify(alert)}`)
    updateVehicleAlerts(alert.vehicle_id)
  } catch (error) {
    console.error('Failed to send alert:', error.message)
  }
}

async function updateVehicleStatus(vehicleId, status) {
  try {
    vehicleId = String(vehicleId)
    await axios.post(UPDATE_STATUS_WEBHOOK, { vehicle_id: vehicleId, status })
    console.log(`Vehicle ${vehicleId} status updated to ${status}`)
  } catch (error) {
    console.error(
      `Failed to update vehicle ${vehicleId} status:`,
      error.message
    )
  }
}

function updateVehicleAlerts(vehicleId) {
  const vehicle = vehicles.find(
    (v) => String(v.vehicle_id) === String(vehicleId)
  )
  if (vehicle) {
    vehicle.alerts += 1
    if (vehicle.alerts >= 2) {
      vehicle.status = 'Critical'
    } else if (vehicle.alerts === 1) {
      vehicle.status = 'Warning'
    }
    updateVehicleStatus(vehicleId, vehicle.status)
  }
}

async function sendReading(reading) {
  try {
    await axios.post(POST_SENSOR_READING_WEBHOOK, reading)
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

// ### Sensor Reading Generators
function generateTPMSReading(sensor_id, vehicle_id) {
  const reading_id = readingCounter++
  const currentData = { ...tyrePressureLevels[vehicle_id] }
  const newData = {
    front_left: {
      pressure: currentData.front_left.pressure - (0.1 + Math.random() * 0.4),
      temperature:
        currentData.front_left.temperature + (0.5 + Math.random() * 1)
    },
    front_right: {
      pressure: currentData.front_right.pressure - (0.1 + Math.random() * 0.4),
      temperature:
        currentData.front_right.temperature + (0.5 + Math.random() * 1)
    },
    rear_left: {
      pressure: currentData.rear_left.pressure - (0.1 + Math.random() * 0.4),
      temperature: currentData.rear_left.temperature + (0.5 + Math.random() * 1)
    },
    rear_right: {
      pressure: currentData.rear_right.pressure - (0.1 + Math.random() * 0.4),
      temperature:
        currentData.rear_right.temperature + (0.5 + Math.random() * 1)
    }
  }

  const reading = {
    reading_id,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: {
      front_left: {
        pressure: Number(newData.front_left.pressure.toFixed(2)),
        temperature: Number(newData.front_left.temperature.toFixed(2))
      },
      front_right: {
        pressure: Number(newData.front_right.pressure.toFixed(2)),
        temperature: Number(newData.front_right.temperature.toFixed(2))
      },
      rear_left: {
        pressure: Number(newData.rear_left.pressure.toFixed(2)),
        temperature: Number(newData.rear_left.temperature.toFixed(2))
      },
      rear_right: {
        pressure: Number(newData.rear_right.pressure.toFixed(2)),
        temperature: Number(newData.rear_right.temperature.toFixed(2))
      }
    }
  }

  const alerts = []

  // Check tire pressures
  ;['front_left', 'front_right', 'rear_left', 'rear_right'].forEach((tyre) => {
    if (newData[tyre].pressure <= 25) {
      alerts.push({
        vehicle_id,
        reading_id,
        sensor_id,
        alert_type: `Tyre Pressure (${tyre.replace('_', ' ')})`,
        severity: 'High',
        description: `Tyre pressure critically low in ${tyre.replace('_', ' ')}`
      })
      newData[tyre].pressure = 32 // Reset pressure for next cycle
    }
    // Reset tire temperature if >= 80°C, but do not generate an alert
    if (newData[tyre].temperature >= 80) {
      newData[tyre].temperature = 20
    }
  })

  // Update state for next cycle
  tyrePressureLevels[vehicle_id] = newData

  return { reading, alerts }
}

function generateTemperatureReading(sensor_id, vehicle_id) {
  const reading_id = readingCounter++
  let engine_temperature = temperatureLevels[vehicle_id]
  engine_temperature += 0.5 + Math.random() * 1 // Increase by 0.5 to 1.5°C

  const reading = {
    reading_id,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: {
      engine_temperature: Number(engine_temperature.toFixed(2))
    }
  }

  const alerts = []
  if (engine_temperature >= 80) {
    alerts.push({
      vehicle_id,
      reading_id,
      sensor_id,
      alert_type: 'Temperature',
      severity: 'Medium',
      description: 'Temperature critically high'
    })
    engine_temperature = 30 // Reset for next cycle
  }

  // Update state for next cycle
  temperatureLevels[vehicle_id] = engine_temperature

  return { reading, alerts }
}

function getNextPosition(vehicle_id) {
  const currentPosition = vehiclePositions[vehicle_id]
  const latChange = (Math.random() * 0.02 - 0.01).toFixed(6)
  const lngChange = (Math.random() * 0.02 - 0.01).toFixed(6)

  const newLat = Number((currentPosition.lat + Number(latChange)).toFixed(6))
  const newLng = Number((currentPosition.lng + Number(lngChange)).toFixed(6))

  vehiclePositions[vehicle_id] = { lat: newLat, lng: newLng }
  return { lat: newLat, lng: newLng }
}

function generateGPSReading(sensor_id, vehicle_id) {
  const reading_id = readingCounter++
  const position = getNextPosition(vehicle_id)
  const reading = {
    reading_id,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: {
      latitude: position.lat,
      longitude: position.lng,
      speed: Number((Math.random() * 60 + 40).toFixed(2))
    }
  }
  return { reading, alerts: [] }
}

const sensorGenerators = {
  1: generateGPSReading,
  2: generateTPMSReading,
  3: generateTemperatureReading
}

// ### Simulate Sensor Readings
function simulateSensorReadings() {
  vehicles.forEach((vehicle) => {
    if (vehicle.status === 'Critical') {
      vehicle.status = 'Active'
      vehicle.alerts = 0 // Reset alerts count to 0
      updateVehicleStatus(vehicle.vehicle_id, 'Active')
    }
    sensors
      .filter(
        (sensor) => String(sensor.vehicle_id) === String(vehicle.vehicle_id)
      )
      .forEach((sensor) => {
        const generator = sensorGenerators[sensor.sensor_type_id]
        if (generator) {
          const { reading, alerts } = generator(
            sensor.sensor_id,
            vehicle.vehicle_id
          )
          sendReading(reading)
          alerts.forEach((alert) => sendAlert(alert))
        }
      })
  })
}

// ### Run the Simulation
setInterval(simulateSensorReadings, 3000)
console.log('Sensor simulator is running...')
