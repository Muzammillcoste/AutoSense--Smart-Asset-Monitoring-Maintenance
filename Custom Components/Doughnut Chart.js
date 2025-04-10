class VehicleDataDisplay extends React.Component {
  constructor() {
    super()
    this.state = {
      vehicleData: [], // Holds the fetched vehicle data
      error: null // Holds any error messages
    }
  }

  async componentDidMount() {
    try {
      const requestData = { user: 'test' }
      const response = await axios.post(
        'https://swift-staging.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1',
        requestData
      )

      console.log('API Response:', response.data)

      // Adjusting parsing logic based on the provided API structure
      if (
        response?.data?.status === 200 &&
        !response?.data?.isError &&
        response?.data?.actions?.[0]?.isError === false
      ) {
        const vehicles = response?.data?.actions?.[0]?.obj || []
        this.setState({ vehicleData: vehicles })
      } else {
        this.setState({ error: 'Error in API response' })
      }
    } catch (error) {
      console.error('Error fetching vehicles:', error)
      this.setState({ error: 'Failed to fetch vehicle data' })
    }
  }

  // Function to calculate status counts for the chart
  getStatusCounts() {
    const { vehicleData } = this.state
    const statusCounts = {}

    // Assuming each vehicle has a "status" property
    vehicleData.forEach((vehicle) => {
      const status = vehicle.status || 'Unknown' // Default to "Unknown" if status is missing
      statusCounts[status] = (statusCounts[status] || 0) + 1
    })

    return statusCounts
  }

  render() {
    const { vehicleData, error } = this.state

    // Prepare data for the doughnut chart
    const statusCounts = this.getStatusCounts()
    const chartData = {
      labels: Object.keys(statusCounts), // Status labels
      datasets: [
        {
          data: Object.values(statusCounts), // Status counts
          backgroundColor: [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF'
          ] // Custom colors
        }
      ]
    }

    // Chart options to make it smaller and responsive
    const chartOptions = {
      maintainAspectRatio: false,
      responsive: true
    }

    return (
      <div>
        {error ? (
          <p>Error: {error}</p>
        ) : (
          <div>
            <h2>Vehicle Status Distribution</h2>
            {Object.keys(statusCounts).length > 0 ? (
              <div style={{ width: '300px', height: '300px', margin: 'auto' }}>
                <Doughnut data={chartData} options={chartOptions} />
              </div>
            ) : (
              <p>No data available for the chart.</p>
            )}
          </div>
        )}
      </div>
    )
  }
}
