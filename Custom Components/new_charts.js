const VehicleAndAlertDisplay = () => {
  // Define component state using the useState hook
  const [vehicleData, setVehicleData] = useState([])
  const [alertData, setAlertData] = useState([])
  const [error, setError] = useState(null)
  const [selectedStatus, setSelectedStatus] = useState(null)
  const [showTab, setShowTab] = useState(false)
  const [chartType, setChartType] = useState('alert_type') // Toggle between 'alert_type' and 'severity'

  // Webhook URLs for fetching data
  const alertsWebhook =
    'https://swift-cloud.ephlux.com/api-swift/ned/workflow/xuRob0A4mf?SWIFT_API_KEY=S1/JT2c/77dtlkCR+qQtZW5s+QX'
  const vehicleWebhook =
    'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1'

  /**
   * Fetch vehicle data from the API.
   */
  const fetchVehicleData = async () => {
    try {
      const vehicleResponse = await axios.post(vehicleWebhook, {})
      const vehicles = vehicleResponse?.data?.actions?.[0]?.obj || []
      setVehicleData(vehicles)
      setError(null) // Clear error on successful fetch
    } catch (err) {
      console.error('Error fetching vehicle data:', err)
      setError('Failed to fetch vehicle data')
    }
  }

  /**
   * Fetch alert data from the API and enrich it with vehicle information.
   */
  const fetchAlertData = async () => {
    try {
      const alertResponse = await axios.post(alertsWebhook, {})
      const alerts = alertResponse?.data?.actions?.[0]?.obj || []
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
    } catch (err) {
      console.error('Error fetching alerts data:', err)
    }
  }

  /**
   * useEffect to fetch vehicle data initially and periodically.
   */
  useEffect(() => {
    fetchVehicleData() // Initial fetch on mount
  }, [vehicleData]) 

  /**
   * useEffect to fetch alert data whenever vehicleData updates.
   */
  useEffect(() => {
    if (vehicleData.length > 0) {
      fetchAlertData()
    }
  }, [vehicleData])

  /**
   * Computes the counts of vehicles by status.
   */
  const getStatusCounts = () => {
    const statusCounts = {}
    vehicleData.forEach((vehicle) => {
      const status = vehicle.status || 'Unknown'
      statusCounts[status] = (statusCounts[status] || 0) + 1
    })
    return statusCounts
  }

  /**
   * Prepares the data for the Bar chart based on alertData and chartType.
   */
  const getChartData = () => {
    const counts = alertData.reduce((acc, alert) => {
      const key = alert[chartType]?.toLowerCase()
      acc[key] = (acc[key] || 0) + 1
      return acc
    }, {})

    return {
      labels: Object.keys(counts),
      datasets: [
        {
          label: `Number of Alerts by ${chartType}`,
          data: Object.values(counts),
          backgroundColor: Object.keys(counts).map((key) => {
            if (chartType === 'severity') {
              switch (key) {
                case 'high':
                  return '#FF4C4C'
                case 'medium':
                  return '#FF9F00'
                case 'low':
                  return '#4CAF50'
                default:
                  return '#9E9E9E'
              }
            } else {
              switch (key) {
                case 'fuel level':
                  return '#00A3FF'
                case 'temperature':
                  return '#FBBF24'
                case 'tyre pressure (front left)':
                  return '#3180F3'
                case 'tyre pressure (front right)':
                  return '#5A67D8'
                case 'tyre pressure (rear left)':
                  return '#ED64A6'
                case 'tyre pressure (rear right)':
                  return '#A78BFA'
                default:
                  return '#00A3FF'
              }
            }
          })
        }
      ]
    }
  }

  /**
   * Handler for clicking on a chart segment to show detailed information.
   */
  const handleChartClick = (status) => {
    setSelectedStatus(status)
    setShowTab(true)
  }

  /**
   * Handler for toggling between different chart grouping types.
   */
  const handleChartTypeChange = (type, event) => {
    event.preventDefault()
    setChartType(type)
  }

  /**
   * Handler to close any open detailed views.
   */
  const closeTab = () => {
    setShowTab(false)
  }

  /**
   * Returns styling for buttons.
   */
  const getButtonStyle = (isActive) => ({
    padding: '10px 20px',
    margin: '0 10px',
    backgroundColor: isActive ? '#00A3FF' : '#E0E0E0',
    color: isActive ? '#FFFFFF' : '#333333',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'background-color 0.3s ease, color 0.3s ease'
  })

  // Prepare doughnut chart data
  const statusCounts = getStatusCounts()
  const colorMapping = {
    active: '#2EB432',
    critical: 'red',
    warning: '#E68A00',
    unknown: '#9E9E9E'
  }

  const doughnutData = {
    labels: Object.keys(statusCounts),
    datasets: [
      {
        data: Object.values(statusCounts),
        backgroundColor: Object.keys(statusCounts).map(
          (status) => colorMapping[status.toLowerCase()] || colorMapping.unknown
        )
      }
    ]
  }

  const doughnutOptions = {
    maintainAspectRatio: false,
    responsive: true,
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const index = elements[0].index
        const status = doughnutData.labels[index]
        handleChartClick(status)
      }
    }
  }

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        fontFamily: 'Segoe UI, sans-serif',
        padding: '20px'
      }}
    >
      <div
        style={{
          margin: '20px auto',
          maxWidth: '1200px',
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'space-around'
        }}
      >
        {/* Doughnut Chart displaying vehicle status */}
        <div
          style={{
            width: '45%',
            backgroundColor: '#D5FFFF',
            borderRadius: '15px',
            padding: '20px',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)'
          }}
        >
          {error ? (
            <div style={{ textAlign: 'center' }}>
              <p style={{ color: 'red' }}>Error: {error}</p>
              <button
                onClick={fetchVehicleData}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#00A3FF',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              <h2 style={{ textAlign: 'center', color: '#333' }}>
                Vehicle Status
              </h2>
              <div style={{ width: '100%', height: '400px', margin: 'auto' }}>
                <Doughnut data={doughnutData} options={doughnutOptions} />
              </div>
            </>
          )}
        </div>

        {/* Bar Chart displaying alert information */}
        <div
          style={{
            width: '45%',
            backgroundColor: '#D5FFFF',
            borderRadius: '15px',
            padding: '20px',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)'
          }}
        >
          <h2 style={{ textAlign: 'center', color: '#333' }}>Alerts</h2>
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <button
              onClick={(e) => handleChartTypeChange('alert_type', e)}
              style={getButtonStyle(chartType === 'alert_type')}
            >
              Group by Alert Type
            </button>
            <button
              onClick={(e) => handleChartTypeChange('severity', e)}
              style={getButtonStyle(chartType === 'severity')}
            >
              Group by Severity
            </button>
          </div>
          <div style={{ width: '100%', height: '400px', margin: 'auto' }}>
            <Bar data={getChartData()} />
          </div>
        </div>
      </div>

      {showTab && (
        <div
          style={{
            margin: '20px auto',
            maxWidth: '1200px',
            backgroundColor: '#D5FFFF',
            borderRadius: '15px',
            padding: '20px',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)'
          }}
        >
          <button
            style={{
              backgroundColor: '#f56565',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 15px',
              cursor: 'pointer',
              float: 'right'
            }}
            onClick={closeTab}
          >
            Close
          </button>
          <h3 style={{ marginBottom: '10px', color: '#333' }}>
            Selected Status: {selectedStatus}
          </h3>
        </div>
      )}
    </div>
  )
}

render(<VehicleAndAlertDisplay />)
