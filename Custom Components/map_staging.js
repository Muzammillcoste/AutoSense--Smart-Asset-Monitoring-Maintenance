const MapComponent = () => {
  const [vehicleData, setVehicleData] = useState([])
  const [sensorReadings, setSensorReadings] = useState([])
  const [alertData, setAlertData] = useState([]) // State for dynamic alerts
  const [selectedVehicleId, setSelectedVehicleId] = useState(null)

  const vehicleWebhook =
    'https://swift-staging.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1'
  const sensorWebhook =
    'https://swift-staging.ephlux.com/api-swift/ned/workflow/zXSGrWOgyg?SWIFT_API_KEY=pB-qorkYtZLfZ9ODofzUnv3OcPA'
  const alertsWebhook =
    'https://swift-staging.ephlux.com/api-swift/ned/workflow/xuRob0A4mf?SWIFT_API_KEY=S1/JT2c/77dtlkCR+qQtZW5s+QX'

  // Fetch Vehicle Data
  const fetchVehicleData = async () => {
    try {
      const response = await axios.post(vehicleWebhook, {})
      const vehicles = response.data.actions[0].obj || []
      console.log('Vehicles', vehicles)
      setVehicleData(vehicles)
    } catch (error) {
      console.error('Error fetching vehicle data:', error)
    }
  }

  // Fetch Sensor Data
  const fetchSensorData = async () => {
    try {
      const response = await axios.post(sensorWebhook, {})
      const sensors = response.data.actions[0].obj || []
      console.log('Sensors', sensors)
      setSensorReadings(sensors)
    } catch (error) {
      console.error('Error fetching sensor data:', error)
    }
  }

  // Fetch Alerts Data Dynamically
  const fetchAlertData = async () => {
    try {
      const response = await axios.post(alertsWebhook, {})
      const alerts = response.data.actions[0].obj || []
      // Map alerts with vehicle name
      const enrichedAlerts = alerts.map((alert) => {
        const vehicle = vehicleData.find(
          (v) => v.vehicle_id === alert.vehicle_id
        )
        const vehicleName = vehicle
          ? `${vehicle.make} ${vehicle.model}`
          : 'Unknown Vehicle'
        return { ...alert, vehicle_name: vehicleName }
      })
      setAlertData(enrichedAlerts)
    } catch (error) {
      console.error('Error fetching alerts data:', error)
    }
  }

  // Fetch all data periodically
  useEffect(() => {
    fetchVehicleData()
    fetchSensorData()
    fetchAlertData()
    const interval = setInterval(() => {
      fetchSensorData()
      fetchAlertData()
    }, 1000)
    return () => clearInterval(interval)
  }, [vehicleData])

  // Calculate vehicle locations dynamically
  const vehicleLocations = {}
  sensorReadings.forEach((reading) => {
    if (reading.value.latitude && reading.value.longitude) {
      vehicleLocations[reading.vehicle_id] = {
        lat: reading.value.latitude,
        lng: reading.value.longitude
      }
    }
  })

  const calculateAverageCenter = () => {
    const coordinates = Object.values(vehicleLocations)
    if (coordinates.length === 0) return { lat: 24.8607, lng: 67.0011 }
    const total = coordinates.reduce(
      (acc, curr) => {
        acc.lat += curr.lat
        acc.lng += curr.lng
        return acc
      },
      { lat: 0, lng: 0 }
    )
    return {
      lat: total.lat / coordinates.length,
      lng: total.lng / coordinates.length
    }
  }

  const defaultCenter = calculateAverageCenter()

  const latestReadings = vehicleData.map((vehicle) => {
    const readings = sensorReadings
      .filter((reading) => reading.vehicle_id === vehicle.vehicle_id)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    const latestSpeed =
      readings.find((r) => r.value.speed !== undefined)?.value.speed || 0
    const latestTyrePressure =
      readings.find((r) => r.value.tyre_pressure)?.value.tyre_pressure || 0
    const latestFuelLevel =
      readings.find((r) => r.value.fuel_level)?.value.fuel_level || 0

    return {
      ...vehicle,
      speed: latestSpeed,
      tyre_pressure: latestTyrePressure,
      fuel_level: latestFuelLevel
    }
  })

  const apiKey = 'AIzaSyBoailEnSezAE-hZK4pruLvZTOLA91YIlQ'
  const mapContainerStyle = { width: '100%', height: '750px' }

  // Filter readings and alerts based on selected vehicle
  const filteredReadings = selectedVehicleId
    ? latestReadings.filter(
        (vehicle) => vehicle.vehicle_id === selectedVehicleId
      )
    : latestReadings

  const filteredAlerts = selectedVehicleId
    ? alertData.filter((alert) => alert.vehicle_id === selectedVehicleId)
    : alertData

  // Status color mapping
  const statusColor = {
    active: 'green',
    critical: 'red',
    broken: 'yellow'
  }

  const getMarkerIcon = (status) => {
    const color = statusColor[status.toLowerCase()] || 'blue'
    return `http://maps.google.com/mapfiles/ms/icons/${color}-dot.png`
  }

  // Styling
  const tableHeaderStyle = {
    padding: '12px',
    backgroundColor: '#e0e0e0',
    borderBottom: '2px solid #ddd',
    textAlign: 'left',
    fontWeight: 'bold',
    fontSize: '16px'
  }

  const tableCellStyle = {
    padding: '12px',
    borderBottom: '1px solid #ddd',
    fontSize: '15px',
    color: '#333'
  }

  const cardStyle = {
    marginBottom: '20px',
    padding: '10px',
    border: '1px solid #ccc',
    borderRadius: '8px',
    backgroundColor: '#fff',
    boxShadow: '0px 2px 5px rgba(0,0,0,0.1)'
  }

  const scrollableStyle = {
    maxHeight: '240px',
    overflowY: 'auto'
  }

  return (
    <div style={{ display: 'flex', gap: '20px', padding: '20px' }}>
      {/* Map Section */}
      <div style={{ flex: 2 }}>
        <LoadScript googleMapsApiKey={apiKey}>
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={defaultCenter}
            zoom={15}
            onClick={() => setSelectedVehicleId(null)}
          >
            {Object.entries(vehicleLocations).map(([vehicleId, location]) => {
              const vehicle = latestReadings.find(
                (v) => v.vehicle_id === parseInt(vehicleId)
              )
              return (
                <Marker
                  key={vehicleId}
                  position={location}
                  icon={getMarkerIcon(vehicle.status)}
                  label={`${vehicle?.make} ${vehicle?.model}`}
                  onClick={() => setSelectedVehicleId(parseInt(vehicleId))} // Set selected vehicle
                />
              )
            })}
          </GoogleMap>
        </LoadScript>
      </div>

      {/* Vehicles and Alerts Card Section */}
      <div style={{ flex: 1 }}>
        {/* Vehicles Card */}
        <div style={cardStyle}>
          <h2 style={{ textAlign: 'center', marginBottom: '10px' }}>
            Vehicles
          </h2>
          <div style={scrollableStyle}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={tableHeaderStyle}>Name</th>
                  <th style={tableHeaderStyle}>Status</th>
                  <th style={tableHeaderStyle}>Speed (KM/H)</th>
                  <th style={tableHeaderStyle}>Fuel (L)</th>
                </tr>
              </thead>
              <tbody>
                {filteredReadings.map((vehicle) => (
                  <tr key={vehicle.vehicle_id}>
                    <td style={tableCellStyle}>
                      {vehicle.make} {vehicle.model}
                    </td>
                    <td style={tableCellStyle}>
                      <span
                        style={{
                          display: 'inline-block',
                          width: '12px',
                          height: '12px',
                          backgroundColor:
                            statusColor[vehicle.status.toLowerCase()],
                          borderRadius: '50%',
                          marginRight: '8px'
                        }}
                      ></span>
                      {vehicle.status}
                    </td>
                    <td style={tableCellStyle}>{vehicle.speed}</td>
                    <td style={tableCellStyle}>{vehicle.fuel_level}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Alerts Card */}
        <div style={cardStyle}>
          <h2 style={{ textAlign: 'center', marginBottom: '10px' }}>Alerts</h2>
          <div style={scrollableStyle}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={tableHeaderStyle}>Time</th>
                  <th style={tableHeaderStyle}>Type</th>
                  <th style={tableHeaderStyle}>Vehicle</th>
                  <th style={tableHeaderStyle}>Severity</th>
                  <th style={tableHeaderStyle}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.map((alert, index) => (
                  <tr key={index}>
                    <td style={tableCellStyle}>{alert.createdAt}</td>
                    <td style={tableCellStyle}>{alert.alert_type}</td>
                    <td style={tableCellStyle}>{alert.vehicle_name}</td>
                    <td style={tableCellStyle}>{alert.severity}</td>
                    <td style={tableCellStyle}>{alert.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

render(<MapComponent />)
