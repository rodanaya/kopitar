import { Routes, Route, NavLink } from 'react-router-dom'
import Overview from './pages/Overview'
import Teams from './pages/Teams'
import Goalies from './pages/Goalies'
import Players from './pages/Players'
import Fatigue from './pages/Fatigue'
import Compare from './pages/Compare'
import Research from './pages/Research'

function Header() {
  const link = (to: string, label: string, end?: boolean) => (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
    >
      {label}
    </NavLink>
  )

  return (
    <header className="header">
      <div className="header-inner">
        <NavLink to="/" className="logo">
          KOPITAR <span>NHL Fatigue Lab</span>
        </NavLink>
        <nav className="nav">
          {link('/', 'Overview', true)}
          {link('/teams', 'Teams')}
          {link('/goalies', 'Goalies')}
          {link('/players', 'Players')}
          {link('/fatigue', 'Fatigue')}
          {link('/compare', 'Compare')}
          {link('/research', 'Research')}
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
        <Route path="/players" element={<Players />} />
        <Route path="/fatigue" element={<Fatigue />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/research" element={<Research />} />
      </Routes>
    </div>
  )
}
