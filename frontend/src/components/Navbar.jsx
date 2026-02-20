/* ==========================================
 * File: frontend/src/components/Navbar.jsx
 *     /\
 *    / K2\
 *   /______\
 *  ~~~~~~~~~~
 *   8,611m
 * ========================================== */

import { Link, useNavigate, useLocation } from 'react-router-dom'
import './Navbar.css'
import qdocLogo from '../assets/qdoc-logo.png'

export default function Navbar() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const active    = (path) => location.pathname === path ? 'active' : ''

  const logout = () => {
    localStorage.removeItem('token')
    navigate('/')
  }

  return (
    <nav className="navbar">
      <Link to="/dashboard" className="navbar-brand">
        <img src={qdocLogo} alt="QDoc" className="navbar-logo" />
        <span className="navbar-brand-text">Vaccine Portal</span>
      </Link>
      <div className="navbar-links">
        <Link to="/dashboard" className={`nav-link ${active('/dashboard')}`}>Dashboard</Link>
        <Link to="/schedule"  className={`nav-link ${active('/schedule')}`}>Schedule</Link>
      </div>
      <button className="btn btn-outline btn-sm" onClick={logout}>Sign Out</button>
    </nav>
  )
}
