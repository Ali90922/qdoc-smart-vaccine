/* ==========================================
 * File: frontend/src/App.jsx
 *     /\
 *    / K2\
 *   /______\
 *  ~~~~~~~~~~
 *   8,611m
 * ========================================== */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import Profile from './pages/Profile'
import Dashboard from './pages/Dashboard'
import Schedule from './pages/Schedule'
import Encyclopedia from './pages/Encyclopedia'

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"          element={<Landing />} />
        <Route path="/profile"   element={<PrivateRoute><Profile /></PrivateRoute>} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/schedule"  element={<PrivateRoute><Schedule /></PrivateRoute>} />
        <Route path="/encyclopedia" element={<PrivateRoute><Encyclopedia /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  )
}
