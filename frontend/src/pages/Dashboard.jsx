import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts'

const STORE_TYPE_COLORS = {
  A: '#2F5D50',
  B: '#5A7C71',
  C: '#8C7D68'
}

const fmtCurrency = (n) => {
  if (n === undefined || n === null || isNaN(n)) return '$0'
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
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
          {p.name}: <strong style={{ color: '#2F5D50' }}>{fmtCurrency(p.value)}</strong>
        </p>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [salesTrend, setSalesTrend] = useState([])
  const [storeRanking, setStoreRanking] = useState([])
  const [deptRanking, setDeptRanking] = useState([])
  const [holidayAnalysis, setHolidayAnalysis] = useState([])
  const [promoEffectiveness, setPromoEffectiveness] = useState([])
  const [storeTypes, setStoreTypes] = useState([])

  // Shared Filter State
  const [storesList, setStoresList] = useState([])
  const [deptList, setDeptList] = useState([])
  const [selectedStore, setSelectedStore] = useState('')
  const [selectedDept, setSelectedDept] = useState('')
  const [granularity, setGranularity] = useState('weekly')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Track latest request to avoid race conditions
  const latestRequestId = useRef(0)

  // Load store list once on mount
  useEffect(() => {
    async function loadStores() {
      try {
        const stores = await api.getStores()
        setStoresList(stores || [])
      } catch (err) {
        console.error('Failed to load stores metadata:', err)
      }
    }
    loadStores()
  }, [])

  // Update dependent department dropdown when selectedStore changes
  useEffect(() => {
    async function updateDepts() {
      try {
        const storeId = selectedStore ? Number(selectedStore) : null
        const depts = await api.getDepartments(storeId)
        setDeptList(depts || [])

        // If currently selected department is not in the store's department list, reset to all
        if (selectedDept && depts && !depts.includes(Number(selectedDept))) {
          setSelectedDept('')
        }
      } catch (err) {
        console.error('Failed to update departments list:', err)
      }
    }
    updateDepts()
  }, [selectedStore])

  // Fetch all dashboard metrics whenever filters change
  useEffect(() => {
    const requestId = ++latestRequestId.current
    let isCancelled = false

    async function loadDashboardData() {
      try {
        setLoading(true)
        setError(null)
        const storeId = selectedStore ? Number(selectedStore) : null
        const deptId = selectedDept ? Number(selectedDept) : null

        const [
          sumRes,
          trendRes,
          storeRankRes,
          deptRankRes,
          holRes,
          promoRes,
          typesRes
        ] = await Promise.all([
          api.getSummary(storeId, deptId),
          api.getSalesTrend({ granularity, store_id: storeId, dept_id: deptId }),
          api.getStoreRanking(10, deptId),
          api.getDeptRanking(10, storeId),
          api.getHolidayAnalysis(storeId, deptId),
          api.getPromoEffectiveness(storeId, deptId),
          api.getStoreTypes(deptId)
        ])

        if (!isCancelled && requestId === latestRequestId.current) {
          setSummary(sumRes)
          setSalesTrend(trendRes || [])
          setStoreRanking(storeRankRes || [])
          setDeptRanking(deptRankRes || [])
          setHolidayAnalysis(holRes || [])
          setPromoEffectiveness(promoRes || [])
          setStoreTypes(typesRes || [])
        }
      } catch (err) {
        if (!isCancelled && requestId === latestRequestId.current) {
          console.error('Dashboard load error:', err)
          setError(err.message)
        }
      } finally {
        if (!isCancelled && requestId === latestRequestId.current) {
          setLoading(false)
        }
      }
    }

    loadDashboardData()

    return () => {
      isCancelled = true
    }
  }, [selectedStore, selectedDept, granularity])

  // Context line for filter feedback
  const storeLabel = selectedStore ? `Store ${selectedStore}` : 'All Stores'
  const deptLabel = selectedDept ? `Department ${selectedDept}` : 'All Departments'
  const viewLabel = granularity === 'monthly' ? 'Monthly View' : 'Weekly View'
  const filterContextText = `${storeLabel} · ${deptLabel} · ${viewLabel}`

  return (
    <div className="dashboard-page">
      {/* Header with Filter Controls */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2>Executive Overview</h2>
          <p style={{ color: 'var(--accent-primary)', fontWeight: 500, marginTop: '2px' }}>
            {filterContextText}
          </p>
        </div>

        {/* Global Filter Controls */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ minWidth: '150px' }}>
            <select
              value={selectedStore}
              onChange={(e) => setSelectedStore(e.target.value)}
              style={{ padding: '7px 10px', fontSize: '13px' }}
            >
              <option value="">All Stores (45)</option>
              {storesList.map((s) => (
                <option key={s.store_id} value={s.store_id}>
                  Store {s.store_id} (Type {s.store_type})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ minWidth: '160px' }}>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              style={{ padding: '7px 10px', fontSize: '13px' }}
            >
              <option value="">All Departments ({deptList.length})</option>
              {deptList.map((d) => (
                <option key={d} value={d}>
                  Department {d}
                </option>
              ))}
            </select>
          </div>

          {/* Time Granularity Selector */}
          <div style={{ display: 'flex', background: '#FFFFFF', border: '1px solid var(--border-medium)', borderRadius: '6px', padding: '2px' }}>
            <button
              style={{
                background: granularity === 'weekly' ? 'var(--accent-light)' : 'transparent',
                color: granularity === 'weekly' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                border: 'none',
                padding: '5px 12px',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
              onClick={() => setGranularity('weekly')}
            >
              Weekly
            </button>
            <button
              style={{
                background: granularity === 'monthly' ? 'var(--accent-light)' : 'transparent',
                color: granularity === 'monthly' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                border: 'none',
                padding: '5px 12px',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
              onClick={() => setGranularity('monthly')}
            >
              Monthly
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-banner" style={{ marginBottom: '16px' }}>
          <span>{error}</span>
        </div>
      )}

      {/* Row 1: Primary Filter-Aware KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Total Sales</div>
          <div className="kpi-value">
            {summary ? fmtCurrency(summary.total_revenue) : '$0'}
          </div>
          <div className="kpi-sub">
            {!selectedStore && !selectedDept && 'Historical dataset volume'}
            {selectedStore && !selectedDept && `Store ${selectedStore} volume`}
            {!selectedStore && selectedDept && `Department ${selectedDept} volume`}
            {selectedStore && selectedDept && `Store ${selectedStore} · Dept ${selectedDept}`}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Average Weekly Sales</div>
          <div className="kpi-value">
            {summary ? fmtCurrency(summary.avg_weekly_sales) : '$0'}
          </div>
          <div className="kpi-sub">Subset weekly sales baseline</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Stores</div>
          <div className="kpi-value">
            {summary ? summary.total_stores : 0}
          </div>
          <div className="kpi-sub">
            {!selectedStore && !selectedDept && 'Active in dataset'}
            {selectedStore && 'Selected store'}
            {!selectedStore && selectedDept && `Selling Dept ${selectedDept}`}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Departments</div>
          <div className="kpi-value">
            {summary ? summary.total_departments : 0}
          </div>
          <div className="kpi-sub">
            {!selectedStore && !selectedDept && 'Available departments'}
            {selectedDept && 'Selected department'}
            {selectedStore && !selectedDept && `In Store ${selectedStore}`}
          </div>
        </div>
      </div>

      {/* Row 2: Secondary Dynamic Insights */}
      <div className="kpi-grid" style={{ marginBottom: '20px' }}>
        <div className="kpi-card">
          <div className="kpi-label">
            {selectedStore ? 'Selected Store' : 'Top Store'}
          </div>
          <div className="kpi-value" style={{ fontSize: '20px' }}>
            {summary && summary.top_store_id ? `Store ${summary.top_store_id}` : '—'}
          </div>
          <div className="kpi-sub">
            {summary ? `${fmtCurrency(summary.top_store_revenue)} sales in subset` : '—'}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            {selectedDept ? 'Selected Department' : 'Top Department'}
          </div>
          <div className="kpi-value" style={{ fontSize: '20px' }}>
            {summary && summary.top_dept_id ? `Dept ${summary.top_dept_id}` : '—'}
          </div>
          <div className="kpi-sub">
            {summary ? `${fmtCurrency(summary.top_dept_revenue)} sales in subset` : '—'}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Holiday Impact</div>
          <div
            className="kpi-value"
            style={{
              color: summary && summary.holiday_lift_pct >= 0 ? 'var(--status-success)' : 'var(--status-danger)',
              fontSize: '20px'
            }}
          >
            {summary ? `${summary.holiday_lift_pct >= 0 ? '+' : ''}${summary.holiday_lift_pct}%` : '0%'}
          </div>
          <div className="kpi-sub">Holiday vs regular week lift</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Promotion Impact</div>
          <div
            className="kpi-value"
            style={{
              color: summary && summary.promotion_lift_pct >= 0 ? 'var(--accent-secondary)' : 'var(--status-danger)',
              fontSize: '20px'
            }}
          >
            {summary ? `${summary.promotion_lift_pct >= 0 ? '+' : ''}${summary.promotion_lift_pct}%` : '0%'}
          </div>
          <div className="kpi-sub">MarkDown-active week lift</div>
        </div>
      </div>

      {/* Chart 1: Time Series Sales Trend */}
      <div className="chart-card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3>Sales Trend ({granularity === 'monthly' ? 'Monthly' : 'Weekly'})</h3>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            {filterContextText}
          </span>
        </div>

        {loading ? (
          <div className="loading-container">
            <div className="spinner" />
            <div className="loading-text">Loading sales time-series...</div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={salesTrend} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ECEAE4" vertical={false} />
              <XAxis
                dataKey="period"
                stroke="#8A8882"
                tick={{ fill: '#66645F', fontSize: 11 }}
                interval={granularity === 'weekly' ? 10 : 2}
              />
              <YAxis
                stroke="#8A8882"
                tick={{ fill: '#66645F', fontSize: 11 }}
                tickFormatter={(v) => fmtCurrency(v)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="sales"
                name="Sales"
                stroke="#2F5D50"
                strokeWidth={2}
                dot={granularity === 'monthly' ? { r: 3, fill: '#2F5D50' } : false}
                activeDot={{ r: 5, fill: '#2F5D50' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Chart Row 2: Store Performance & Department Performance */}
      <div className="chart-grid">
        <div className="chart-card">
          <h3>Store Performance {selectedDept ? `(Dept ${selectedDept})` : ''}</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={storeRanking}
              layout="vertical"
              margin={{ top: 5, right: 20, left: 30, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#ECEAE4" horizontal={false} />
              <XAxis type="number" stroke="#8A8882" tickFormatter={(v) => fmtCurrency(v)} tick={{ fill: '#66645F', fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="store_id"
                stroke="#8A8882"
                tickFormatter={(id) => `Store ${id}`}
                tick={{ fill: '#66645F', fontSize: 11 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="total_sales" name="Total Sales" radius={[0, 4, 4, 0]}>
                {storeRanking.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={STORE_TYPE_COLORS[entry.store_type] || '#2F5D50'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Department Performance {selectedStore ? `(Store ${selectedStore})` : ''}</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={deptRanking}
              layout="vertical"
              margin={{ top: 5, right: 20, left: 30, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#ECEAE4" horizontal={false} />
              <XAxis type="number" stroke="#8A8882" tickFormatter={(v) => fmtCurrency(v)} tick={{ fill: '#66645F', fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="dept_id"
                stroke="#8A8882"
                tickFormatter={(id) => `Dept ${id}`}
                tick={{ fill: '#66645F', fontSize: 11 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="total_sales" name="Total Sales" fill="#5A7C71" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart Row 3: Holiday / Promotion Breakdown & Store Types */}
      <div className="chart-grid">
        <div className="chart-card">
          <h3>Holiday Impact & Promotion Effectiveness</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', height: '220px', alignItems: 'center' }}>
            <div style={{ background: 'var(--bg-card-secondary)', border: '1px solid var(--border-medium)', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.5px' }}>
                Holiday Season
              </div>
              <div
                style={{
                  fontSize: '22px',
                  fontWeight: 700,
                  color: summary && summary.holiday_lift_pct >= 0 ? 'var(--status-success)' : 'var(--status-danger)',
                  margin: '6px 0'
                }}
              >
                {summary ? `${summary.holiday_lift_pct >= 0 ? '+' : ''}${summary.holiday_lift_pct}%` : '0%'}
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {holidayAnalysis.find((h) => h.is_holiday === 1)
                  ? `Holiday: $${Number(holidayAnalysis.find((h) => h.is_holiday === 1).avg_weekly_sales).toLocaleString()}`
                  : 'Holiday: —'}
                <br />
                {holidayAnalysis.find((h) => h.is_holiday === 0)
                  ? `Regular: $${Number(holidayAnalysis.find((h) => h.is_holiday === 0).avg_weekly_sales).toLocaleString()}`
                  : 'Regular: —'}
              </p>
            </div>

            <div style={{ background: 'var(--bg-card-secondary)', border: '1px solid var(--border-medium)', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.5px' }}>
                MarkDown Promotions
              </div>
              <div
                style={{
                  fontSize: '22px',
                  fontWeight: 700,
                  color: summary && summary.promotion_lift_pct >= 0 ? 'var(--accent-primary)' : 'var(--status-danger)',
                  margin: '6px 0'
                }}
              >
                {summary ? `${summary.promotion_lift_pct >= 0 ? '+' : ''}${summary.promotion_lift_pct}%` : '0%'}
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {promoEffectiveness.find((p) => p.period === 'Promo')
                  ? `Promo: $${Number(promoEffectiveness.find((p) => p.period === 'Promo').avg_weekly_sales).toLocaleString()}`
                  : 'Promo: —'}
                <br />
                {promoEffectiveness.find((p) => p.period === 'No Promo')
                  ? `Non-Promo: $${Number(promoEffectiveness.find((p) => p.period === 'No Promo').avg_weekly_sales).toLocaleString()}`
                  : 'Non-Promo: —'}
              </p>
            </div>
          </div>
        </div>

        <div className="chart-card">
          <h3>Store Type Performance {selectedDept ? `(Dept ${selectedDept})` : ''}</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={storeTypes}
                dataKey="total_sales"
                nameKey="store_type"
                cx="50%"
                cy="50%"
                outerRadius={75}
                innerRadius={40}
                paddingAngle={3}
              >
                {storeTypes.map((entry) => (
                  <Cell key={`cell-${entry.store_type}`} fill={STORE_TYPE_COLORS[entry.store_type] || '#2F5D50'} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#DDDAD3',
                  borderRadius: '6px',
                  color: '#1C1C1C',
                  fontSize: '12px'
                }}
                formatter={(val, name) => [
                  `${fmtCurrency(val)}`,
                  `Type ${name}`
                ]}
              />
              <Legend
                formatter={(val) => <span style={{ color: '#66645F', fontSize: '12px' }}>Type {val}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
