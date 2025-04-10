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
  { lat: 29.7604, lng: -95.3698 },
  { lat: 29.7499, lng: -95.3584 },
  { lat: 29.7321, lng: -95.342 },
  { lat: 29.7602, lng: -95.4025 },
  { lat: 29.7188, lng: -95.426 }
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
    front_left: 20 + Math.random() * 12, // 20 to 32 psi
    front_right: 20 + Math.random() * 12, // 20 to 32 psi
    rear_left: 20 + Math.random() * 12, // 20 to 32 psi
    rear_right: 20 + Math.random() * 12 // 20 to 32 psi
  }
  temperatureLevels[v.vehicle_id] = 30 + Math.random() * 70 // 30 to 100°C
})

// Alert Counter
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
    if (vehicle.alerts > 3) {
      vehicle.status = 'Critical'
    } else if (vehicle.alerts >= 1) {
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
  const currentPressures = { ...tyrePressureLevels[vehicle_id] }
  const newPressures = {
    front_left: currentPressures.front_left - (0.1 + Math.random() * 0.4),
    front_right: currentPressures.front_right - (0.1 + Math.random() * 0.4),
    rear_left: currentPressures.rear_left - (0.1 + Math.random() * 0.4),
    rear_right: currentPressures.rear_right - (0.1 + Math.random() * 0.4)
  }

  Object.entries(newPressures).forEach(([tyre, pressure]) => {
    if (pressure <= 25) {
      sendAlert({
        vehicle_id,
        sensor_id,
        alert_type: `Tyre Pressure (${tyre.replace('_', ' ')})`,
        severity: 'High',
        description: `Tyre pressure critically low in ${tyre.replace('_', ' ')}`
      })
      newPressures[tyre] = 32
    }
  })

  tyrePressureLevels[vehicle_id] = newPressures

  return {
    reading_id: readingCounter++,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: {
      tyre_pressure: {
        front_left: Number(newPressures.front_left.toFixed(2)),
        front_right: Number(newPressures.front_right.toFixed(2)),
        rear_left: Number(newPressures.rear_left.toFixed(2)),
        rear_right: Number(newPressures.rear_right.toFixed(2))
      }
    }
  }
}

function generateTemperatureReading(sensor_id, vehicle_id) {
  let temperature = temperatureLevels[vehicle_id]
  temperature += 0.5 + Math.random() * 1 // Increase by 0.5 to 1.5°C
  if (temperature >= 80) {
    sendAlert({
      vehicle_id,
      sensor_id,
      alert_type: 'Temperature',
      severity: 'Medium',
      description: 'Temperature critically high'
    })
    temperature = 30
  }
  temperatureLevels[vehicle_id] = temperature

  return {
    reading_id: readingCounter++,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: {
      temperature: Number(temperature.toFixed(2))
    }
  }
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
  const position = getNextPosition(vehicle_id)
  return {
    reading_id: readingCounter++,
    sensor_id,
    vehicle_id,
    timestamp: new Date().toISOString(),
    value: {
      latitude: position.lat,
      longitude: position.lng,
      speed: Number((Math.random() * 60 + 40).toFixed(2))
    }
  }
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
      updateVehicleStatus(vehicle.vehicle_id, 'Active')
    }
    sensors
      .filter(
        (sensor) => String(sensor.vehicle_id) === String(vehicle.vehicle_id)
      )
      .forEach((sensor) => {
        const generator = sensorGenerators[sensor.sensor_type_id]
        if (generator) {
          const reading = generator(sensor.sensor_id, vehicle.vehicle_id)
          sendReading(reading)
        }
      })
  })
}

// ### Run the Simulation
setInterval(simulateSensorReadings, 10000)
console.log('Sensor simulator is running...')
