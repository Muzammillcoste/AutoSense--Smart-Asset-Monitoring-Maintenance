const VehicleFuelConsumption = () => {
  const [vehicleData, setVehicleData] = useState([])
  const [selectedVehicle, setSelectedVehicle] = useState(null)
  const [selectedDataType, setSelectedDataType] = useState('fuel') // Default to "fuel"
  const [fuelConsumptionData, setFuelConsumptionData] = useState(null)
  const [tyrePressureData, setTyrePressureData] = useState(null)
  const [temperatureData, setTemperatureData] = useState(null) // Added temperature data state
  const [error, setError] = useState(null)
  const [pollingInterval, setPollingInterval] = useState(null)

  useEffect(() => {
    const fetchVehicles = async () => {
      try {
        const requestData = { user: 'test' }
        const response = await axios.post(
          'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1',
          requestData
        )

        if (
          !response?.data?.isError &&
          response?.data?.actions?.[0]?.obj &&
          Array.isArray(response.data.actions[0].obj)
        ) {
          const vehicles = response.data.actions[0].obj.map((item) => ({
            vehicle_id: item.vehicle_id,
            make: item.make || 'Unknown',
            model: item.model || 'Unknown',
            year: item.year || 'Unknown',
            vin: item.vin || 'N/A',
            status: item.status || 'Unknown',
            license_plate: item.license_plate || 'N/A'
          }))

          setVehicleData(vehicles)
        } else {
          setError('Error in API response or invalid data structure')
        }
      } catch (err) {
        console.error('Error fetching vehicles:', err)
        setError('Failed to fetch vehicle data')
      }
    }

    fetchVehicles()
  }, [])

  useEffect(() => {
    if (!selectedVehicle) return

    const fetchData = async () => {
      try {
        const requestData = { user: 'test' }
        const response = await axios.post(
          'https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=tdFQHIL9F97blZ-D7eeUPblvx',
          requestData
        )

        if (response?.data?.response?.obj) {
          const data = response.data.response.obj.filter(
            (item) => item.vehicle_id === selectedVehicle
          )

          // Slice the last 100 data points
          const last100Data = data.slice(-100)

          const labels = []
          const fuelData = []
          const tyreData = []
          const tempData = [] // Array for storing temperature data
          const fuelColors = [] // To store point colors for fuel
          const tyreColors = [] // To store point colors for tyre pressure
          const tempColors = [] // To store point colors for temperature

          // Process the data, pairing fuel, tyre pressure, and temperature readings by timestamp
          last100Data.forEach((item) => {
            const createdAt = new Date(item.createdAt)
            if (!isNaN(createdAt)) {
              const timestamp = formatTime(createdAt)
              if (!labels.includes(timestamp)) labels.push(timestamp)

              // Fuel data
              const fuelLevel = item.value.fuel_level
              if (fuelLevel) {
                fuelData.push(fuelLevel)
                // Set color to red if fuel is below 20
                fuelColors.push(fuelLevel < 20 ? 'red' : '#4BC0C0')
              } else {
                fuelData.push(null) // Ensure we maintain the same length if fuel data is missing
                fuelColors.push(null)
              }

              // Tyre pressure data
              const tyrePressure = item.value.tyre_pressure
              if (tyrePressure) {
                tyreData.push(tyrePressure)
                // Set color to red if tyre pressure is below 100
                tyreColors.push(tyrePressure < 100 ? 'red' : '#F39C12')
              } else {
                tyreData.push(null) // Ensure we maintain the same length if tyre data is missing
                tyreColors.push(null)
              }

              // Temperature data
              const temperature = item.value.temperature
              if (temperature) {
                tempData.push(temperature)
                // Set color to red if temperature is above 40
                tempColors.push(temperature > 40 ? 'red' : '#E74C3C')
              } else {
                tempData.push(null) // Ensure we maintain the same length if temperature data is missing
                tempColors.push(null)
              }
            }
          })

          setFuelConsumptionData({
            labels: labels,
            datasets: [
              {
                label: 'Fuel Level (L)',
                data: fuelData,
                fill: false,
                borderColor: '#4BC0C0', // Fuel color
                tension: 0.4,
                borderWidth: 2,
                spanGaps: true,
                pointBackgroundColor: fuelColors // Apply color logic to points
              }
            ]
          })

          setTyrePressureData({
            labels: labels,
            datasets: [
              {
                label: 'Tyre Pressure (PSI)',
                data: tyreData,
                fill: false,
                borderColor: '#F39C12', // Tyre pressure color
                tension: 0.4,
                borderWidth: 2,
                spanGaps: true,
                pointBackgroundColor: tyreColors // Apply color logic to points
              }
            ]
          })

          setTemperatureData({
            labels: labels,
            datasets: [
              {
                label: 'Temperature (°C)',
                data: tempData,
                fill: false,
                borderColor: '#E74C3C', // Temperature color
                tension: 0.4,
                borderWidth: 2,
                spanGaps: true,
                pointBackgroundColor: tempColors // Apply color logic to points
              }
            ]
          })
        } else {
          setError('No data available for the selected vehicle')
        }
      } catch (err) {
        console.error('Error fetching data:', err)
        setError('Failed to fetch data')
      }
    }

    const interval = setInterval(() => {
      fetchData()
    }, 100)

    setPollingInterval(interval)

    return () => clearInterval(interval)
  }, [selectedVehicle])

  const formatTime = (date) => {
    const hours = date.getHours()
    const minutes = date.getMinutes()
    const seconds = date.getSeconds()
    const ampm = hours >= 12 ? 'PM' : 'AM'
    const formattedHours = hours % 12 || 12
    const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes
    const formattedSeconds = seconds < 10 ? `0${seconds}` : seconds

    return `${formattedHours}:${formattedMinutes}:${formattedSeconds} ${ampm}`
  }

  const handleVehicleSelect = (vehicleId) => {
    setSelectedVehicle(vehicleId)
    setFuelConsumptionData(null)
    setTyrePressureData(null)
    setTemperatureData(null) // Reset temperature data

    if (pollingInterval) {
      clearInterval(pollingInterval)
    }
  }

  const handleDataTypeChange = (event) => {
    setSelectedDataType(event.target.value)
  }

  if (error) {
    return (
      <div
        style={{
          color: '#e74c3c',
          fontSize: '18px',
          padding: '20px',
          textAlign: 'center'
        }}
      >
        Error: {error}
      </div>
    )
  }

  if (!vehicleData.length) {
    return (
      <div style={{ fontSize: '18px', textAlign: 'center', padding: '20px' }}>
        Loading vehicles...
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        padding: '20px',
        gap: '20px'
      }}
    >
      <div
        style={{
          flex: 1,
          padding: '10px',
          borderRadius: '8px',
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
          backgroundColor: '#fff'
        }}
      >
        <h2
          style={{
            color: '#34495e',
            fontSize: '24px',
            marginBottom: '20px',
            textAlign: 'center'
          }}
        >
          Vehicles
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {vehicleData.map((vehicle) => (
            <div
              key={vehicle.vehicle_id}
              onClick={() => handleVehicleSelect(vehicle.vehicle_id)}
              style={{
                background:
                  selectedVehicle === vehicle.vehicle_id
                    ? '#3498db'
                    : '#bdc3c7', // Darker shade for unselected
                color:
                  selectedVehicle === vehicle.vehicle_id ? '#fff' : '#2c3e50',
                padding: '15px',
                margin: '5px 0',
                cursor: 'pointer',
                borderRadius: '10px',
                boxShadow: '0 5px 15px rgba(0, 0, 0, 0.1)',
                transition: 'transform 0.2s, background 0.3s, color 0.3s',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
              onMouseEnter={(e) => (e.target.style.transform = 'scale(1.05)')}
              onMouseLeave={(e) => (e.target.style.transform = 'scale(1)')}
            >
              <div>
                <h4
                  style={{ margin: 0 }}
                >{`${vehicle.make} ${vehicle.model}`}</h4>
                <p style={{ margin: 0, fontSize: '14px' }}>
                  {vehicle.license_plate}
                </p>
              </div>
              <i
                className='fas fa-car'
                style={{
                  fontSize: '18px',
                  color:
                    selectedVehicle === vehicle.vehicle_id ? '#fff' : '#7f8c8d'
                }}
              ></i>
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          flex: 2,
          padding: '10px',
          borderRadius: '8px',
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
          backgroundColor: '#fff'
        }}
      >
        <div style={{ marginBottom: '20px' }}>
          <label style={{ fontSize: '18px', color: '#34495e' }}>
            Select Data Type:
          </label>
          <select
            value={selectedDataType}
            onChange={handleDataTypeChange}
            style={{
              padding: '10px',
              borderRadius: '5px',
              marginLeft: '10px',
              border: '1px solid #bdc3c7',
              fontSize: '16px'
            }}
          >
            <option value='fuel'>Fuel Consumption</option>
            <option value='tyre'>Tyre Pressure</option>
            <option value='temperature'>Temperature</option>{' '}
            {/* Added temperature option */}
          </select>
        </div>

        {selectedVehicle &&
        (selectedDataType === 'fuel'
          ? fuelConsumptionData
          : selectedDataType === 'tyre'
          ? tyrePressureData
          : temperatureData) ? (
          <>
            {/* Displaying make and model of selected vehicle */}
            <h2
              style={{
                color: '#34495e',
                fontSize: '24px',
                marginBottom: '20px'
              }}
            >
              {selectedDataType === 'fuel'
                ? 'Fuel Consumption'
                : selectedDataType === 'tyre'
                ? 'Tyre Pressure'
                : 'Temperature'}{' '}
              -{' '}
              {
                vehicleData.find(
                  (vehicle) => vehicle.vehicle_id === selectedVehicle
                )?.make
              }{' '}
              {
                vehicleData.find(
                  (vehicle) => vehicle.vehicle_id === selectedVehicle
                )?.model
              }
            </h2>
            <Line
              data={
                selectedDataType === 'fuel'
                  ? fuelConsumptionData
                  : selectedDataType === 'tyre'
                  ? tyrePressureData
                  : temperatureData
              }
            />
          </>
        ) : (
          <p style={{ fontSize: '18px', color: '#7f8c8d' }}>
            Select a vehicle and data type to view the graph.
          </p>
        )}
      </div>
    </div>
  )
}

render(
  <React.StrictMode>
    <VehicleFuelConsumption />
  </React.StrictMode>,
  document.getElementById('root')
)
