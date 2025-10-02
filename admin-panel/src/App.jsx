
import { useState, useEffect } from 'react'
import './App.css'
import Sidebar from './components/Sidebar'
import Credentials from './components/Credentials'
import Keys from './components/Keys'
import Login from './components/Login'

function App() {
  const [activeView, setActiveView] = useState({ type: 'credentials', platform: 'netflix' })
  const [stats, setStats] = useState(null)
  const [authenticated, setAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [currentPlatform, setCurrentPlatform] = useState(null)
  const [platforms, setPlatforms] = useState([])
  const [totalKeys, setTotalKeys] = useState(0)
  const [activeKeys, setActiveKeys] = useState(0)
  const [userRole, setUserRole] = useState(null)
  const [username, setUsername] = useState(null)

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/check-auth')
      const data = await response.json()
      setAuthenticated(data.authenticated)
      if (data.authenticated) {
        setUserRole(data.role)
        setUsername(data.username)
        if (data.platform) {
          setCurrentPlatform(data.platform)
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setAuthenticated(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  useEffect(() => {
    if (authenticated) {
      fetchStats()
    } else {
      setStats({})
      setPlatforms([])
    }
  }, [authenticated, currentPlatform])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats')
      const data = await response.json()
      if (data.success) {
        setStats(data.stats || {})
        setPlatforms(data.platforms || [])
        setTotalKeys(data.total_keys || 0)
        setActiveKeys(data.active_keys || 0)
      } else {
        console.error('Stats fetch failed:', data.message)
      }
    } catch (error) {
      console.error('Stats fetch failed:', error)
      setStats({})
      setPlatforms([])
    }
  }

  const handleLogin = (role, user) => {
    setUserRole(role)
    setUsername(user)
    setAuthenticated(true)
  }

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', { method: 'POST' })
      setAuthenticated(false)
      setUserRole(null)
      setUsername(null)
      setStats({})
      setPlatforms([])
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  if (loading) {
    return (
      <div className="app" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    )
  }

  if (!authenticated) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className="app">
      <Sidebar 
        activeView={activeView} 
        setActiveView={setActiveView}
        stats={stats}
        platforms={platforms}
        totalKeys={totalKeys}
        activeKeys={activeKeys}
        authenticated={authenticated}
        userRole={userRole}
        username={username}
        onLogout={handleLogout}
      />
      <div className="main-content">
        {activeView.type === 'credentials' ? (
          <Credentials platform={activeView.platform} refreshStats={fetchStats} authenticated={authenticated} />
        ) : (
          <Keys platform={activeView.platform} authenticated={authenticated} />
        )}
      </div>
    </div>
  )
}

export default App
