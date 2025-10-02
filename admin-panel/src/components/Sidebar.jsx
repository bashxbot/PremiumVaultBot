import React, { useState } from 'react'
import { MdDashboard, MdCreditCard, MdVpnKey, MdChevronRight, MdExpandMore } from 'react-icons/md'
import { SiNetflix, SiCrunchyroll, SiSpotify } from 'react-icons/si'
import { GiBoxingGlove } from 'react-icons/gi'
import './Sidebar.css'

const platformIcons = {
  netflix: SiNetflix,
  crunchyroll: SiCrunchyroll,
  spotify: SiSpotify,
  wwe: GiBoxingGlove
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
        <h2><MdDashboard className="header-icon" /> Admin Panel</h2>
      </div>

      <div className="sidebar-section">
        <div 
          className={`section-header ${expandedSection === 'credentials' ? 'active' : ''}`}
          onClick={() => toggleSection('credentials')}
        >
          <span><MdCreditCard className="section-icon" /> Credentials</span>
          <span className="arrow">{expandedSection === 'credentials' ? <MdExpandMore /> : <MdChevronRight />}</span>
        </div>
        {expandedSection === 'credentials' && (
          <div className="section-items">
            {platforms.map(platform => {
              const PlatformIcon = platformIcons[platform]
              return (
                <div
                  key={platform}
                  className={`section-item ${activeView.type === 'credentials' && activeView.platform === platform ? 'active' : ''}`}
                  onClick={() => setActiveView({ type: 'credentials', platform })}
                >
                  <span><PlatformIcon className="platform-icon" /> {platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                  {stats && stats.stats && stats.stats[platform] && (
                    <span className="count">{stats.stats[platform].active}/{stats.stats[platform].total}</span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div className="sidebar-section">
        <div 
          className={`section-header ${expandedSection === 'keys' ? 'active' : ''}`}
          onClick={() => toggleSection('keys')}
        >
          <span><MdVpnKey className="section-icon" /> Keys</span>
          <span className="arrow">{expandedSection === 'keys' ? <MdExpandMore /> : <MdChevronRight />}</span>
        </div>
        {expandedSection === 'keys' && (
          <div className="section-items">
            {platforms.map(platform => {
              const PlatformIcon = platformIcons[platform]
              return (
                <div
                  key={platform}
                  className={`section-item ${activeView.type === 'keys' && activeView.platform === platform ? 'active' : ''}`}
                  onClick={() => setActiveView({ type: 'keys', platform })}
                >
                  <span><PlatformIcon className="platform-icon" /> {platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar
