
const VehicleSensorDashboard = () => {
    const [vehicleData, setVehicleData] = useState([])
    const [selectedVehicle, setSelectedVehicle] = useState(null)
    const [sensorData, setSensorData] = useState(null)
    const [error, setError] = useState(null)
    const [pollingInterval, setPollingInterval] = useState(null)
    const [selectedMetric, setSelectedMetric] = useState('engine_temp')
    const [isVehicleCritical, setIsVehicleCritical] = useState(false)
  
    // Inject blinking keyframes once
    useEffect(() => {
      const style = document.createElement('style')
      style.innerHTML = `
        @keyframes blinker {
          50% { opacity: 0; }
        }
      `
      document.head.appendChild(style)
      return () => document.head.removeChild(style)
    }, [])
  
    const formatTime = (date) =>
      date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
  
    // 1. Fetch vehicles on mount
    useEffect(() => {
      const fetchVehicles = async () => {
        try {
          const { data } = await axios.post(
            'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1',
            { user: 'test' }
          )
          const items = data.actions?.[0]?.obj
          if (!data.isError && Array.isArray(items)) {
            setVehicleData(
              items.map((item) => ({
                vehicle_id: parseInt(item.vehicle_id, 10) || 0,
                make: item.make || 'Unknown',
                model: item.model || 'Unknown',
                license_plate: item.license_plate || 'N/A',
              }))
            )
          } else {
            setError('Error in API response or invalid data structure')
          }
        } catch (err) {
          console.error(err)
          setError('Failed to fetch vehicle data')
        }
      }
      fetchVehicles()
    }, [])
  
    // 2. Fetch sensor data when vehicle or metric changes
    useEffect(() => {
      if (!selectedVehicle) return
  
      const fetchSensorData = async () => {
        try {
          const { data } = await axios.post(
            'https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=tdFQHIL9F97blZ-D7eeUPblvx',
            { user: 'test' }
          )
          const all = data.response?.obj?.filter(
            (i) => i.vehicle_id === selectedVehicle
          ) || []
          const recent = all.slice(-500).filter(
            (i) => i.latitude == null && i.longitude == null && i.speed == null
          ).slice(-200)
  
          if (!recent.length) {
            setError('No sensor data found for this vehicle.')
            setSensorData(null)
            return
          }
          setError(null)
  
          const labels = []
          const pFL = [], pFR = [], pRL = [], pRR = [], eT = []
  
          recent.forEach((it) => {
            const t = new Date(it.timestamp || it.createdAt)
            if (!isNaN(t)) {
              labels.push(formatTime(t))
              pFL.push(it.front_lef?.pressure ?? null)
              pFR.push(it.front_right?.pressure ?? null)
              pRL.push(it.rear_left?.pressure ?? null)
              pRR.push(it.rear_right?.pressure ?? null)
              const temp = parseFloat(it.temperature)
              eT.push(isNaN(temp) || temp === 0 ? null : temp)
            }
          })
  
          const filtered = {
            pressure_FL: pFL.map((v) => (v === 0 ? null : v)),
            pressure_FR: pFR.map((v) => (v === 0 ? null : v)),
            pressure_RL: pRL.map((v) => (v === 0 ? null : v)),
            pressure_RR: pRR.map((v) => (v === 0 ? null : v)),
            engineTemp: eT.map((v) => (v === 0 ? null : v)),
          }
  
          // build the same chartData you already had
          const chartData = {
            labels,
            datasets:
              selectedMetric === 'tyre_pressure'
                ? [
                    {
                      label: 'Front Left',
                      data: filtered.pressure_FL,
                      borderColor: '#1abc9c',
                      pointBackgroundColor: filtered.pressure_FL.map((v) =>
                        v !== null && v < 27 ? 'red' : '#1abc9c'
                      ),
                      fill: false,
                      tension: 0.4,
                      spanGaps: true,
                    },
                    {
                      label: 'Front Right',
                      data: filtered.pressure_FR,
                      borderColor: '#3498db',
                      pointBackgroundColor: filtered.pressure_FR.map((v) =>
                        v !== null && v < 27 ? 'red' : '#3498db'
                      ),
                      fill: false,
                      tension: 0.4,
                      spanGaps: true,
                    },
                    {
                      label: 'Rear Left',
                      data: filtered.pressure_RL,
                      borderColor: '#f1c40f',
                      pointBackgroundColor: filtered.pressure_RL.map((v) =>
                        v !== null && v < 27 ? 'red' : '#f1c40f'
                      ),
                      fill: false,
                      tension: 0.4,
                      spanGaps: true,
                    },
                    {
                      label: 'Rear Right',
                      data: filtered.pressure_RR,
                      borderColor: '#e67e22',
                      pointBackgroundColor: filtered.pressure_RR.map((v) =>
                        v !== null && v < 27 ? 'red' : '#e67e22'
                      ),
                      fill: false,
                      tension: 0.4,
                      spanGaps: true,
                    },
                    {
                      label: 'Min Safe Pressure (27 PSI)',
                      data: Array(labels.length).fill(27),
                      borderColor: 'red',
                      borderDash: [5, 5],
                      pointRadius: 0,
                      fill: false,
                    },
                  ]
                : [
                    {
                      label: 'Engine Temperature',
                      data: filtered.engineTemp,
                      borderColor: '#c0392b',
                      pointBackgroundColor: filtered.engineTemp.map((v) =>
                        v !== null && v > 80 ? 'red' : '#c0392b'
                      ),
                      fill: false,
                      tension: 0.4,
                      spanGaps: true,
                    },
                    {
                      label: 'Max Safe Temp (80°C)',
                      data: Array(labels.length).fill(80),
                      borderColor: 'red',
                      borderDash: [5, 5],
                      pointRadius: 0,
                      fill: false,
                    },
                  ],
          }
  
          setSensorData(chartData)
        } catch (err) {
          console.error(err)
          setError('Failed to fetch sensor data')
          setSensorData(null)
        }
      }
  
      fetchSensorData()
      const iv = setInterval(fetchSensorData, 1000)
      setPollingInterval(iv)
      return () => clearInterval(iv)
    }, [selectedVehicle, selectedMetric])
  
    // 3. Derive blinking state whenever sensorData updates
    useEffect(() => {
      if (!sensorData) {
        setIsVehicleCritical(false)
        return
      }
      const dataVals =
        selectedMetric === 'engine_temp'
          ? sensorData.datasets[0].data
          : sensorData.datasets
              .filter((ds) => !ds.label.includes('Min Safe'))
              .flatMap((ds) => ds.data)
  
      const critical =
        selectedMetric === 'engine_temp'
          ? dataVals.some((v) => v !== null && v > 80)
          : dataVals.some((v) => v !== null && v < 27)
  
      setIsVehicleCritical(critical)
    }, [sensorData, selectedMetric])
  
    const handleVehicleSelect = (vid) => {
      if (pollingInterval) clearInterval(pollingInterval)
      setSelectedVehicle(vid)
      setSensorData(null)
      setIsVehicleCritical(false)
    }
  
    const blinkingStyle = {
      animation: 'blinker 1s linear infinite',
      color: 'red',
    }
  
    return (
      <div style={{ display: 'flex', gap: '20px', padding: '20px' }}>
        <div style={{ flex: 1 }}>
          <h2>Vehicles</h2>
          {error && <p style={{ color: 'red' }}>{error}</p>}
          {vehicleData.length === 0 ? (
            <p>Loading vehicles...</p>
          ) : (
            vehicleData.map((v) => (
              <div
                key={v.vehicle_id}
                onClick={() => handleVehicleSelect(v.vehicle_id)}
                style={{
                  padding: '10px',
                  marginBottom: '5px',
                  cursor: 'pointer',
                  borderRadius: '5px',
                  backgroundColor:
                    selectedVehicle === v.vehicle_id ? '#3498db' : '#ecf0f1',
                  ...(selectedVehicle === v.vehicle_id && isVehicleCritical
                    ? blinkingStyle
                    : {}),
                }}
              >
                {v.make} {v.model} ({v.license_plate})
              </div>
            ))
          )}
        </div>
  
        <div style={{ flex: 3 }}>
          {selectedVehicle ? (
            <>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <h2>
                  Sensor Data –{' '}
                  {
                    vehicleData.find((x) => x.vehicle_id === selectedVehicle)
                      ?.make
                  }{' '}
                  {
                    vehicleData.find((x) => x.vehicle_id === selectedVehicle)
                      ?.model
                  }
                </h2>
                <select
                  value={selectedMetric}
                  onChange={(e) => setSelectedMetric(e.target.value)}
                  style={{
                    padding: '5px',
                    borderRadius: '4px',
                    border: '1px solid #ccc',
                  }}
                >
                  <option value='tyre_pressure'>Tyre Pressure</option>
                  <option value='engine_temp'>Engine Temperature</option>
                </select>
              </div>
              {sensorData ? (
                <Line
                  data={sensorData}
                  options={{
                    responsive: true,
                    plugins: { legend: { position: 'top' } },
                  }}
                />
              ) : (
                <p>Loading sensor data...</p>
              )}
            </>
          ) : (
            <p>Select a vehicle to view sensor data.</p>
          )}
        </div>
      </div>
    )
  }
  
  
  // Render
  render(<VehicleSensorDashboard />, document.getElementById('root'))
  