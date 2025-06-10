// StatusandAlertsCharts.js

const VehicleAndAlertDisplay = () => {
  const [vehicleData, setVehicleData] = useState([])
  const [alertData, setAlertData] = useState([])
  const [error, setError] = useState(null)
  const [selectedStatus, setSelectedStatus] = useState(null)
  const [showTab, setShowTab] = useState(false)
  const [chartType, setChartType] = useState('alert_type')

  const alertsWebhook =
    'https://swift-cloud.ephlux.com/api-swift/ned/workflow/xuRob0A4mf?SWIFT_API_KEY=S1/JT2c/77dtlkCR+qQtZW5s+QX'
  const vehicleWebhook =
    'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1'

  const fetchVehicleData = async () => {
    try {
      const vehicleResponse = await axios.post(vehicleWebhook, {})
      const vehicles = vehicleResponse?.data?.actions?.[0]?.obj || []
      setVehicleData(vehicles)
      setError(null)
    } catch (err) {
      console.error('Error fetching vehicle data:', err)
      setError('Failed to fetch vehicle data')
    }
  }

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

  useEffect(() => {
    fetchVehicleData()
  }, [])

  useEffect(() => {
    if (vehicleData.length > 0) {
      fetchAlertData()
    }
  }, [vehicleData])

  const getStatusCounts = () => {
    const statusCounts = {}
    vehicleData.forEach((vehicle) => {
      const status = vehicle.status || 'Unknown'
      statusCounts[status] = (statusCounts[status] || 0) + 1
    })
    return statusCounts
  }

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
              return (
                {
                  high: '#FF4C4C',
                  medium: '#FF9F00',
                  low: '#4CAF50'
                }[key] || '#9E9E9E'
              )
            } else {
              return (
                {
                  'fuel level': '#00A3FF',
                  temperature: '#FBBF24',
                  'tyre pressure (front left)': '#3180F3',
                  'tyre pressure (front right)': '#5A67D8',
                  'tyre pressure (rear left)': '#ED64A6',
                  'tyre pressure (rear right)': '#A78BFA'
                }[key] || '#00A3FF'
              )
            }
          })
        }
      ]
    }
  }

  const handleChartClick = (status) => {
    setSelectedStatus(status)
    setShowTab(true)
  }

  const handleChartTypeChange = (type, e) => {
    e.preventDefault()
    setChartType(type)
  }

  const closeTab = () => {
    setShowTab(false)
  }

  const getButtonStyle = (isActive) => ({
    padding: '10px 16px',
    margin: '0 6px',
    backgroundColor: isActive ? '#2563EB' : '#E5E7EB',
    color: isActive ? '#FFFFFF' : '#374151',
    border: 'none',
    borderRadius: '12px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: '0.3s ease'
  })

  const statusCounts = getStatusCounts()
  const doughnutData = {
    labels: Object.keys(statusCounts),
    datasets: [
      {
        data: Object.values(statusCounts),
        backgroundColor: Object.keys(statusCounts).map(
          (status) =>
            ({
              active: '#22C55E',
              critical: '#EF4444',
              warning: '#F59E0B'
            }[status.toLowerCase()] || '#9CA3AF')
        )
      }
    ]
  }

  const doughnutOptions = {
    maintainAspectRatio: false,
    responsive: true,
    onClick: (e, elements) => {
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
        padding: '30px',
        fontFamily: 'Segoe UI, sans-serif',
        backgroundColor: '#F9FAFB'
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
          gap: '30px',
          marginBottom: '30px'
        }}
      >
        <div
          style={{
            backgroundColor: '#FFFFFF',
            padding: '24px',
            borderRadius: '16px',
            boxShadow: '0 10px 15px rgba(0,0,0,0.05)'
          }}
        >
          {error ? (
            <div style={{ textAlign: 'center' }}>
              <p style={{ color: '#DC2626' }}>{error}</p>
              <button onClick={fetchVehicleData} style={getButtonStyle(true)}>
                Retry
              </button>
            </div>
          ) : (
            <>
              <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>
                Vehicle Status
              </h2>
              <div style={{ height: '400px' }}>
                <Doughnut data={doughnutData} options={doughnutOptions} />
              </div>
            </>
          )}
        </div>

        <div
          style={{
            backgroundColor: '#FFFFFF',
            padding: '24px',
            borderRadius: '16px',
            boxShadow: '0 10px 15px rgba(0,0,0,0.05)'
          }}
        >
          <h2 style={{ textAlign: 'center', marginBottom: '16px' }}>Alerts</h2>
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              marginBottom: '20px'
            }}
          >
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
          <div style={{ height: '400px' }}>
            <Bar data={getChartData()} />
          </div>
        </div>
      </div>

      {showTab && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            padding: '20px',
            borderRadius: '16px',
            boxShadow: '0 10px 15px rgba(0,0,0,0.05)',
            maxWidth: '1000px',
            margin: 'auto'
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <h3 style={{ color: '#111827' }}>
              Selected Status: {selectedStatus}
            </h3>
            <button
              onClick={closeTab}
              style={{
                backgroundColor: '#DC2626',
                color: '#FFFFFF',
                padding: '10px 14px',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

render(<VehicleAndAlertDisplay />, document.getElementById('root'))
