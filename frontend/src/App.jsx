import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Forecast from './pages/Forecast'
import Assistant from './pages/Assistant'
import Insights from './pages/Insights'

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route path="/insights" element={<Insights />} />
        </Routes>
      </main>
    </div>
  )
}
