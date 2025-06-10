// PredictedVehicleAlerts.js

const VehicleAlertsWidget = () => {
  const [allVehiclesData, setAllVehiclesData] = useState([])
  const [vehicleMetadata, setVehicleMetadata] = useState([])

  // Fetch prediction data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.post(
          'https://swift-cloud.ephlux.com/api-swift/ned/integration/g7tSCP-7or?SWIFT_API_KEY=6Y5MkiaY7Q-Diwy-tm4Y7JE',
          { user: 'test' }
        )
        const items = response?.data?.response?.obj || []
        setAllVehiclesData(items)
      } catch (err) {
        console.error('Error fetching data:', err)
      }
    }
    fetchData()
  }, [])

  // Fetch vehicle metadata
  useEffect(() => {
    const fetchVehicles = async () => {
      try {
        const response = await axios.post(
          'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1',
          { user: 'test' }
        )
        const items = response?.data?.actions?.[0]?.obj || []
        setVehicleMetadata(
          items.map((item) => ({
            vehicle_id: item.vehicle_id,
            make: item.make || 'Unknown',
            model: item.model || 'Unknown'
          }))
        )
      } catch (err) {
        console.error('Error fetching vehicles:', err)
      }
    }
    fetchVehicles()
  }, [])

  // Create mapping from vehicle_id to "Make Model"
  const vehicleIdToName = {}
  vehicleMetadata.forEach((v) => {
    vehicleIdToName[v.vehicle_id] = `${v.make} ${v.model}`
  })

  // Thresholds for alerts (adjusted to be more reachable)
  const THRESHOLDS = {
    engine_temperature_c: { max: 95 }, // Alert if > 95°C (was 100°C)
    tyre_temperature_c: { max: 70 }, // Alert if > 70°C (was 80°C)
    tyre_pressure_psi: { min: 28 } // Alert if < 28 PSI (was 27 PSI)
  }

  // Generate predicted alerts from the data
  const generatePredictedAlerts = () => {
    const alerts = []

    allVehiclesData.forEach((vehicle) => {
      const { metadata, predictions } = vehicle
      const vehicleId = metadata.vehicle_id
      const vehicleName = vehicleIdToName[vehicleId] || vehicleId

      // Check predictions data for alerts
      if (predictions) {
        // Engine Temperature (Predictions)
        predictions.engine_temperature_c.forEach((point) => {
          if (point.value > THRESHOLDS.engine_temperature_c.max) {
            alerts.push({
              vehicle: vehicleName,
              metric: 'Engine Temperature (Predicted)',
              value: `${point.value}°C`,
              threshold: `> ${THRESHOLDS.engine_temperature_c.max}°C`,
              date: point.timestamp,
              severity: 'critical'
            })
          }
        })

        // Tyre Temperature (Predictions)
        Object.entries(predictions.tyre_temperature_c).forEach(
          ([position, points]) => {
            points.forEach((point) => {
              if (point.value > THRESHOLDS.tyre_temperature_c.max) {
                alerts.push({
                  vehicle: vehicleName,
                  metric: `Tyre Temp (${position.replace(
                    '_',
                    ' '
                  )}) (Predicted)`,
                  value: `${point.value}°C`,
                  threshold: `> ${THRESHOLDS.tyre_temperature_c.max}°C`,
                  date: point.timestamp,
                  severity: 'warning'
                })
              }
            })
          }
        )

        // Tyre Pressure (Predictions)
        Object.entries(predictions.tyre_pressure_psi).forEach(
          ([position, points]) => {
            points.forEach((point) => {
              if (point.value < THRESHOLDS.tyre_pressure_psi.min) {
                alerts.push({
                  vehicle: vehicleName,
                  metric: `Tyre Pressure (${position.replace(
                    '_',
                    ' '
                  )}) (Predicted)`,
                  value: `${point.value} PSI`,
                  threshold: `< ${THRESHOLDS.tyre_pressure_psi.min} PSI`,
                  date: point.timestamp,
                  severity: 'critical'
                })
              }
            })
          }
        )
      }
    })

    // Sort alerts by date (most recent first)
    return alerts.sort((a, b) => new Date(b.date) - new Date(a.date))
  }

  const alerts = generatePredictedAlerts()

  return (
    <div
      style={{
        backgroundColor: '#f0f4f8',
        borderRadius: '12px',
        padding: '20px',
        maxWidth: '800px',
        margin: '40px auto',
        fontFamily: 'Segoe UI, sans-serif',
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
      }}
    >
      <h1
        style={{
          marginBottom: '16px',
          color: '#2d3748',
          fontSize: '28px',
          textAlign: 'center'
        }}
      >
        🚨 Predicted Vehicle Alerts
      </h1>

      {alerts.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#4a5568' }}>
          No predicted alerts at this time.
        </p>
      ) : (
        <div
          style={{
            backgroundColor: '#fff',
            borderRadius: '8px',
            padding: '15px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
            maxHeight: '400px',
            overflowY: 'auto'
          }}
        >
          {alerts.map((alert, index) => (
            <div
              key={index}
              style={{
                padding: '10px',
                borderBottom:
                  index < alerts.length - 1 ? '1px solid #e2e8f0' : 'none',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div>
                <p
                  style={{
                    fontWeight: '600',
                    color: alert.severity === 'critical' ? 'red' : '#d97706',
                    marginBottom: '4px'
                  }}
                >
                  {alert.vehicle} - {alert.metric}
                </p>
                <p style={{ color: '#4a5568', fontSize: '14px' }}>
                  Value: {alert.value} ({alert.threshold})
                </p>
                <p style={{ color: '#718096', fontSize: '12px' }}>
                  {new Date(alert.date).toLocaleString()}
                </p>
              </div>
              <span
                style={{
                  backgroundColor:
                    alert.severity === 'critical' ? '#fee2e2' : '#fef3c7',
                  color: alert.severity === 'critical' ? 'red' : '#d97706',
                  padding: '4px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  textTransform: 'uppercase',
                  fontWeight: '600'
                }}
              >
                {alert.severity}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Render component
render(<VehicleAlertsWidget />, document.getElementById('root'))
