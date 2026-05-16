import { Routes, Route, NavLink } from 'react-router-dom'
import Overview from './pages/Overview'
import Teams from './pages/Teams'
import Goalies from './pages/Goalies'
import Research from './pages/Research'

function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        <NavLink to="/" className="logo">
          KOPITAR <span>NHL Fatigue Research</span>
        </NavLink>
        <nav className="nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
          >
            Overview
          </NavLink>
          <NavLink
            to="/teams"
            className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
          >
            Teams
          </NavLink>
          <NavLink
            to="/goalies"
            className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
          >
            Goalies
          </NavLink>
          <NavLink
            to="/research"
            className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
          >
            Research
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <div className="app">
      <Header />
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/teams" element={<Teams />} />
        <Route path="/goalies" element={<Goalies />} />
        <Route path="/research" element={<Research />} />
      </Routes>
    </div>
  )
}
