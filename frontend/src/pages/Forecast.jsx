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
      background: 'rgba(15, 23, 42, 0.95)',
      border: '1px solid rgba(148, 163, 184, 0.2)',
      borderRadius: '8px',
      padding: '10px 14px',
      fontSize: '12px',
      boxShadow: '0 8px 24px rgba(0,0,0,0.5)'
    }}>
      <p style={{ color: '#94a3b8', marginBottom: '4px', fontWeight: 600 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || '#60a5fa', margin: '2px 0' }}>
          {p.name}: <strong>{fmtCurrency(p.value)}</strong>
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

  // Combine historical baseline reference with forecast points for visualization
  const chartData = result
    ? [
        {
          week: `${result.historical_summary.last_known_date} (Hist)`,
          historical_sales: result.historical_summary.last_known_sales,
          predicted_sales: result.historical_summary.last_known_sales,
          is_boundary: true
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

      {/* Controls Card */}
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <div className="forecast-controls">
          <div className="form-group" style={{ flex: 1, minWidth: '200px' }}>
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

          <div className="form-group" style={{ minWidth: '150px' }}>
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

          <div className="form-group" style={{ minWidth: '180px' }}>
            <label>Forecast Horizon: {horizon} Weeks</label>
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
            style={{ height: '42px', alignSelf: 'flex-end' }}
          >
            {loading ? '⏳ Computing...' : '🔮 Generate Forecast'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner" style={{ marginBottom: '24px' }}>
          <span>⚠️ {error}</span>
        </div>
      )}

      {loading && (
        <div className="loading-container">
          <div className="spinner" />
          <div className="loading-text">Computing recursive multi-step LightGBM demand forecast...</div>
        </div>
      )}

      {result && (
        <>
          {/* Forecast Summary KPIs */}
          <div className="kpi-grid" style={{ marginBottom: '24px' }}>
            <div className="kpi-card">
              <span className="kpi-icon">🏪</span>
              <div className="kpi-label">Store & Dept</div>
              <div className="kpi-value" style={{ fontSize: '20px' }}>
                Store {result.store_id} • Dept {result.dept_id}
              </div>
              <div className="kpi-sub">Target Time-Series Segment</div>
            </div>

            <div className="kpi-card">
              <span className="kpi-icon">⏱️</span>
              <div className="kpi-label">Horizon</div>
              <div className="kpi-value">
                {result.horizon_weeks} Weeks
              </div>
              <div className="kpi-sub">Recursive multi-step roll</div>
            </div>

            <div className="kpi-card">
              <span className="kpi-icon">🎯</span>
              <div className="kpi-label">Next Week Forecast</div>
              <div className="kpi-value" style={{ color: 'var(--accent-primary)' }}>
                {fmtCurrency(nextWeekForecast)}
              </div>
              <div className="kpi-sub">Week of {result.predictions[0]?.week}</div>
            </div>

            <div className="kpi-card">
              <span className="kpi-icon">📊</span>
              <div className="kpi-label">Average Forecast</div>
              <div className="kpi-value" style={{ color: 'var(--accent-success)' }}>
                {fmtCurrency(avgForecast)}
              </div>
              <div className="kpi-sub">Across {result.horizon_weeks} weeks horizon</div>
            </div>

            <div className="kpi-card">
              <span className="kpi-icon">🤖</span>
              <div className="kpi-label">Model Engine</div>
              <div className="kpi-value" style={{ fontSize: '15px' }}>
                {result.model_type}
              </div>
              <div className="kpi-sub">Version {result.model_version}</div>
            </div>
          </div>

          {/* Historical vs Forecast Main Chart */}
          <div className="chart-card" style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3>
                <span className="chart-icon">📈</span> Historical Baseline vs. Projected Demand
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Historical Mean: <strong>{fmtCurrency(result.historical_summary.historical_mean_sales)}</strong>
              </span>
            </div>

            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="week" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => fmtCurrency(v)} />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Historical Mean Reference Line */}
                <ReferenceLine
                  y={result.historical_summary.historical_mean_sales}
                  stroke="#f59e0b"
                  strokeDasharray="4 4"
                  label={{ value: 'Historical Mean', fill: '#f59e0b', fontSize: 11, position: 'top' }}
                />

                {/* Forecast Starts Vertical Reference Line */}
                <ReferenceLine
                  x={`${result.historical_summary.last_known_date} (Hist)`}
                  stroke="#ec4899"
                  strokeDasharray="3 3"
                  label={{ value: 'Forecast Starts', fill: '#ec4899', fontSize: 11, position: 'insideTopLeft' }}
                />

                <Line
                  type="monotone"
                  dataKey="predicted_sales"
                  name="Forecasted Sales"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{ r: 5, fill: '#3b82f6', stroke: '#111827', strokeWidth: 2 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Week-by-Week Predictions Table */}
          <div className="glass-card" style={{ marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '16px', fontSize: '15px', fontWeight: 600 }}>
              <span style={{ marginRight: '8px' }}>📋</span> Week-by-Week Forecast Schedule
            </h3>
            <table className="forecast-table">
              <thead>
                <tr>
                  <th>Step</th>
                  <th>Week Ending</th>
                  <th>Forecasted Sales</th>
                  <th>Holiday Event</th>
                  <th>Feature Context & Assumptions</th>
                </tr>
              </thead>
              <tbody>
                {result.predictions.map((p) => (
                  <tr key={p.step}>
                    <td style={{ fontWeight: 600 }}>Step {p.step}</td>
                    <td>{p.week}</td>
                    <td style={{ fontWeight: 700, color: 'var(--text-accent)' }}>
                      ${p.weekly_sales.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td>
                      {p.is_holiday ? (
                        <span className="holiday-badge">🎄 Holiday Week</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Regular</span>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                      {p.assumptions.join('; ') || 'Continuous lag & rolling feature generation'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* How this forecast works Section */}
          <div className="glass-card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent-primary)', marginBottom: '8px' }}>
              💡 How This Forecast Works
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.65 }}>
              RetailIQ uses historical weekly sales together with recursive lag patterns (1, 2, 4, 8, 13, 26, 52 weeks),
              rolling window statistics (4, 8, 13-week mean and standard deviations), calendar information (week of year, holidays),
              store characteristics (Type A/B/C, square footage), and available macroeconomic and promotional features (MarkDown1–5, fuel price, CPI, unemployment)
              to estimate future weekly sales via the <strong>{result.model_type}</strong>.
            </p>
          </div>
        </>
      )}

      {!result && !loading && !error && (
        <div className="empty-state">
          <div className="empty-icon">🔮</div>
          <p>Select a store and department above, then click <strong>Generate Forecast</strong> to project weekly demand.</p>
        </div>
      )}
    </div>
  )
}
