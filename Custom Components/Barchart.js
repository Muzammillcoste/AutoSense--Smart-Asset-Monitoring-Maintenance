class AlertsChart extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      alertData: [],
      vehicleData: [],
      chartType: 'alert_type' // Toggle between alert_type and severity
    }

    this.alertsWebhook =
      'https://swift-cloud.ephlux.com/api-swift/ned/workflow/xuRob0A4mf?SWIFT_API_KEY=S1/JT2c/77dtlkCR+qQtZW5s+QX'
    this.vehicleWebhook =
      'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1'
  }

  componentDidMount() {
    this.fetchVehicleData()
  }

  componentDidUpdate(prevProps, prevState) {
    if (prevState.vehicleData !== this.state.vehicleData) {
      this.fetchAlertData()
    }
  }

  // Fetch vehicle data
  fetchVehicleData = async () => {
    try {
      const response = await axios.post(this.vehicleWebhook, {})
      const vehicles = response.data.actions[0]?.obj || []
      this.setState({ vehicleData: vehicles })
    } catch (error) {
      console.error('Error fetching vehicle data:', error)
    }
  }

  // Fetch alerts data
  fetchAlertData = async () => {
    try {
      const { vehicleData } = this.state
      const response = await axios.post(this.alertsWebhook, {})
      const alerts = response.data.actions[0]?.obj || []
      const enrichedAlerts = alerts.map((alert) => {
        const vehicle = vehicleData.find(
          (v) => v.vehicle_id === alert.vehicle_id
        )
        const vehicleName = vehicle
          ? `${vehicle.make} ${vehicle.model}`
          : 'Unknown Vehicle'
        return { ...alert, vehicle_name: vehicleName }
      })
      this.setState({ alertData: enrichedAlerts })
    } catch (error) {
      console.error('Error fetching alerts data:', error)
    }
  }

  // Process alerts data for chart
  getChartData = () => {
    const { alertData, chartType } = this.state
    const counts = alertData.reduce((acc, alert) => {
      const key = alert[chartType]?.toLowerCase() // Ensure values are lowercase
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
              // For severity types
              switch (key) {
                case 'critical':
                  return '#FF4C4C' // Bright red for critical
                case 'high':
                  return '#FF9F00' // Orange for high
                case 'normal':
                  return '#4CAF50' // Green for normal
                default:
                  return '#9E9E9E' // Neutral gray for unexpected severity
              }
            } else if (chartType === 'alert_type') {
              // For alert types (like Fuel Level, Temperature, etc.)
              switch (key) {
                case 'fuel level':
                  return '#FF9800' // Orange for Fuel Level
                case 'temperature':
                  return '#2196F3' // Blue for Temperature
                case 'tyre pressure':
                  return '#3180F3' // Blue for Temperature
                default:
                  return '#9E9E9E' // Neutral gray for other types
              }
            }
            return '#9E9E9E' // Fallback gray for unexpected types
          })
        }
      ]
    }
  }

  handleChartTypeChange = (type) => {
    this.setState({ chartType: type })
  }

  render() {
    const { alertData, chartType } = this.state

    return (
      <div style={{ fontFamily: 'Arial, sans-serif', margin: '20px' }}>
        <h1 style={{ textAlign: 'center', color: '#333' }}>Alerts</h1>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <button
            type='button'
            onClick={() => this.handleChartTypeChange('alert_type')}
            style={{
              padding: '10px 20px',
              marginRight: '10px',
              backgroundColor: chartType === 'alert_type' ? '#007BFF' : '#ccc',
              color: '#fff',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Group by Alert Type
          </button>
          <button
            type='button'
            onClick={() => this.handleChartTypeChange('severity')}
            style={{
              padding: '10px 20px',
              backgroundColor: chartType === 'severity' ? '#007BFF' : '#ccc',
              color: '#fff',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Group by Severity
          </button>
        </div>

        {alertData.length > 0 ? (
          <div
            style={{
              width: '80%',
              height: '500px',
              margin: 'auto',
              background: '#D5FFFF',
              padding: '20px',
              borderRadius: '10px',
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)'
            }}
          >
            <Bar data={this.getChartData()} />
          </div>
        ) : (
          <p
            style={{
              textAlign: 'center',
              color: '#666',
              fontSize: '18px',
              marginTop: '20px'
            }}
          >
            No alerts data available for the chart.
          </p>
        )}
      </div>
    )
  }
}
