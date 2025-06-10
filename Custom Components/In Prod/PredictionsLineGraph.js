// PredictionsLineGraph.js

const TyreEnginePredictionChart = () => {
  const [allVehiclesData, setAllVehiclesData] = useState([])
  const [vehicleMetadata, setVehicleMetadata] = useState([])
  const [selectedVehicleId, setSelectedVehicleId] = useState('')
  const [selectedMetric, setSelectedMetric] = useState('engine_temperature')

  // Fetch prediction data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.post(
          'https://swift-cloud.ephlux.com/api-swift/ned/integration/g7tSCP-7or?SWIFT_API_KEY=6Y5MkiaY7Q-Diwy-tm4Y7JE',
          { user: 'test' }
        )
        const items = response?.data?.response?.obj || []
        if (items.length) {
          setAllVehiclesData(items)
          if (!selectedVehicleId && vehicleMetadata.length > 0) {
            setSelectedVehicleId(items[0].metadata.vehicle_id)
          }
        }
      } catch (err) {
        console.error('Error fetching data:', err)
      }
    }
    fetchData()
  }, [vehicleMetadata, selectedVehicleId])

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
            vehicle_id: parseInt(item.vehicle_id, 10) || 0,
            make: item.make || 'Unknown',
            model: item.model || 'Unknown',
            license_plate: item.license_plate || 'N/A'
          }))
        )
      } catch (err) {
        console.error('Error fetching vehicles:', err)
      }
    }
    fetchVehicles()
  }, [])

  // Build chart data with styled points
  const buildChartData = () => {
    if (!selectedVehicleId || allVehiclesData.length === 0) return null
    const selectedData = allVehiclesData.find(
      (item) => item.metadata.vehicle_id === selectedVehicleId
    )
    if (!selectedData) return null

    const predictions = selectedData.predictions

    const getTimeLabels = (arr) =>
      arr.map((d) =>
        new Date(d.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit'
        })
      )

    const getStyledDataset = (label, arr, baseColor, thresholdFn) => {
      const data = []
      const bgColors = []
      const borderColors = []
      arr.forEach((d) => {
        const val = d.value
        data.push(val)
        const isAlert = thresholdFn(val)
        const ptColor = isAlert ? 'red' : baseColor
        bgColors.push(ptColor)
        borderColors.push('#fff') // white border for contrast
      })
      return {
        label,
        data,
        borderColor: baseColor,
        borderWidth: 2,
        pointBackgroundColor: bgColors,
        pointBorderColor: borderColors,
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        fill: false,
        tension: 0.3
      }
    }

    const colors = {
      front_left: '#1abc9c',
      front_right: '#3498db',
      rear_left: '#f1c40f',
      rear_right: '#e67e22'
    }

    if (selectedMetric === 'tyre_temperature') {
      const sample = predictions.tyre_temperature_c.front_left
      const labels = getTimeLabels(sample)
      return {
        labels,
        datasets: [
          getStyledDataset(
            'Front Left',
            predictions.tyre_temperature_c.front_left,
            colors.front_left,
            (v) => v > 80
          ),
          getStyledDataset(
            'Front Right',
            predictions.tyre_temperature_c.front_right,
            colors.front_right,
            (v) => v > 80
          ),
          getStyledDataset(
            'Rear Left',
            predictions.tyre_temperature_c.rear_left,
            colors.rear_left,
            (v) => v > 80
          ),
          getStyledDataset(
            'Rear Right',
            predictions.tyre_temperature_c.rear_right,
            colors.rear_right,
            (v) => v > 80
          )
        ]
      }
    }

    if (selectedMetric === 'tyre_pressure') {
      const sample = predictions.tyre_pressure_psi.front_left
      const labels = getTimeLabels(sample)
      return {
        labels,
        datasets: [
          getStyledDataset(
            'Front Left',
            predictions.tyre_pressure_psi.front_left,
            colors.front_left,
            (v) => v < 27
          ),
          getStyledDataset(
            'Front Right',
            predictions.tyre_pressure_psi.front_right,
            colors.front_right,
            (v) => v < 27
          ),
          getStyledDataset(
            'Rear Left',
            predictions.tyre_pressure_psi.rear_left,
            colors.rear_left,
            (v) => v < 27
          ),
          getStyledDataset(
            'Rear Right',
            predictions.tyre_pressure_psi.rear_right,
            colors.rear_right,
            (v) => v < 27
          )
        ]
      }
    }

    if (selectedMetric === 'engine_temperature') {
      const labels = getTimeLabels(predictions.engine_temperature_c)
      return {
        labels,
        datasets: [
          getStyledDataset(
            'Engine Temperature (°C)',
            predictions.engine_temperature_c,
            '#c0392b',
            (v) => v > 80
          )
        ]
      }
    }

    return null
  }

  const chartDataObj = buildChartData()

  // Map vehicle IDs to names
  const vehicleIdToName = {}
  vehicleMetadata.forEach((v) => {
    vehicleIdToName[v.vehicle_id] = `${v.make} ${v.model}`
  })

  // Combine unique vehicle IDs
  const uniqueVehicleIds = Array.from(
    new Set(allVehiclesData.map((i) => i.metadata.vehicle_id))
  )

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
          text: selectedMetric.includes('temperature')
            ? 'Temperature (°C)'
            : 'Pressure (PSI)'
        },
        ticks: {
          callback: (v) =>
            `${v}${selectedMetric.includes('temperature') ? '°C' : ' PSI'}`
        }
      },
      x: {
        title: {
          display: true,
          text: 'Time'
        }
      }
    }
  }

  return (
    <div
      style={{
        margin: '40px auto',
        padding: '24px',
        maxWidth: '960px',
        backgroundColor: '#f7fafc',
        borderRadius: '16px',
        boxShadow: '0 12px 24px rgba(0,0,0,0.1)',
        fontFamily: 'Segoe UI, sans-serif'
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
        🚗 Vehicle Sensor Predictions
      </h1>

      {allVehiclesData.length > 0 && (
        <p
          style={{
            textAlign: 'center',
            marginBottom: '32px',
            color: '#4a5568'
          }}
        >
          Predictions as of{' '}
          <strong>
            {new Date(
              Math.max(
                ...allVehiclesData.map((i) =>
                  new Date(i.metadata.date).getTime()
                )
              )
            ).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </strong>
        </p>
      )}

      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '24px',
          flexWrap: 'wrap',
          marginBottom: '32px'
        }}
      >
        <div>
          <label
            style={{
              display: 'block',
              fontWeight: '600',
              marginBottom: '8px',
              color: '#2d3748'
            }}
          >
            Vehicle
          </label>
          <select
            value={selectedVehicleId}
            onChange={(e) => setSelectedVehicleId(e.target.value)}
            style={{
              width: '180px',
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid #cbd5e0',
              backgroundColor: '#fff'
            }}
          >
            {uniqueVehicleIds.map((id) => (
              <option key={id} value={id}>
                {vehicleIdToName[id] || id}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            style={{
              display: 'block',
              fontWeight: '600',
              marginBottom: '8px',
              color: '#2d3748'
            }}
          >
            Metric
          </label>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            style={{
              width: '200px',
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid #cbd5e0',
              backgroundColor: '#fff'
            }}
          >
            <option value='engine_temperature'>Engine Temperature</option>
            <option value='tyre_temperature'>Tyre Temperature</option>
            <option value='tyre_pressure'>Tyre Pressure</option>
          </select>
        </div>
      </div>

      {chartDataObj ? (
        <div
          style={{
            backgroundColor: '#fff',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 8px 16px rgba(0,0,0,0.05)'
          }}
        >
          <Line data={chartDataObj} options={chartOptions} />
        </div>
      ) : (
        <p style={{ textAlign: 'center', color: '#718096' }}>
          Loading chart...
        </p>
      )}
    </div>
  )
}

// Render component
render(<TyreEnginePredictionChart />, document.getElementById('root'))
