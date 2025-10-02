import { useState, useEffect } from 'react'
import './App.css'
import Sidebar from './components/Sidebar'
import Credentials from './components/Credentials'
import Keys from './components/Keys'

function App() {
  const [activeView, setActiveView] = useState({ type: 'credentials', platform: 'netflix' })
  const [stats, setStats] = useState(null)
  const [authenticated, setAuthenticated] = useState(false);
  const [currentPlatform, setCurrentPlatform] = useState(null);
  const [platforms, setPlatforms] = useState([]);
  const [totalKeys, setTotalKeys] = useState(0);
  const [activeKeys, setActiveKeys] = useState(0);


  const checkAuth = async () => {
    try {
      const response = await fetch('/api/check-auth');
      const data = await response.json();
      setAuthenticated(data.authenticated);
      if (data.authenticated && data.platform) {
        setCurrentPlatform(data.platform);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setAuthenticated(false);
    }
  };

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
      console.error('Stats fetch failed (likely not authenticated)')
      setStats({})
      setPlatforms([])
    }
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