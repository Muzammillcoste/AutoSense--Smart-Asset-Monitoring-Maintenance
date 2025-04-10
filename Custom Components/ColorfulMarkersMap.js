const MapComponent = () => {
  const [vehicleData, setVehicleData] = useState([])
  const [sensorReadings, setSensorReadings] = useState([])
  const [latestReadings, setLatestReadings] = useState([]) // Combined data
  const [selectedVehicleId, setSelectedVehicleId] = useState(null)

  const vehicleWebhook =
    'https://swift-staging.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1'
  const sensorWebhook =
    'https://swift-staging.ephlux.com/api-swift/ned/workflow/zXSGrWOgyg?SWIFT_API_KEY=pB-qorkYtZLfZ9ODofzUnv3OcPA'

  // Fetch Vehicle Data
  const fetchVehicleData = async () => {
    try {
      const response = await axios.post(vehicleWebhook, {})
      const vehicles = response.data.actions[0].obj || []
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
      setSensorReadings(sensors)
    } catch (error) {
      console.error('Error fetching sensor data:', error)
    }
  }

  const updateLatestReadings = () => {
    const combinedReadings = vehicleData.map((vehicle) => {
      const readings = sensorReadings
        .filter((reading) => reading.vehicle_id === vehicle.vehicle_id)
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)) // Sort by latest timestamp

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
    setLatestReadings(combinedReadings) // Update the table data
  }

  // Combine vehicle data with latest sensor readings
  useEffect(() => {
    updateLatestReadings()
  }, [vehicleData, sensorReadings]) // Re-run whenever new data is fetched

  // Fetch data every second
  useEffect(() => {
    fetchVehicleData()
    fetchSensorData()
    const interval = setInterval(() => {
      fetchVehicleData()
      fetchSensorData()
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const apiKey = 'AIzaSyBoailEnSezAE-hZK4pruLvZTOLA91YIlQ'
  const mapContainerStyle = { width: '100%', height: '500px' }
  const defaultCenter = { lat: 24.8607, lng: 67.0011 }

  // Status color mapping for marker icons
  const statusColor = {
    active: 'green',
    critical: 'red',
    broken: 'yellow'
  }

  //   const getMarkerIcon = (status) => {
  //     const color = statusColor[status.toLowerCase()] || 'blue'
  //     return `http://maps.google.com/mapfiles/ms/icons/${color}-dot.png`
  //   }

  return (
    <div style={{ display: 'flex', gap: '20px', padding: '20px' }}>
      {/* Map Section */}
      <div style={{ flex: 2 }}>
        <LoadScript googleMapsApiKey={apiKey}>
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={defaultCenter}
            zoom={14}
          >
            {latestReadings.map((vehicle) => {
              const color = statusColor[vehicle.status.toLowerCase()] || 'blue'
              const location = sensorReadings
                .filter((reading) => reading.vehicle_id === vehicle.vehicle_id)
                .find((r) => r.value.latitude && r.value.longitude)

              return location ? (
                <Marker
                  key={vehicle.vehicle_id}
                  position={{
                    lat: location.value.latitude,
                    lng: location.value.longitude
                  }}
                  icon={`http://maps.google.com/mapfiles/ms/icons/${color}-dot.png`} // Dynamic marker icon
                  label={{
                    text: `${vehicle.make} ${vehicle.model}`,
                    color: '#000',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}
                  onClick={() => setSelectedVehicleId(vehicle.vehicle_id)}
                />
              ) : null
            })}
          </GoogleMap>
        </LoadScript>
      </div>

      {/* Table Section */}
      <div
        style={{
          flex: 1,
          padding: '20px',
          border: '1px solid #ccc',
          borderRadius: '8px',
          backgroundColor: '#f9f9f9',
          boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)',
          fontFamily: 'Roboto, sans-serif',
          maxHeight: '500px',
          overflowY: 'auto'
        }}
      >
        <h2 style={{ marginBottom: '15px', textAlign: 'center' }}>Vehicles</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={tableHeaderStyle}>Name</th>
              <th style={tableHeaderStyle}>Status</th>
              <th style={tableHeaderStyle}>Speed (km/h)</th>
              <th style={tableHeaderStyle}>Tyre Pressure (PSI)</th>
              <th style={tableHeaderStyle}>Fuel Level (L)</th>
            </tr>
          </thead>
          <tbody>
            {latestReadings.map((vehicle) => (
              <tr key={vehicle.vehicle_id} style={{ backgroundColor: '#fff' }}>
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
                <td style={tableCellStyle}>{vehicle.tyre_pressure}</td>
                <td style={tableCellStyle}>{vehicle.fuel_level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

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

render(MapComponent)
