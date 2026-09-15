import { useState, useEffect } from 'react'
import { api } from '../api/client'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts'

const MODEL_META = {
  model_name: 'RetailIQ Demand Forecaster',
  version: '1.0.0',
  algorithm: 'LightGBM GBDT Regressor',
  granularity: 'Store + Department + Week',
  training_samples: 421570,
  features_count: 44,
  training_cutoff: '2012-07-27',
  validation_strategy: 'Time-Series Split (Forward Chaining / Out-of-Time Holdout)',
  holdout_evaluation: {
    RMSE: 2496.47,
    MAE: 1213.4,
    MAPE: '15.8%',
    WMAE: 1250.03
  },
  parameters: {
    n_estimators: 400,
    learning_rate: 0.04,
    num_leaves: 63,
    subsample: 0.8,
    colsample_bytree: 0.8
  },
  top_features: [
    { feature: 'dept_id', importance: 1844, desc: 'Department Category Identifier' },
    { feature: 'week_of_year', importance: 1795, desc: 'Annual Seasonality Position (1–52)' },
    { feature: 'day_of_year', importance: 1679, desc: 'Continuous Temporal Day Index' },
    { feature: 'lag_52', importance: 1599, desc: 'Prior Year Same-Week Sales' },
    { feature: 'sales_to_roll_mean_13', importance: 1388, desc: '13-Week Moving Window Ratio' },
    { feature: 'sales_to_roll_mean_4', importance: 1217, desc: '4-Week Short-Term Momentum' },
    { feature: 'lag_1', importance: 1033, desc: 'Previous Week Sales' },
    { feature: 'fuel_price', importance: 1027, desc: 'Regional Fuel Price Index' },
    { feature: 'lag_2', importance: 782, desc: '2-Week Lag Sales' },
    { feature: 'lag_13', importance: 769, desc: 'Quarterly Seasonal Lag' }
  ]
}

const FEATURE_CATEGORIES = [
  { name: 'Lag Features (1, 2, 4, 8, 13, 26, 52)', count: 7, desc: 'Captures short-term auto-regressive momentum and 52-week annual periodicity' },
  { name: 'Rolling Window Stats (Mean, Std, Min, Max 4/8/13)', count: 14, desc: 'Moving window central tendency and demand volatility' },
  { name: 'Calendar & Seasonality (Week, Month, Quarter, Day)', count: 8, desc: 'Calendar cycles, month boundaries, and holiday flags' },
  { name: 'Promotions & Markdowns (MD1-5, Total MD, Flags)', count: 7, desc: 'Promotional markdown activity and discount intensity' },
  { name: 'Macroeconomic Drivers (CPI, Fuel, Unemployment, Temp)', count: 4, desc: 'External economic climate and weather seasonality' },
  { name: 'Store Entity Embeddings (Type, Size, IDs)', count: 4, desc: 'Store physical footprint and categorical classifications' }
]

const SCHEMA_TABLES = [
  {
    name: 'fact_sales',
    type: 'Fact Table',
    rows: '421,570',
    cols: 'sales_id, store_id, dept_id, date_id, weekly_sales, returns_flag, is_holiday, markdowns, temp, fuel, cpi, unemp',
    desc: 'Core transactional grain at store_id × dept_id × date_id with weekly sales and environmental metrics.'
  },
  {
    name: 'dim_store',
    type: 'Dimension',
    rows: '45',
    cols: 'store_id, store_type (A/B/C), store_size, first_active_week, last_active_week',
    desc: 'Store master attributes, physical square footage, and active date boundaries.'
  },
  {
    name: 'dim_dept',
    type: 'Dimension',
    rows: '81',
    cols: 'dept_id',
    desc: 'Standardized department identifiers representing retail merchandise categories.'
  },
  {
    name: 'dim_date',
    type: 'Dimension',
    rows: '143',
    cols: 'date_id (YYYYMMDD), full_date, year, quarter, month, month_name, week_of_year, is_holiday_week',
    desc: 'Conformed 4-5-4 retail calendar dimension mapping weeks, quarters, and holiday events.'
  }
]

export default function Insights() {
  const [stores, setStores] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [storeFilter, setStoreFilter] = useState('ALL')

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const storesRes = await api.getStores()
        setStores(storesRes || [])
      } catch (err) {
        console.error('Failed to load insights data:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const filteredStores =
    storeFilter === 'ALL'
      ? stores
      : stores.filter((s) => s.store_type === storeFilter)

  return (
    <div className="insights-page">
      <div className="page-header">
        <h2>Data Insights & Architecture</h2>
        <p>Verified Model Metadata, 44-Feature Pipeline, Relational Star Schema, and Store Network</p>
      </div>

      {error && (
        <div className="error-banner" style={{ marginBottom: '16px' }}>
          <span>{error}</span>
        </div>
      )}

      {/* Dataset & Model Overview KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Observations</div>
          <div className="kpi-value">421,570</div>
          <div className="kpi-sub">143 Contiguous Weeks (2010–2012)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Forecaster Engine</div>
          <div className="kpi-value" style={{ fontSize: '18px' }}>LightGBM GBDT</div>
          <div className="kpi-sub">400 Trees · num_leaves=63</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Holdout WMAE</div>
          <div className="kpi-value" style={{ color: 'var(--status-success)' }}>
            ${MODEL_META.holdout_evaluation.WMAE.toLocaleString()}
          </div>
          <div className="kpi-sub">Weighted MAE on test set</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">RMSE / MAE</div>
          <div className="kpi-value" style={{ fontSize: '18px' }}>
            ${MODEL_META.holdout_evaluation.RMSE.toLocaleString()}
          </div>
          <div className="kpi-sub">MAE: ${MODEL_META.holdout_evaluation.MAE.toLocaleString()}</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Features Count</div>
          <div className="kpi-value">{MODEL_META.features_count}</div>
          <div className="kpi-sub">Engineered feature pipeline</div>
        </div>
      </div>

      {/* Feature Importance & Taxonomy */}
      <div className="chart-grid">
        <div className="chart-card">
          <h3>Feature Importance (Tree Split Gain)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={MODEL_META.top_features}
              layout="vertical"
              margin={{ top: 5, right: 20, left: 70, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#ECEAE4" horizontal={false} />
              <XAxis type="number" stroke="#8A8882" tick={{ fill: '#66645F', fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="feature"
                stroke="#8A8882"
                tick={{ fill: '#66645F', fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#DDDAD3',
                  borderRadius: '6px',
                  color: '#1C1C1C',
                  fontSize: '12px'
                }}
                formatter={(val, name, item) => [
                  `${val} splits (${item.payload.desc})`,
                  'Importance'
                ]}
              />
              <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                {MODEL_META.top_features.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index < 3 ? '#2F5D50' : index < 6 ? '#5A7C71' : '#8A9E96'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Feature Pipeline Structure (44 Features)</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
            {FEATURE_CATEGORIES.map((cat, idx) => (
              <div
                key={idx}
                style={{
                  padding: '9px 12px',
                  background: 'var(--bg-card-secondary)',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                  <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
                    {cat.name}
                  </span>
                  <span
                    className="feature-chip"
                    style={{ background: '#FFFFFF', fontSize: '11px', padding: '1px 6px' }}
                  >
                    {cat.count} features
                  </span>
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>
                  {cat.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Star Schema Data Warehouse Architecture */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '6px', fontSize: '15px', fontWeight: 600 }}>
          SQLite Star Schema Architecture (retailiq.db)
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
          Dimensional model featuring a centralized <code>fact_sales</code> fact table and 3 dimension tables, indexed on composite keys for fast aggregations.
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table className="insights-table">
            <thead>
              <tr>
                <th>Table Name</th>
                <th>Classification</th>
                <th>Row Count</th>
                <th>Schema Definition</th>
                <th>Business Description</th>
              </tr>
            </thead>
            <tbody>
              {SCHEMA_TABLES.map((table, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                    <code>{table.name}</code>
                  </td>
                  <td>
                    <span
                      className="type-badge"
                      style={{
                        background: table.type.includes('Fact') ? '#E8EFEA' : '#EDF4F2',
                        color: table.type.includes('Fact') ? '#2F5D50' : '#406E61'
                      }}
                    >
                      {table.type}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{table.rows}</td>
                  <td>
                    <code style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>{table.cols}</code>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{table.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Store Master Directory */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600 }}>
            Store Directory (45 Stores)
          </h3>
          <div style={{ display: 'flex', gap: '6px' }}>
            {['ALL', 'A', 'B', 'C'].map((type) => (
              <button
                key={type}
                className="btn-secondary"
                style={{
                  padding: '4px 10px',
                  fontSize: '12px',
                  background: storeFilter === type ? 'var(--accent-primary)' : 'var(--bg-card)',
                  color: storeFilter === type ? '#FFFFFF' : 'var(--text-secondary)',
                  borderColor: storeFilter === type ? 'var(--accent-primary)' : 'var(--border-medium)',
                  fontWeight: 600
                }}
                onClick={() => setStoreFilter(type)}
              >
                Type {type}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="loading-container">
            <div className="spinner" />
            <div className="loading-text">Loading store directory...</div>
          </div>
        ) : (
          <div style={{ maxHeight: '360px', overflowY: 'auto' }}>
            <table className="insights-table">
              <thead>
                <tr>
                  <th>Store #</th>
                  <th>Store Type</th>
                  <th>Footprint (Sq Ft)</th>
                  <th>Scale</th>
                  <th>Format Description</th>
                </tr>
              </thead>
              <tbody>
                {filteredStores.map((s) => (
                  <tr key={s.store_id}>
                    <td style={{ fontWeight: 600 }}>Store {s.store_id}</td>
                    <td>
                      <span className={`type-badge type-${(s.store_type || 'A').toLowerCase()}`}>
                        Type {s.store_type}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>
                      {Number(s.store_size || s.size || 0).toLocaleString()} sqft
                    </td>
                    <td>
                      <div style={{ width: '100px', height: '5px', background: 'var(--border-subtle)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${Math.min(100, Math.round((Number(s.store_size || s.size || 0) / 220000) * 100))}%`,
                            background:
                              s.store_type === 'A' ? '#2F5D50' : s.store_type === 'B' ? '#5A7C71' : '#8C7D68'
                          }}
                        />
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                      {s.store_type === 'A'
                        ? 'Supercenter (>150k sqft, Full Merchandise + Grocery)'
                        : s.store_type === 'B'
                        ? 'Standard Format (100k–150k sqft)'
                        : 'Small Format / Neighborhood (<100k sqft)'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
