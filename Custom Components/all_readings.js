const VehicleReadingsTable = () => {
  // State variables
  const [sensorReadings, setSensorReadings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortColumn, setSortColumn] = useState('timestamp')
  const [sortDirection, setSortDirection] = useState('desc')

  // Webhook URL
  const sensorWebhook =
    'https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=tdFQHIL9F97blZ-D7eeUPblvx'

  // Fetch data with parsing for tyre_pressure
  const fetchDataWithStates = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(sensorWebhook, {})
      const sensors = response.data.response.obj || []
      const parsedSensors = sensors.map((reading) => {
        if (typeof reading.value.tyre_pressure === 'string') {
          try {
            reading.value.tyre_pressure = JSON.parse(
              reading.value.tyre_pressure
            )
          } catch (e) {
            console.error('Error parsing tyre_pressure:', e)
            reading.value.tyre_pressure = {}
          }
        }
        return reading
      })
      setSensorReadings(parsedSensors)
    } catch (error) {
      console.error('Error fetching sensor data:', error)
      setError('Failed to fetch sensor data')
    } finally {
      setLoading(false)
    }
  }

  // Fetch data on component mount
  useEffect(() => {
    fetchDataWithStates()
  }, [])

  // Define table columns
  const columns = [
    { key: 'readingId', label: 'Reading ID' },
    { key: 'sensorId', label: 'Sensor ID' },
    { key: 'vehicleId', label: 'Vehicle ID' },
    { key: 'timestamp', label: 'Timestamp' },
    { key: 'speed', label: 'Speed' },
    { key: 'temperature', label: 'Temperature' },
    { key: 'latitude', label: 'Latitude' },
    { key: 'longitude', label: 'Longitude' },
    { key: 'frontLeft', label: 'Front Left Tyre' },
    { key: 'frontRight', label: 'Front Right Tyre' },
    { key: 'rearLeft', label: 'Rear Left Tyre' },
    { key: 'rearRight', label: 'Rear Right Tyre' }
  ]

  // Extract value for a given column from a reading
  const getColumnValue = (reading, column) => {
    switch (column) {
      case 'readingId':
        return reading.reading_id
      case 'sensorId':
        return reading.sensor_id
      case 'vehicleId':
        return reading.vehicle_id
      case 'timestamp':
        return reading.timestamp
      case 'speed':
        return reading.value.speed
      case 'temperature':
        return reading.value.temperature
      case 'latitude':
        return reading.value.latitude
      case 'longitude':
        return reading.value.longitude
      case 'frontLeft':
        return reading.value.tyre_pressure?.front_left
      case 'frontRight':
        return reading.value.tyre_pressure?.front_right
      case 'rearLeft':
        return reading.value.tyre_pressure?.rear_left
      case 'rearRight':
        return reading.value.tyre_pressure?.rear_right
      default:
        return undefined
    }
  }

  // Convert value to comparable type for sorting
  const getCompareValue = (value, column) => {
    if (value === undefined || value === null) {
      return null
    }
    switch (column) {
      case 'timestamp':
        return new Date(value)
      case 'readingId':
      case 'sensorId':
      case 'vehicleId':
        return String(value)
      case 'speed':
      case 'temperature':
      case 'latitude':
      case 'longitude':
      case 'frontLeft':
      case 'frontRight':
      case 'rearLeft':
      case 'rearRight':
        return Number(value)
      default:
        return value
    }
  }

  // Handle column header click to sort
  const handleSort = (columnKey) => {
    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(columnKey)
      setSortDirection('asc')
    }
  }

  // Sort the readings based on current sort column and direction
  const sortedReadings = [...sensorReadings].sort((a, b) => {
    const aRaw = getColumnValue(a, sortColumn)
    const bRaw = getColumnValue(b, sortColumn)
    const aValue = getCompareValue(aRaw, sortColumn)
    const bValue = getCompareValue(bRaw, sortColumn)

    if (aValue === null && bValue === null) return 0
    if (aValue === null) return sortDirection === 'asc' ? 1 : -1
    if (bValue === null) return sortDirection === 'asc' ? -1 : 1
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  // Conditional rendering for loading and error states
  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>{error}</div>
  }

  // Render the table with all readings
  return (
    <table
      style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}
    >
      <thead>
        <tr style={{ backgroundColor: '#f2f2f2' }}>
          {columns.map((column) => (
            <th
              key={column.key}
              onClick={() => handleSort(column.key)}
              style={{
                border: '1px solid #ddd',
                padding: '8px',
                textAlign: 'left',
                cursor: 'pointer'
              }}
            >
              {column.label}
              {sortColumn === column.key &&
                (sortDirection === 'asc' ? ' ↑' : ' ↓')}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sortedReadings.map((reading, index) => (
          <tr
            key={reading.reading_id || index}
            style={{ backgroundColor: index % 2 === 0 ? '#fff' : '#f9f9f9' }}
          >
            {columns.map((column) => (
              <td
                key={column.key}
                style={{ border: '1px solid #ddd', padding: '8px' }}
              >
                {getColumnValue(reading, column.key) ?? 'N/A'}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

render(<VehicleReadingsTable />)
