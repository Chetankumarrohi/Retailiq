import { NavLink } from 'react-router-dom'

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>RetailIQ</h1>
        <p>Demand Intelligence</p>
      </div>
      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
          <span className="nav-icon">📊</span>
          Dashboard
        </NavLink>
        <NavLink to="/forecast" className={({ isActive }) => (isActive ? 'active' : '')}>
          <span className="nav-icon">📈</span>
          Forecast Explorer
        </NavLink>
        <NavLink to="/assistant" className={({ isActive }) => (isActive ? 'active' : '')}>
          <span className="nav-icon">💬</span>
          Business Assistant
        </NavLink>
        <NavLink to="/insights" className={({ isActive }) => (isActive ? 'active' : '')}>
          <span className="nav-icon">📑</span>
          Data Insights
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className="status-dot"></span>
          <span>System Online · v1.0.0</span>
        </div>
      </div>
    </aside>
  )
}
