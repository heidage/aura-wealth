import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import ClientDashboard from './pages/ClientDashboard'
import AdvisorDashboard from './pages/AdvisorDashboard'

export interface User {
  id: string
  email: string
  name: string
  role: 'client' | 'advisor'
}

export default function App() {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem('user')
    if (stored) setUser(JSON.parse(stored))
  }, [])

  const handleLogin = (u: User, token: string) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(u))
    setUser(u)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={user ? <Navigate to="/" /> : <LoginPage onLogin={handleLogin} />}
        />
        <Route
          path="/"
          element={
            !user ? (
              <Navigate to="/login" />
            ) : user.role === 'advisor' ? (
              <AdvisorDashboard user={user} onLogout={handleLogout} />
            ) : (
              <ClientDashboard user={user} onLogout={handleLogout} />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
