const CombinedVehicleChart = () => {
  const [mode, setMode] = useState('predicted') // "predicted" or "realtime"
  const [vehicles, setVehicles] = useState([])
  const [selectedVehicle, setSelectedVehicle] = useState('')
  const [metric, setMetric] = useState('engine_temperature')
  const [chartData, setChartData] = useState(null)
  const [error, setError] = useState('')

  // common chart options
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      tooltip: { mode: 'index', intersect: false }
    },
    scales: {
      x: { title: { display: true, text: 'Time' } },
      y: {
        title: {
          display: true,
          text:
            metric === 'tyre_pressure' ? 'Pressure (PSI)' : 'Temperature (°C)'
        },
        ticks: {
          callback: (val) =>
            metric === 'tyre_pressure' ? `${val} PSI` : `${val}°C`
        }
      }
    }
  }

  // load vehicle list on mount
  useEffect(() => {
    axios
      .post(
        'https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=4LVIflv9QMrGVVK1',
        { user: 'test' }
      )
      .then((resp) => {
        const arr = resp.data.actions?.[0]?.obj || []
        const list = arr.map((v) => ({
          id: String(v.vehicle_id),
          name: `${v.make || 'Unknown'} ${v.model || ''}`.trim()
        }))
        setVehicles(list)
        if (!selectedVehicle && list.length) setSelectedVehicle(list[0].id)
      })
      .catch(() => setError('Failed to load vehicles'))
  }, [])

  // fetch data whenever mode, selectedVehicle, or metric changes
  useEffect(() => {
    if (!selectedVehicle) return

    let intervalId
    async function fetchData() {
      setError('')
      try {
        let labels = []
        let datasets = []
        if (mode === 'predicted') {
          const resp = await axios.post(
            'https://swift-cloud.ephlux.com/api-swift/ned/integration/g7tSCP-7or?SWIFT_API_KEY=6Y5MkiaY7Q-Diwy-tm4Y7JE',
            { user: 'test' }
          )
          const items = resp.data.response?.obj || []
          const sel = items.find(
            (i) => String(i.metadata.vehicle_id) === selectedVehicle
          )
          if (!sel) throw new Error('No prediction data for this vehicle')

          const getTimeLabels = (arr) =>
            arr.map((d) =>
              new Date(d.timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })
            )

          const getDataset = (label, arr, color, xf = (v) => v) => ({
            label,
            data: arr.map((d) => xf(d.value ?? d)),
            borderColor: color,
            fill: false,
            tension: 0.3,
            pointRadius: 2
          })

          if (metric === 'engine_temperature') {
            labels = getTimeLabels(sel.predictions.engine_temperature_c)
            datasets = [
              getDataset(
                'Engine Temperature (°C)',
                sel.predictions.engine_temperature_c,
                '#c0392b'
              )
            ]
          } else {
            const pts = sel.predictions.tyre_pressure_psi
            labels = getTimeLabels(pts.front_left)
            datasets = [
              getDataset('Front Left', pts.front_left, '#1abc9c'),
              getDataset('Front Right', pts.front_right, '#3498db'),
              getDataset('Rear Left', pts.rear_left, '#f1c40f'),
              getDataset('Rear Right', pts.rear_right, '#e67e22')
            ]
          }
        } else {
          const resp = await axios.post(
            'https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=tdFQHIL9F97blZ-D7eeUPblvx',
            { user: 'test' }
          )
          const arr = resp.data.response?.obj || []
          const me = arr
            .filter((i) => String(i.vehicle_id) === selectedVehicle)
            .filter((i) => !i.latitude && !i.longitude && !i.speed)
            .slice(-200)
          if (!me.length) throw new Error('No realtime data for this vehicle')

          labels = me.map((i) =>
            new Date(i.timestamp || i.createdAt).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })
          )
          const fl = [],
            fr = [],
            rl = [],
            rr = [],
            et = []
          me.forEach((i) => {
            const pfl = i.front_left?.pressure ?? null
            fl.push(pfl === 0 ? null : pfl)
            const pfr = i.front_right?.pressure ?? null
            fr.push(pfr === 0 ? null : pfr)
            const prl = i.rear_left?.pressure ?? null
            rl.push(prl === 0 ? null : prl)
            const prr = i.rear_right?.pressure ?? null
            rr.push(prr === 0 ? null : prr)
            const rawT = parseFloat(i.temperature)
            const adj = isNaN(rawT) ? null : rawT - 60
            et.push(adj === 0 ? null : adj)
          })

          if (metric === 'engine_temperature') {
            datasets = [
              {
                label: 'Engine Temperature (°C)',
                data: et,
                borderColor: '#c0392b',
                fill: false,
                tension: 0.4,
                spanGaps: true
              }
            ]
          } else {
            datasets = [
              {
                label: 'Front Left',
                data: fl,
                borderColor: '#1abc9c',
                fill: false,
                tension: 0.4,
                spanGaps: true
              },
              {
                label: 'Front Right',
                data: fr,
                borderColor: '#3498db',
                fill: false,
                tension: 0.4,
                spanGaps: true
              },
              {
                label: 'Rear Left',
                data: rl,
                borderColor: '#f1c40f',
                fill: false,
                tension: 0.4,
                spanGaps: true
              },
              {
                label: 'Rear Right',
                data: rr,
                borderColor: '#e67e22',
                fill: false,
                tension: 0.4,
                spanGaps: true
              }
            ]
          }

          // set up polling only in realtime mode
          intervalId = setInterval(fetchData, 1000)
        }

        setChartData({ labels, datasets })
      } catch (err) {
        setError(err.message)
      }
    }

    fetchData()
    return () => clearInterval(intervalId)
  }, [mode, selectedVehicle, metric])

  return (
    <div style={{ width: '100%', margin: '20px auto', padding: '20px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <h2>
          Vehicle Data — {mode === 'predicted' ? 'Predicted' : 'Realtime'}
        </h2>
        <button
          type='button'
          onClick={() =>
            setMode((m) => (m === 'predicted' ? 'realtime' : 'predicted'))
          }
        >
          Switch to {mode === 'predicted' ? 'Realtime' : 'Predicted'}
        </button>
      </div>
      <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
        <select
          value={selectedVehicle}
          onChange={(e) => setSelectedVehicle(e.target.value)}
        >
          {vehicles.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
        </select>
        <select value={metric} onChange={(e) => setMetric(e.target.value)}>
          <option value='engine_temperature'>Engine Temperature</option>
          <option value='tyre_pressure'>Tyre Pressure</option>
        </select>
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {chartData ? (
        <Line data={chartData} options={chartOptions} />
      ) : (
        <p>Loading...</p>
      )}
    </div>
  )
}

render(<CombinedVehicleChart />)
