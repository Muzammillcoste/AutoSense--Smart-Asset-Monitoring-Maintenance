import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Line } from 'react-chartjs-2'

// ---------- Helper: Format time ----------
const formatTime = (date) =>
  date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })

// ---------- Main Component ----------
const RealtimeAndPredictedVehicleData = () => {
  // States for vehicle list & selection
  const [vehicleData, setVehicleData] = useState([])
  const [selectedVehicle, setSelectedVehicle] = useState(null)

  // States for sensor data
  const [realSensorData, setRealSensorData] = useState(null)
  const [predictedSensorData, setPredictedSensorData] = useState(null)
  const [error, setError] = useState(null)
  const [pollingInterval, setPollingInterval] = useState(null)

  // Toggle mode: "realtime" or "predicted"
  const [mode, setMode] = useState('realtime')

  // Metric: "tyre_pressure" or "engine_temp"
  const [selectedMetric, setSelectedMetric] = useState('engine_temp')

  // ---------- Styles ----------
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
    backgroundColor: '#f0f2f5',
    minHeight: '100vh'
  }

  const headerStyle = {
    textAlign: 'center',
    color: '#34495e'
  }

  const toggleButtonStyle = {
    padding: '10px 20px',
    borderRadius: '25px',
    border: 'none',
    background: 'linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%)',
    color: '#fff',
    fontSize: '16px',
    cursor: 'pointer',
    transition: 'background 0.3s ease, transform 0.2s ease',
    alignSelf: 'center',
    marginBottom: '10px'
  }

  const mainContentStyle = {
    display: 'flex',
    gap: '20px',
    backgroundColor: '#fff',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
    flexGrow: 1
  }

  const sidebarStyle = {
    flex: '1',
    backgroundColor: '#ecf0f1',
    padding: '10px',
    borderRadius: '8px'
  }

  const sidebarItemStyle = (active) => ({
    padding: '15px',
    margin: '5px 0',
    backgroundColor: active ? '#3498db' : '#bdc3c7',
    color: active ? '#fff' : '#2c3e50',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'transform 0.2s'
  })

  const contentStyle = {
    flex: '2',
    padding: '10px'
  }

  const selectStyle = {
    padding: '8px 12px',
    borderRadius: '8px',
    fontSize: '15px',
    border: '1px solid #ccc',
    backgroundColor: '#ecf0f1',
    color: '#2c3e50',
    marginLeft: '10px'
  }

  // ---------- Fetch Vehicle Metadata (Common for both modes) ----------
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
          Array.isArray(response.data.actions?.[0]?.obj)
        ) {
          const vehicles = response.data.actions[0].obj.map((item) => ({
            vehicle_id: parseInt(item.vehicle_id, 10) || 0,
            make: item.make || 'Unknown',
            model: item.model || 'Unknown',
            year: item.year || 'Unknown',
            vin: item.vin || 'N/A',
            status: item.status || 'Unknown',
            license_plate: item.license_plate || 'N/A'
          }))
          setVehicleData(vehicles)
          if (!selectedVehicle && vehicles.length > 0) {
            setSelectedVehicle(vehicles[0].vehicle_id)
          }
        } else {
          setError('Error in API response or invalid data structure')
        }
      } catch (err) {
        console.error('Error fetching vehicles:', err)
        setError('Failed to fetch vehicle data')
      }
    }
    fetchVehicles()
  }, [selectedVehicle])

  // ---------- Real-Time Data Fetching (Polling every 1 sec) ----------
  useEffect(() => {
    if (mode !== 'realtime' || !selectedVehicle) return

    // Clear any existing interval if needed
    if (pollingInterval) clearInterval(pollingInterval)

    const fetchRealSensorData = async () => {
      try {
        const requestData = { user: 'test' }
        const response = await axios.post(
          'https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=tdFQHIL9F97blZ-D7eeUPblvx',
          requestData
        )
        const allVehicleData = response?.data?.response?.obj || []
        const currentVehicleData = allVehicleData.filter(
          (item) => String(item.vehicle_id) === String(selectedVehicle)
        )

        // Use the last 500 records and further filter out geo-data; then pick the last 200 records
        const last200 = (currentVehicleData.slice(-500) || [])
          .filter(
            (item) =>
              item.latitude == null &&
              item.longitude == null &&
              item.speed == null
          )
          .slice(-200)

        if (last200.length === 0) {
          setError('No sensor data found for this vehicle.')
          setRealSensorData(null)
          return
        } else {
          setError(null)
        }

        const labels = []
        const pressure_FL = []
        const pressure_FR = []
        const pressure_RL = []
        const pressure_RR = []
        const engineTemp = []

        last200.forEach((item) => {
          const rawDate = item.timestamp || item.createdAt
          const time = new Date(rawDate)
          if (!isNaN(time.getTime())) {
            labels.push(formatTime(time))
            pressure_FL.push(item?.front_lef?.pressure ?? null)
            pressure_FR.push(item?.front_right?.pressure ?? null)
            pressure_RL.push(item?.rear_left?.pressure ?? null)
            pressure_RR.push(item?.rear_right?.pressure ?? null)
            const temp = parseFloat(item.temperature)
            engineTemp.push(isNaN(temp) ? null : temp - 60)
          }
        })

        const chartData =
          selectedMetric === 'tyre_pressure'
            ? {
                labels,
                datasets: [
                  {
                    label: 'Front Left',
                    data: pressure_FL,
                    borderColor: '#1abc9c',
                    backgroundColor: '#1abc9c',
                    fill: false,
                    tension: 0.4,
                    spanGaps: true
                  },
                  {
                    label: 'Front Right',
                    data: pressure_FR,
                    borderColor: '#3498db',
                    backgroundColor: '#3498db',
                    fill: false,
                    tension: 0.4,
                    spanGaps: true
                  },
                  {
                    label: 'Rear Left',
                    data: pressure_RL,
                    borderColor: '#f1c40f',
                    backgroundColor: '#f1c40f',
                    fill: false,
                    tension: 0.4,
                    spanGaps: true
                  },
                  {
                    label: 'Rear Right',
                    data: pressure_RR,
                    borderColor: '#e67e22',
                    backgroundColor: '#e67e22',
                    fill: false,
                    tension: 0.4,
                    spanGaps: true
                  }
                ]
              }
            : {
                labels,
                datasets: [
                  {
                    label: 'Engine Temperature (−60°C)',
                    data: engineTemp,
                    borderColor: '#c0392b',
                    backgroundColor: '#c0392b',
                    fill: false,
                    tension: 0.4,
                    spanGaps: true
                  }
                ]
              }

        setRealSensorData(chartData)
      } catch (err) {
        console.error('Error fetching real-time sensor data:', err)
        setError('Failed to fetch real-time sensor data')
      }
    }

    // Initial fetch, then start interval polling.
    fetchRealSensorData()
    const interval = setInterval(fetchRealSensorData, 1000)
    setPollingInterval(interval)
    return () => clearInterval(interval)
  }, [mode, selectedVehicle, selectedMetric, pollingInterval])

  // ---------- Predicted Data Fetching (One-time on mode change) ----------
  useEffect(() => {
    if (mode !== 'predicted' || !selectedVehicle) return

    // For predicted data, fetch once (no polling)
    const fetchPredictedData = async () => {
      try {
        const requestData = { user: 'test' }
        const response = await axios.post(
          'https://swift-cloud.ephlux.com/api-swift/ned/integration/g7tSCP-7or?SWIFT_API_KEY=6Y5MkiaY7Q-Diwy-tm4Y7JE',
          requestData
        )
        const allPredictedData = response?.data?.response?.obj || []
        if (!Array.isArray(allPredictedData) || allPredictedData.length === 0) {
          setError('No predicted data available.')
          setPredictedSensorData(null)
          return
        }
        setError(null)
        const selectedData = allPredictedData.find(
          (item) => String(item.metadata.vehicle_id) === String(selectedVehicle)
        )
        if (!selectedData) {
          setError('No predicted data found for the selected vehicle.')
          setPredictedSensorData(null)
          return
        }
        const predictions = selectedData.predictions
        // Helper: Produce time labels from prediction data array
        const getTimeLabels = (dataArr) =>
          dataArr.map((d) =>
            new Date(d.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })
          )

        // Build chart data based on selected metric.
        let chartData
        if (selectedMetric === 'tyre_pressure') {
          const sample = predictions.tyre_pressure_psi.front_left
          const labels = getTimeLabels(sample)
          chartData = {
            labels,
            datasets: [
              {
                label: 'Front Left',
                data: predictions.tyre_pressure_psi.front_left.map(
                  (d) => d.value
                ),
                borderColor: '#1abc9c',
                fill: false,
                tension: 0.3,
                pointRadius: 2
              },
              {
                label: 'Front Right',
                data: predictions.tyre_pressure_psi.front_right.map(
                  (d) => d.value
                ),
                borderColor: '#3498db',
                fill: false,
                tension: 0.3,
                pointRadius: 2
              },
              {
                label: 'Rear Left',
                data: predictions.tyre_pressure_psi.rear_left.map(
                  (d) => d.value
                ),
                borderColor: '#f1c40f',
                fill: false,
                tension: 0.3,
                pointRadius: 2
              },
              {
                label: 'Rear Right',
                data: predictions.tyre_pressure_psi.rear_right.map(
                  (d) => d.value
                ),
                borderColor: '#e67e22',
                fill: false,
                tension: 0.3,
                pointRadius: 2
              }
            ]
          }
        } else if (selectedMetric === 'engine_temp') {
          const labels = getTimeLabels(predictions.engine_temperature_c)
          chartData = {
            labels,
            datasets: [
              {
                label: 'Engine Temperature (°C)',
                data: predictions.engine_temperature_c.map((d) => d.value - 60),
                borderColor: '#c0392b',
                fill: false,
                tension: 0.3,
                pointRadius: 2
              }
            ]
          }
        }
        setPredictedSensorData(chartData)
      } catch (err) {
        console.error('Error fetching predicted sensor data:', err)
        setError('Failed to fetch predicted sensor data')
      }
    }

    fetchPredictedData()
  }, [mode, selectedVehicle, selectedMetric])

  // ---------- Handle Vehicle Selection ----------
  const handleVehicleSelect = (vehicleId) => {
    setSelectedVehicle(vehicleId)
    setRealSensorData(null)
    setPredictedSensorData(null)
    if (pollingInterval) clearInterval(pollingInterval)
  }

  // ---------- Toggle Mode (Real-time / Predicted) ----------
  const toggleMode = () => {
    // Clear polling interval if switching from real-time
    if (mode === 'realtime' && pollingInterval) {
      clearInterval(pollingInterval)
    }
    setError(null)
    setMode((prev) => (prev === 'realtime' ? 'predicted' : 'realtime'))
  }

  // ---------- Chart Options ----------
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      tooltip: { mode: 'index', intersect: false }
    },
    scales: {
      y: {
        title: {
          display: true,
          text:
            selectedMetric === 'engine_temp'
              ? 'Temperature (°C)'
              : 'Pressure (PSI)'
        },
        ticks: {
          callback: (val) =>
            `${val}${selectedMetric === 'engine_temp' ? '°C' : ' PSI'}`
        }
      },
      x: {
        title: {
          display: true,
          text: 'Time'
        }
      }
    },
    animation: {
      duration: 800,
      easing: 'easeInOutQuad'
    }
  }

  // ---------- Determine which Chart Data to Show ----------
  const chartDataToShow =
    mode === 'realtime' ? realSensorData : predictedSensorData

  return (
    <div style={containerStyle}>
      <h1 style={headerStyle}>Vehicle Sensor Data Dashboard</h1>
      <button
        style={toggleButtonStyle}
        onMouseOver={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
        onMouseOut={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        onClick={toggleMode}
      >
        {mode === 'realtime'
          ? 'Show Predicted Data Graphs'
          : 'Show Real-Time Data Graphs'}
      </button>
      <div style={mainContentStyle}>
        {/* Sidebar: Vehicle List */}
        <aside style={sidebarStyle}>
          <h2 style={{ textAlign: 'center' }}>Vehicles</h2>
          {error && (
            <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>
          )}
          {vehicleData.length === 0 ? (
            <p style={{ textAlign: 'center' }}>Loading vehicles...</p>
          ) : (
            vehicleData.map((vehicle) => (
              <div
                key={vehicle.vehicle_id}
                onClick={() => handleVehicleSelect(vehicle.vehicle_id)}
                style={sidebarItemStyle(
                  String(vehicle.vehicle_id) === String(selectedVehicle)
                )}
              >
                <h4>{`${vehicle.make} ${vehicle.model}`}</h4>
                <p style={{ fontSize: '14px' }}>{vehicle.license_plate}</p>
              </div>
            ))
          )}
        </aside>
        {/* Main Content: Chart & Controls */}
        <div style={contentStyle}>
          {selectedVehicle ? (
            <>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px'
                }}
              >
                <h2 style={{ margin: 0 }}>
                  {mode === 'realtime'
                    ? 'Real-Time Sensor Data'
                    : 'Predicted Sensor Data'}
                </h2>
                <div>
                  <label htmlFor='metricSelect' style={{ marginRight: '10px' }}>
                    Metric:
                  </label>
                  <select
                    id='metricSelect'
                    value={selectedMetric}
                    onChange={(e) => setSelectedMetric(e.target.value)}
                    style={selectStyle}
                  >
                    <option value='tyre_pressure'>Tyre Pressure</option>
                    <option value='engine_temp'>Engine Temperature</option>
                  </select>
                </div>
              </div>
              {chartDataToShow ? (
                <Line data={chartDataToShow} options={chartOptions} />
              ) : (
                <p style={{ fontSize: '18px', color: '#7f8c8d' }}>
                  {mode === 'realtime'
                    ? 'Loading real-time sensor data...'
                    : 'Loading predicted sensor data...'}
                </p>
              )}
            </>
          ) : (
            <p style={{ fontSize: '18px', color: '#7f8c8d' }}>
              Select a vehicle to view sensor data.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

// ---------- Render the Component ----------
render(<RealtimeAndPredictedVehicleData />)
