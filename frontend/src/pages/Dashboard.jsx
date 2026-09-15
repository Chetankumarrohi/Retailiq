import { useState, useEffect } from 'react'
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
  
  // Filters
  const [storesList, setStoresList] = useState([])
  const [deptList, setDeptList] = useState([])
  const [selectedStore, setSelectedStore] = useState('')
  const [selectedDept, setSelectedDept] = useState('')
  const [granularity, setGranularity] = useState('monthly')
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Initial metadata load
  useEffect(() => {
    async function loadMetadata() {
      try {
        const stores = await api.getStores()
        setStoresList(stores || [])
        const depts = await api.getDepartments()
        setDeptList(depts || [])
      } catch (err) {
        console.error('Failed to load metadata:', err)
      }
    }
    loadMetadata()
  }, [])

  // Update departments when store filter changes
  useEffect(() => {
    async function updateDepts() {
      try {
        const depts = await api.getDepartments(selectedStore ? Number(selectedStore) : null)
        setDeptList(depts || [])
      } catch (err) {
        console.error('Failed to update depts:', err)
      }
    }
    updateDepts()
  }, [selectedStore])

  // Load dashboard analytics
  useEffect(() => {
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
          api.getSummary(),
          api.getSalesTrend({ granularity, store_id: storeId, dept_id: deptId }),
          api.getStoreRanking(10),
          api.getDeptRanking(10, storeId),
          api.getHolidayAnalysis(storeId),
          api.getPromoEffectiveness(storeId),
          api.getStoreTypes()
        ])

        setSummary(sumRes)
        setSalesTrend(trendRes || [])
        setStoreRanking(storeRankRes || [])
        setDeptRanking(deptRankRes || [])
        setHolidayAnalysis(holRes || [])
        setPromoEffectiveness(promoRes || [])
        setStoreTypes(typesRes || [])
      } catch (err) {
        console.error('Dashboard load error:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadDashboardData()
  }, [selectedStore, selectedDept, granularity])

  return (
    <div className="dashboard-page">
      {/* Header with Filter Controls */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2>Executive Overview</h2>
          <p>Multi-Store Retail Demand Intelligence & Chain Performance</p>
        </div>

        {/* Filters */}
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

          <div className="form-group" style={{ minWidth: '150px' }}>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              style={{ padding: '7px 10px', fontSize: '13px' }}
            >
              <option value="">All Departments (81)</option>
              {deptList.map((d) => (
                <option key={d} value={d}>
                  Department {d}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', background: '#FFFFFF', border: '1px solid var(--border-medium)', borderRadius: '6px', padding: '2px' }}>
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
          </div>
        </div>
      </div>

      {error && (
        <div className="error-banner" style={{ marginBottom: '16px' }}>
          <span>{error}</span>
        </div>
      )}

      {/* Row 1: Primary KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Total Sales</div>
          <div className="kpi-value">
            {summary ? fmtCurrency(summary.total_revenue || 6737218987.11) : '$6.74B'}
          </div>
          <div className="kpi-sub">Historical dataset volume</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Average Weekly Sales</div>
          <div className="kpi-value">
            {summary ? fmtCurrency(summary.avg_weekly_sales || 15981.26) : '$15,981'}
          </div>
          <div className="kpi-sub">Per store-department week</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Stores</div>
          <div className="kpi-value">
            {summary ? summary.total_stores : 45}
          </div>
          <div className="kpi-sub">Type A (22), B (17), C (6)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Departments</div>
          <div className="kpi-value">
            {summary ? summary.total_departments : 81}
          </div>
          <div className="kpi-sub">Merchandise categories</div>
        </div>
      </div>

      {/* Row 2: Secondary Business Insights */}
      <div className="kpi-grid" style={{ marginBottom: '20px' }}>
        <div className="kpi-card">
          <div className="kpi-label">Top Store</div>
          <div className="kpi-value" style={{ fontSize: '20px' }}>
            Store 20
          </div>
          <div className="kpi-sub">$301.4M lifetime volume</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Top Department</div>
          <div className="kpi-value" style={{ fontSize: '20px' }}>
            Department 92
          </div>
          <div className="kpi-sub">$483.9M lifetime volume</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Holiday Impact</div>
          <div className="kpi-value" style={{ color: 'var(--status-success)' }}>
            +7.13%
          </div>
          <div className="kpi-sub">$17,036 vs $15,901 baseline</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Promotion Impact</div>
          <div className="kpi-value" style={{ color: 'var(--accent-secondary)' }}>
            +1.92%
          </div>
          <div className="kpi-sub">Active markdown weeks</div>
        </div>
      </div>

      {/* Chart 1: Sales Trend */}
      <div className="chart-card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3>Weekly Sales Trend</h3>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            {selectedStore ? `Store ${selectedStore}` : 'Chain Total'} {selectedDept ? `· Dept ${selectedDept}` : ''}
          </span>
        </div>

        {loading ? (
          <div className="loading-container">
            <div className="spinner" />
            <div className="loading-text">Loading sales data...</div>
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
                name="Weekly Sales"
                stroke="#2F5D50"
                strokeWidth={2}
                dot={granularity === 'monthly' ? { r: 3, fill: '#2F5D50' } : false}
                activeDot={{ r: 5, fill: '#2F5D50' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Chart Row 2: Store & Dept Performance */}
      <div className="chart-grid">
        <div className="chart-card">
          <h3>Store Performance</h3>
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
          <h3>Department Performance</h3>
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

      {/* Chart Row 3: Holiday / Promotion Comparison & Store Types */}
      <div className="chart-grid">
        <div className="chart-card">
          <h3>Holiday Impact & Promotion Effectiveness</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', height: '220px', alignItems: 'center' }}>
            <div style={{ background: 'var(--bg-card-secondary)', border: '1px solid var(--border-medium)', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.5px' }}>
                Holiday Season
              </div>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--status-success)', margin: '6px 0' }}>
                +7.13%
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Holiday Avg: <strong>$17,036</strong><br />
                Normal Avg: <strong>$15,901</strong>
              </p>
            </div>

            <div style={{ background: 'var(--bg-card-secondary)', border: '1px solid var(--border-medium)', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.5px' }}>
                MarkDown Promotions
              </div>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--accent-primary)', margin: '6px 0' }}>
                +1.92%
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Promo Avg: <strong>$16,177</strong><br />
                Non-Promo: <strong>$15,872</strong>
              </p>
            </div>
          </div>
        </div>

        <div className="chart-card">
          <h3>Store Type Performance</h3>
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
                  `${fmtCurrency(val)} (${((val / 6737218987.11) * 100).toFixed(1)}%)`,
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
