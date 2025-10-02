import { useState, useEffect } from 'react'
import './App.css'
import Sidebar from './components/Sidebar'
import Credentials from './components/Credentials'
import Keys from './components/Keys'

function App() {
  const [activeView, setActiveView] = useState({ type: 'credentials', platform: 'netflix' })
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats')
      if (!response.ok) {
        console.warn('Stats fetch failed (likely not authenticated)')
        return
      }
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  return (
    <div className="app">
      <Sidebar 
        activeView={activeView} 
        setActiveView={setActiveView}
        stats={stats}
      />
      <div className="main-content">
        {activeView.type === 'credentials' ? (
          <Credentials platform={activeView.platform} refreshStats={fetchStats} />
        ) : (
          <Keys platform={activeView.platform} />
        )}
      </div>
    </div>
  )
}

export default App
