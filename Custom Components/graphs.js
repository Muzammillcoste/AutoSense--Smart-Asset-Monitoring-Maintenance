class VehicleAndAlertDisplay extends React.Component {
  constructor() {
    super()
    this.state = {
      vehicleData: [],
      alertData: [],
      error: null,
      selectedStatus: null,
      showTab: false,
      chartType: 'alert_type' // Toggle between alert_type and severity
    }

    this.alertsWebhook =
      'https://swift-cloud.ephlux.com/api-swift/ned/workflow/xuRob0A4mf?SWIFT_API_KEY=S1/JT2c/77dtlkCR+qQtZW5s+QX'
    this.vehicleWebhook =
      'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1'
  }

  async componentDidMount() {
    try {
      const vehicleResponse = await axios.post(this.vehicleWebhook, {})
      const vehicles = vehicleResponse?.data?.actions?.[0]?.obj || []
      this.setState({ vehicleData: vehicles }, this.fetchAlertData)
    } catch (error) {
      console.error('Error fetching vehicle data:', error)
      this.setState({ error: 'Failed to fetch vehicle data' })
    }
  }

  fetchAlertData = async () => {
    try {
      const { vehicleData } = this.state
      const alertResponse = await axios.post(this.alertsWebhook, {})
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
      this.setState({ alertData: enrichedAlerts })
    } catch (error) {
      console.error('Error fetching alerts data:', error)
    }
  }

  getStatusCounts() {
    const { vehicleData } = this.state
    const statusCounts = {}

    vehicleData.forEach((vehicle) => {
      const status = vehicle.status || 'Unknown'
      statusCounts[status] = (statusCounts[status] || 0) + 1
    })

    return statusCounts
  }

  getChartData() {
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

  handleChartClick = (status) => {
    this.setState({ selectedStatus: status, showTab: true })
  }

  handleChartTypeChange = (type, event) => {
    event.preventDefault() // Prevent page refresh
    this.setState({ chartType: type })
  }

  closeTab = () => {
    this.setState({ showTab: false })
  }

  getButtonStyle(isActive) {
    return {
      padding: '10px 20px',
      margin: '0 10px',
      backgroundColor: isActive ? '#007BFF' : '#ccc',
      color: '#fff',
      border: 'none',
      borderRadius: '5px',
      cursor: 'pointer',
      fontSize: '14px'
    }
  }

  render() {
    const {
      vehicleData,
      alertData,
      error,
      selectedStatus,
      showTab,
      chartType
    } = this.state

    const statusCounts = this.getStatusCounts()

    // Color mapping for donut chart
    const colorMapping = {
      active: 'green',
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
            (status) =>
              colorMapping[status.toLowerCase()] || colorMapping.unknown
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
          this.handleChartClick(status)
        }
      }
    }

    return (
      <div
        style={{
          backgroundColor: '#D5FFFF', // Light blue background
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
          {/* Doughnut Chart */}
          <div style={{ width: '45%' }}>
            {error ? (
              <p style={{ color: 'red', textAlign: 'center' }}>
                Error: {error}
              </p>
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

          {/* Bar Chart */}
          <div style={{ width: '45%' }}>
            <h2 style={{ textAlign: 'center', color: '#333' }}>Alerts</h2>
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <button
                onClick={(e) => this.handleChartTypeChange('alert_type', e)}
                style={this.getButtonStyle(chartType === 'alert_type')}
              >
                Group by Alert Type
              </button>
              <button
                onClick={(e) => this.handleChartTypeChange('severity', e)}
                style={this.getButtonStyle(chartType === 'severity')}
              >
                Group by Severity
              </button>
            </div>
            <div style={{ width: '100%', height: '400px', margin: 'auto' }}>
              <Bar data={this.getChartData()} />
            </div>
          </div>
        </div>
      </div>
    )
  }
}
