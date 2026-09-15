import { useState, useEffect } from 'react'
import { api } from '../api/client'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts'

const fmtCurrency = (n) => {
  if (n === undefined || n === null || isNaN(n)) return '$0'
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(1)}K`
  return `$${Number(n).toFixed(0)}`
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#FFFFFF',
      border: '1px solid #DDDAD3',
      borderRadius: '6px',
      padding: '8px 12px',
      fontSize: '12px',
      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.08)'
    }}>
      <p style={{ color: '#66645F', marginBottom: '4px', fontWeight: 600 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: '#1C1C1C', margin: '2px 0' }}>
          {p.name}: <strong style={{ color: p.color || '#2F5D50' }}>{fmtCurrency(p.value)}</strong>
        </p>
      ))}
    </div>
  )
}

export default function Forecast() {
  const [stores, setStores] = useState([])
  const [departments, setDepartments] = useState([])
  const [storeId, setStoreId] = useState(1)
  const [deptId, setDeptId] = useState(1)
  const [horizon, setHorizon] = useState(4)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getStores().then((res) => setStores(res || [])).catch(() => {})
  }, [])

  useEffect(() => {
    api.getDepartments(storeId).then((res) => setDepartments(res || [])).catch(() => {})
  }, [storeId])

  const runForecast = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await api.postForecast(storeId, deptId, horizon)
      setResult(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Combine historical reference with projected steps
  const chartData = result
    ? [
        {
          week: `${result.historical_summary.last_known_date} (Hist)`,
          historical_sales: result.historical_summary.last_known_sales,
          predicted_sales: result.historical_summary.last_known_sales
        },
        ...result.predictions.map((p) => ({
          week: p.week,
          predicted_sales: p.weekly_sales,
          holiday: p.is_holiday
        }))
      ]
    : []

  const avgForecast = result && result.predictions.length
    ? result.predictions.reduce((acc, p) => acc + p.weekly_sales, 0) / result.predictions.length
    : 0

  const nextWeekForecast = result && result.predictions.length
    ? result.predictions[0].weekly_sales
    : 0

  return (
    <div className="forecast-page">
      <div className="page-header">
        <h2>Demand Forecast Explorer</h2>
        <p>Forecast future weekly sales using historical demand patterns, store characteristics and retail features.</p>
      </div>

      {/* Control Panel */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="forecast-controls">
          <div className="form-group" style={{ flex: 1, minWidth: '180px' }}>
            <label>Store</label>
            <select
              value={storeId}
              onChange={(e) => setStoreId(Number(e.target.value))}
            >
              {stores.map((s) => (
                <option key={s.store_id} value={s.store_id}>
                  Store {s.store_id} (Type {s.store_type}, {Number(s.store_size).toLocaleString()} sqft)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ minWidth: '140px' }}>
            <label>Department</label>
            <select
              value={deptId}
              onChange={(e) => setDeptId(Number(e.target.value))}
            >
              {departments.map((d) => (
                <option key={d} value={d}>Department {d}</option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ minWidth: '160px' }}>
            <label>Horizon: {horizon} Weeks</label>
            <input
              type="range"
              min={1}
              max={12}
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
            />
          </div>

          <button
            className="btn-primary"
            onClick={runForecast}
            disabled={loading}
            style={{ height: '38px', alignSelf: 'flex-end' }}
          >
            {loading ? 'Calculating...' : 'Generate Forecast'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner" style={{ marginBottom: '20px' }}>
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="loading-container">
          <div className="spinner" />
          <div className="loading-text">Generating recursive demand forecast...</div>
        </div>
      )}

      {result && (
        <>
          {/* Summary KPIs */}
          <div className="kpi-grid" style={{ marginBottom: '20px' }}>
            <div className="kpi-card">
              <div className="kpi-label">Store & Department</div>
              <div className="kpi-value" style={{ fontSize: '18px' }}>
                Store {result.store_id} · Dept {result.dept_id}
              </div>
              <div className="kpi-sub">Target segment</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Horizon</div>
              <div className="kpi-value">
                {result.horizon_weeks} Weeks
              </div>
              <div className="kpi-sub">Recursive multi-step forecast</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Next Week Forecast</div>
              <div className="kpi-value" style={{ color: 'var(--accent-primary)' }}>
                {fmtCurrency(nextWeekForecast)}
              </div>
              <div className="kpi-sub">Week ending {result.predictions[0]?.week}</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Average Forecast</div>
              <div className="kpi-value">
                {fmtCurrency(avgForecast)}
              </div>
              <div className="kpi-sub">Across {result.horizon_weeks} weeks</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Model Engine</div>
              <div className="kpi-value" style={{ fontSize: '14px' }}>
                {result.model_type}
              </div>
              <div className="kpi-sub">v{result.model_version}</div>
            </div>
          </div>

          {/* Historical vs Forecast Main Chart */}
          <div className="chart-card" style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3>Historical Demand & Predicted Trend</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Historical Mean: <strong>{fmtCurrency(result.historical_summary.historical_mean_sales)}</strong>
              </span>
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ECEAE4" vertical={false} />
                <XAxis dataKey="week" stroke="#8A8882" tick={{ fill: '#66645F', fontSize: 11 }} />
                <YAxis stroke="#8A8882" tick={{ fill: '#66645F', fontSize: 11 }} tickFormatter={(v) => fmtCurrency(v)} />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Historical Mean Baseline */}
                <ReferenceLine
                  y={result.historical_summary.historical_mean_sales}
                  stroke="#8A8882"
                  strokeDasharray="4 4"
                  label={{ value: 'Historical Mean', fill: '#66645F', fontSize: 11, position: 'top' }}
                />

                {/* Forecast Starts Separator */}
                <ReferenceLine
                  x={`${result.historical_summary.last_known_date} (Hist)`}
                  stroke="#DDDAD3"
                  strokeDasharray="2 2"
                  label={{ value: 'Forecast Starts', fill: '#66645F', fontSize: 11, position: 'insideTopLeft' }}
                />

                <Line
                  type="monotone"
                  dataKey="predicted_sales"
                  name="Forecasted Sales"
                  stroke="#2F5D50"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#2F5D50' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Week-by-Week Table */}
          <div className="card" style={{ marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '14px', fontSize: '14px', fontWeight: 600 }}>
              Forecast Schedule
            </h3>
            <table className="forecast-table">
              <thead>
                <tr>
                  <th>Step</th>
                  <th>Week Ending</th>
                  <th>Forecasted Sales</th>
                  <th>Holiday</th>
                  <th>Feature Context</th>
                </tr>
              </thead>
              <tbody>
                {result.predictions.map((p) => (
                  <tr key={p.step}>
                    <td style={{ fontWeight: 600 }}>Step {p.step}</td>
                    <td>{p.week}</td>
                    <td style={{ fontWeight: 600, color: '#2F5D50' }}>
                      ${p.weekly_sales.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td>
                      {p.is_holiday ? (
                        <span className="holiday-badge">Holiday</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Regular</span>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                      {p.assumptions.join('; ') || 'Continuous lag & rolling statistics roll'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* How this forecast works */}
          <div className="card" style={{ background: 'var(--bg-card-secondary)', border: '1px solid var(--border-medium)' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-primary)', marginBottom: '6px' }}>
              How This Forecast Works
            </h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '12.5px', lineHeight: 1.6 }}>
              RetailIQ uses historical weekly sales together with lag patterns, rolling statistics, calendar information,
              store characteristics and available economic/promotional features to estimate future weekly sales via the <strong>{result.model_type}</strong>.
            </p>
          </div>
        </>
      )}

      {!result && !loading && !error && (
        <div className="empty-state">
          <p>Select a store and department above, then click <strong>Generate Forecast</strong> to project weekly sales.</p>
        </div>
      )}
    </div>
  )
}
