import React, { useState } from 'react'
import './Sidebar.css'

const platformEmoji = {
  netflix: '🎬',
  crunchyroll: '🍜',
  spotify: '🎵',
  wwe: '🤼'
}

function Sidebar({ activeView, setActiveView, stats }) {
  const [expandedSection, setExpandedSection] = useState('credentials')

  const platforms = ['netflix', 'crunchyroll', 'spotify', 'wwe']

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>🎮 Admin Panel</h2>
      </div>

      <div className="sidebar-section">
        <div 
          className={`section-header ${expandedSection === 'credentials' ? 'active' : ''}`}
          onClick={() => toggleSection('credentials')}
        >
          <span>📋 Credentials</span>
          <span className="arrow">{expandedSection === 'credentials' ? '▼' : '▶'}</span>
        </div>
        {expandedSection === 'credentials' && (
          <div className="section-items">
            {platforms.map(platform => (
              <div
                key={platform}
                className={`section-item ${activeView.type === 'credentials' && activeView.platform === platform ? 'active' : ''}`}
                onClick={() => setActiveView({ type: 'credentials', platform })}
              >
                <span>{platformEmoji[platform]} {platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                {stats && stats.stats[platform] && (
                  <span className="count">{stats.stats[platform].active}/{stats.stats[platform].total}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="sidebar-section">
        <div 
          className={`section-header ${expandedSection === 'keys' ? 'active' : ''}`}
          onClick={() => toggleSection('keys')}
        >
          <span>🔑 Keys</span>
          <span className="arrow">{expandedSection === 'keys' ? '▼' : '▶'}</span>
        </div>
        {expandedSection === 'keys' && (
          <div className="section-items">
            {platforms.map(platform => (
              <div
                key={platform}
                className={`section-item ${activeView.type === 'keys' && activeView.platform === platform ? 'active' : ''}`}
                onClick={() => setActiveView({ type: 'keys', platform })}
              >
                <span>{platformEmoji[platform]} {platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar
