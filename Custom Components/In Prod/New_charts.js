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
      // Update vehicleData state
      setVehicleData(vehicles)
    } catch (err) {
      console.error('Error fetching vehicle data:', err)
      setError('Failed to fetch vehicle data')
    }
  }

  /**
   * Fetch alert data from the API and enrich it with the vehicle information.
   */
  const fetchAlertData = async () => {
    try {
      const alertResponse = await axios.post(alertsWebhook, {})
      const alerts = alertResponse?.data?.actions?.[0]?.obj || []
      // Map over alerts and add the corresponding vehicle name
      const enrichedAlerts = alerts.map((alert) => {
        const vehicle = vehicleData.find(
          (v) => v.vehicle_id === alert.vehicle_id
        )
        const vehicleName = vehicle
          ? `${vehicle.make} ${vehicle.model}`
          : 'Unknown Vehicle'
        return { ...alert, vehicle_name: vehicleName }
      })
      // Update alertData state
      setAlertData(enrichedAlerts)
    } catch (err) {
      console.error('Error fetching alerts data:', err)
      // Optionally, set an error message for alerts here
    }
  }

  /**
   * useEffect to fetch vehicle data when the component mounts.
   */
  useEffect(() => {
    fetchVehicleData()
    // Empty dependency array ensures this runs only once on mount.
  }, [])

  /**
   * useEffect to fetch alert data whenever vehicleData is updated.
   * (We use vehicleData as a dependency because alertData is enriched with vehicleData.
   * Adding alertData as a dependency would trigger an endless loop.)
   */
  useEffect(() => {
    if (vehicleData.length > 0) {
      fetchAlertData()
    }
    4
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
      // Convert key to lowercase for consistency
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
          // Define background colors based on the chartType and key values
          backgroundColor: Object.keys(counts).map((key) => {
            if (chartType === 'severity') {
              switch (key) {
                case 'critical':
                  return '#FF4C4C'
                case 'high':
                  return '#FF9F00'
                case 'normal':
                  return '#4CAF50'
                default:
                  return '#9E9E9E'
              }
            } else {
              switch (key) {
                case 'fuel level':
                  return '#FF9800'
                case 'temperature':
                  return '#2196F3'
                case 'tyre pressure':
                  return '#3180F3'
                default:
                  return '#9E9E9E'
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
    event.preventDefault() // Prevent default behavior (e.g., page refresh)
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
    backgroundColor: isActive ? '#007BFF' : '#ccc',
    color: '#fff',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px'
  })

  // Prepare doughnut chart data using the vehicle status counts
  const statusCounts = getStatusCounts()
  const colorMapping = {
    active: '#2EB432',
    critical: 'red',
    warning: '#E68A00',
    unknown: '#9E9E9E' // Default color for undefined statuses
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

  // Doughnut chart options including a click handler to show detailed view
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
        fontFamily: 'Arial, sans-serif',
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
            backgroundColor: '#D5FFFF', // Light blue background
            borderRadius: '15px',
            padding: '20px',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)'
          }}
        >
          {error ? (
            <p style={{ color: 'red', textAlign: 'center' }}>Error: {error}</p>
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
            backgroundColor: '#D5FFFF', // Light blue background
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
      {/* Additional UI elements (such as a detailed tab) can be added here if needed */}
    </div>
  )
}

render(<VehicleAndAlertDisplay />)
