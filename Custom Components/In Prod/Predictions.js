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
        const items = response?.data?.response?.obj

        if (Array.isArray(items) && items.length > 0) {
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
  }, [vehicleMetadata]) // Re-run fetchData once vehicle metadata is available

  // Fetch vehicle metadata (make + model)
  useEffect(() => {
    const fetchVehicles = async () => {
      try {
        const response = await axios.post(
          'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1',
          { user: 'test' }
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
          setVehicleMetadata(vehicles)
        } else {
          console.error('Invalid vehicle metadata response')
        }
      } catch (err) {
        console.error('Error fetching vehicles:', err)
      }
    }

    fetchVehicles()
  }, [])

  const buildChartData = () => {
    if (!selectedVehicleId || allVehiclesData.length === 0) return null

    const selectedData = allVehiclesData.find(
      (item) => item.metadata.vehicle_id === selectedVehicleId
    )
    if (!selectedData) return null

    const predictions = selectedData.predictions

    const getTimeLabels = (dataArr) =>
      dataArr.map((d) =>
        new Date(d.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit'
        })
      )

    const getDataset = (label, dataArr, color, transformFn) => ({
      label,
      data: dataArr.map((d) => (transformFn ? transformFn(d.value) : d.value)),
      borderColor: color,
      fill: false,
      tension: 0.3,
      pointRadius: 2
    })

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
          getDataset(
            'Front Left',
            predictions.tyre_temperature_c.front_left,
            colors.front_left
          ),
          getDataset(
            'Front Right',
            predictions.tyre_temperature_c.front_right,
            colors.front_right
          ),
          getDataset(
            'Rear Left',
            predictions.tyre_temperature_c.rear_left,
            colors.rear_left
          ),
          getDataset(
            'Rear Right',
            predictions.tyre_temperature_c.rear_right,
            colors.rear_right
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
          getDataset(
            'Front Left',
            predictions.tyre_pressure_psi.front_left,
            colors.front_left
          ),
          getDataset(
            'Front Right',
            predictions.tyre_pressure_psi.front_right,
            colors.front_right
          ),
          getDataset(
            'Rear Left',
            predictions.tyre_pressure_psi.rear_left,
            colors.rear_left
          ),
          getDataset(
            'Rear Right',
            predictions.tyre_pressure_psi.rear_right,
            colors.rear_right
          )
        ]
      }
    }

    if (selectedMetric === 'engine_temperature') {
      const labels = getTimeLabels(predictions.engine_temperature_c)
      return {
        labels,
        datasets: [
          getDataset(
            'Engine Temperature(°C)',
            predictions.engine_temperature_c,
            '#c0392b',
            (val) => val - 60
          )
        ]
      }
    }

    return null
  }

  const chartDataObj = buildChartData()

  // Create ID + name map
  const vehicleIdToName = {}
  vehicleMetadata.forEach((vehicle) => {
    vehicleIdToName[vehicle.vehicle_id] = `${vehicle.make} ${vehicle.model}`
  })

  const uniqueVehicleIds = [
    ...new Set(allVehiclesData.map((item) => item.metadata.vehicle_id))
  ]

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
          callback: (val) =>
            `${val}${selectedMetric.includes('temperature') ? '°C' : ' PSI'}`
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
        padding: '30px',
        fontFamily: "'Segoe UI', sans-serif",
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
        maxWidth: '900px',
        margin: 'auto'
      }}
    >
      <h2 style={{ color: '#2c3e50', marginBottom: '25px', fontSize: '26px' }}>
        🚗 Vehicle Sensor Data Predictions
      </h2>

      {allVehiclesData.length > 0 && (
        <h2
          style={{ color: '#2c3e50', marginBottom: '25px', fontSize: '26px' }}
        >
          Predictions for:{' '}
          {new Date(
            Math.max(
              ...allVehiclesData.map((item) =>
                new Date(item.metadata.date).getTime()
              )
            )
          ).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </h2>
      )}

      <div
        style={{
          display: 'flex',
          gap: '20px',
          marginBottom: '25px',
          alignItems: 'center',
          flexWrap: 'wrap'
        }}
      >
        <div>
          <label style={{ fontWeight: '600', marginRight: '10px' }}>
            Vehicle:
          </label>
          <select
            value={selectedVehicleId}
            onChange={(e) => setSelectedVehicleId(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid #ccc',
              minWidth: '160px'
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
          <label style={{ fontWeight: '600', marginRight: '10px' }}>
            Metric:
          </label>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid #ccc',
              minWidth: '200px'
            }}
          >
            <option value='engine_temperature'>Engine Temperature</option>
            <option value='tyre_temperature'>Tyre Temperature</option>
            <option value='tyre_pressure'>Tyre Pressure</option>
          </select>
        </div>
      </div>

      {chartDataObj ? (
        <Line
          data={{
            labels: chartDataObj.labels,
            datasets: chartDataObj.datasets
          }}
          options={chartOptions}
        />
      ) : (
        <p>Loading chart...</p>
      )}
    </div>
  )
}
render(<TyreEnginePredictionChart />)
