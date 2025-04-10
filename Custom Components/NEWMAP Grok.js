// Map.js
const MapComponent = () => {
  const [vehicleData, setVehicleData] = useState([])
  const [sensorReadings, setSensorReadings] = useState([])
  const [alertData, setAlertData] = useState([])
  const [selectedVehicleId, setSelectedVehicleId] = useState(null)

  const vehicleWebhook =
    'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1'
  const sensorWebhook =
    'https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=tdFQHIL9F97blZ-D7eeUPblvx'
  const alertsWebhook =
    'https://swift-cloud.ephlux.com/api-swift/ned/workflow/xuRob0A4mf?SWIFT_API_KEY=S1/JT2c/77dtlkCR+qQtZW5s+QX'

  const markerIcons = {
    active:
      'https://swift-cloud.ephlux.com/uploads/c94afedf-5baf-45da-9feb-ac776fc94eae-green.png',
    warning:
      'https://swift-cloud.ephlux.com/uploads/2ec842d5-ff5a-4105-85e1-1b36ead0c636-yellow.png',
    critical:
      'https://swift-cloud.ephlux.com/uploads/15f3188c-cacd-4c09-822a-13377829cc1f-red.png'
  }

  // ---------------- FETCH METHODS ----------------
  const fetchVehicleData = async () => {
    try {
      const response = await axios.post(vehicleWebhook, {})
      const vehicles = response.data.actions[0].obj || []
      setVehicleData(vehicles)
    } catch (error) {
      console.error('Error fetching vehicle data:', error)
    }
  }

  const fetchSensorData = async () => {
    try {
      const response = await axios.post(sensorWebhook, {})
      const sensors = response.data.response.obj || []
      setSensorReadings(sensors)
    } catch (error) {
      console.error('Error fetching sensor data:', error)
    }
  }

  const fetchAlertData = async () => {
    try {
      const response = await axios.post(alertsWebhook, {})
      const alerts = response.data.actions[0].obj || []
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

  useEffect(() => {
    fetchVehicleData()
    fetchSensorData()
    fetchAlertData()
  }, [sensorReadings])

  // ---------------- LOCATION & CENTER ----------------
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
    if (coordinates.length === 0) return { lat: 29.7321, lng: -95.342 }
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

  // ---------------- LATEST READINGS ----------------
  const latestReadings = vehicleData.map((vehicle) => {
    const readings = sensorReadings
      .filter((reading) => reading.vehicle_id === vehicle.vehicle_id)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

    const latestSpeed =
      readings.find((r) => r.value.speed !== undefined)?.value.speed || 0

    const latestFrontLeftTyrePressure =
      readings.find(
        (r) =>
          r.value.tyre_pressure &&
          r.value.tyre_pressure.front_left !== undefined
      )?.value.tyre_pressure.front_left || 0

    const latestFrontRightTyrePressure =
      readings.find(
        (r) =>
          r.value.tyre_pressure &&
          r.value.tyre_pressure.front_right !== undefined
      )?.value.tyre_pressure.front_right || 0

    const latestRearLeftTyrePressure =
      readings.find(
        (r) =>
          r.value.tyre_pressure && r.value.tyre_pressure.rear_left !== undefined
      )?.value.tyre_pressure.rear_left || 0

    const latestRearRightTyrePressure =
      readings.find(
        (r) =>
          r.value.tyre_pressure &&
          r.value.tyre_pressure.rear_right !== undefined
      )?.value.tyre_pressure.rear_right || 0

    return {
      ...vehicle,
      speed: latestSpeed,
      front_left: latestFrontLeftTyrePressure,
      front_right: latestFrontRightTyrePressure,
      rear_left: latestRearLeftTyrePressure,
      rear_right: latestRearRightTyrePressure
    }
  })

  // ---------------- FILTERS ----------------
  const filteredReadings = selectedVehicleId
    ? latestReadings.filter(
        (vehicle) => vehicle.vehicle_id === selectedVehicleId
      )
    : latestReadings

  const filteredAlerts = selectedVehicleId
    ? alertData.filter((alert) => alert.vehicle_id === selectedVehicleId)
    : alertData

  // ---------------- STYLING ----------------
  const pageContainerStyle = {
    minHeight: '100vh',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
    background: 'linear-gradient(to right, #f9fafc, #eef1f5)'
  }

  const mapContainerStyle = {
    width: '100%',
    height: '750px',
    borderRadius: '10px',
    overflow: 'hidden',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
  }

  const cardStyle = {
    marginBottom: '20px',
    padding: '15px',
    borderRadius: '10px',
    backgroundColor: '#fff',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    width: '100%',
    maxWidth: '600px'
  }

  const cardHover = (e) => {
    e.currentTarget.style.transform = 'scale(1.02)'
    e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)'
  }
  const cardLeave = (e) => {
    e.currentTarget.style.transform = 'scale(1)'
    e.currentTarget.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)'
  }

  // The container now always allows scrolling but the scrollbars are hidden by default.
  // They become visible on hover using CSS.
  const scrollableContainerStyle = {
    maxHeight: '240px',
    border: '1px solid #e0e0e0',
    borderRadius: '6px',
    marginTop: '10px'
  }

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: '#fff',
    whiteSpace: 'nowrap'
  }

  const tableHeaderStyle = {
    padding: '12px',
    backgroundColor: '#e0e0e0',
    borderBottom: '2px solid #ddd',
    textAlign: 'center',
    fontWeight: '600',
    fontSize: '14px',
    color: '#333',
    whiteSpace: 'nowrap'
  }

  const tableCellStyle = {
    padding: '12px',
    borderBottom: '1px solid #eee',
    fontSize: '14px',
    color: '#555'
  }

  const tableRowStyle = {
    cursor: 'pointer',
    transition: 'background-color 0.3s ease'
  }

  const rowHover = (e) => {
    e.currentTarget.style.backgroundColor = '#f9f9fc'
  }
  const rowLeave = (e) => {
    e.currentTarget.style.backgroundColor = ''
  }

  const statusColor = {
    active: 'green',
    critical: 'red',
    warning: '#E68A00'
  }

  // ---------------- RENDER ----------------
  return (
    <div style={pageContainerStyle}>
      {/* CSS for showing scrollbars on hover */}
      <style>
        {`
          .scrollable-container {
            overflow: auto;
            scrollbar-width: none; /* Firefox */
            -ms-overflow-style: none;  /* IE and Edge */
          }
          .scrollable-container::-webkit-scrollbar {
            width: 0;
            height: 0;
            transition: all 0.3s ease;
          }
          .scrollable-container:hover {
            scrollbar-width: thin;
          }
          .scrollable-container:hover::-webkit-scrollbar {
            width: 8px;
            height: 8px;
          }
        `}
      </style>
      <div style={{ display: 'flex', gap: '20px' }}>
        {/* MAP SECTION */}
        <div style={{ flex: 2 }}>
          <LoadScript googleMapsApiKey='AIzaSyBoailEnSezAE-hZK4pruLvZTOLA91YIlQ'>
            <GoogleMap
              mapContainerStyle={mapContainerStyle}
              center={defaultCenter}
              zoom={13}
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
                    icon={{
                      url: markerIcons[vehicle?.status.toLowerCase()],
                      scaledSize: new window.google.maps.Size(55, 55)
                    }}
                    onClick={() => setSelectedVehicleId(parseInt(vehicleId))}
                  />
                )
              })}
            </GoogleMap>
          </LoadScript>
        </div>

        {/* VEHICLES & ALERTS */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Vehicles Card */}
          <div
            style={cardStyle}
            onMouseEnter={cardHover}
            onMouseLeave={cardLeave}
          >
            <h2
              style={{ textAlign: 'center', margin: '0 0 10px', color: '#333' }}
            >
              Vehicles
            </h2>
            <div
              className='scrollable-container'
              style={scrollableContainerStyle}
            >
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={tableHeaderStyle}>Name</th>
                    <th style={tableHeaderStyle}>Status</th>
                    <th style={tableHeaderStyle}>Speed (km/h)</th>
                    <th style={tableHeaderStyle}>Front Left Tyre (PSI)</th>
                    <th style={tableHeaderStyle}>Front Right Tyre (PSI)</th>
                    <th style={tableHeaderStyle}>Rear Left Tyre (PSI)</th>
                    <th style={tableHeaderStyle}>Rear Right Tyre (PSI)</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredReadings.map((vehicle) => (
                    <tr
                      key={vehicle.vehicle_id}
                      style={tableRowStyle}
                      onMouseEnter={rowHover}
                      onMouseLeave={rowLeave}
                      onClick={() => setSelectedVehicleId(vehicle.vehicle_id)}
                    >
                      <td style={tableCellStyle}>
                        {vehicle.make} {vehicle.model}
                      </td>
                      <td style={tableCellStyle}>
                        <span
                          style={{
                            display: 'inline-block',
                            width: '10px',
                            height: '10px',
                            backgroundColor:
                              statusColor[vehicle.status.toLowerCase()],
                            borderRadius: '50%',
                            marginRight: '6px',
                            animation:
                              vehicle.status.toLowerCase() === 'critical'
                                ? 'pulseCritical 1.5s infinite'
                                : vehicle.status.toLowerCase() === 'warning'
                                ? 'pulseWarning 1.5s infinite'
                                : 'none'
                          }}
                        />
                        {vehicle.status}
                      </td>
                      <td style={tableCellStyle}>{vehicle.speed.toFixed(2)}</td>
                      <td style={tableCellStyle}>
                        {vehicle.front_left.toFixed(2)}
                      </td>
                      <td style={tableCellStyle}>
                        {vehicle.front_right.toFixed(2)}
                      </td>
                      <td style={tableCellStyle}>
                        {vehicle.rear_left.toFixed(2)}
                      </td>
                      <td style={tableCellStyle}>
                        {vehicle.rear_right.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Alerts Card */}
          <div
            style={cardStyle}
            onMouseEnter={cardHover}
            onMouseLeave={cardLeave}
          >
            <h2
              style={{ textAlign: 'center', margin: '0 0 10px', color: '#333' }}
            >
              Alerts
            </h2>
            <div
              className='scrollable-container'
              style={scrollableContainerStyle}
            >
              <table style={tableStyle}>
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
                    <tr
                      key={index}
                      style={tableRowStyle}
                      onMouseEnter={rowHover}
                      onMouseLeave={rowLeave}
                    >
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
    </div>
  )
}

render(<MapComponent />)
