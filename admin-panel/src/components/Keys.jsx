import React, { useState, useEffect } from 'react'
import { MdBarChart, MdDelete } from 'react-icons/md'
import { SiNetflix, SiCrunchyroll } from 'react-icons/si'
import { GiBoxingGlove } from 'react-icons/gi'
import { FaStar, FaTv, FaGamepad, FaXbox } from 'react-icons/fa'
import { MdSportsKabaddi } from 'react-icons/md'
import './Keys.css'

function Keys({ platform }) {
  const [keys, setKeys] = useState([])

  useEffect(() => {
    fetchKeys()
  }, [platform])

  const fetchKeys = async () => {
    try {
      const response = await fetch(`/api/keys/${platform}`)
      const data = await response.json()
      if (data.success) {
        setKeys(data.keys)
      }
    } catch (error) {
      console.error('Error fetching keys:', error)
    }
  }

  const platformIcons = {
    netflix: SiNetflix,
    crunchyroll: SiCrunchyroll,
    wwe: GiBoxingGlove,
    paramountplus: FaStar,
    dazn: MdSportsKabaddi,
    molotovtv: FaTv,
    disneyplus: FaStar,
    psnfa: FaGamepad,
    xbox: FaXbox
  }

  const PlatformIcon = platformIcons[platform]

  const stats = {
    total: keys.length,
    active: keys.filter(k => k.status === 'active').length,
    expired: keys.filter(k => k.status === 'expired').length,
    used: keys.filter(k => k.status === 'used').length
  }

  const handleDeleteAll = async () => {
    if (!confirm(`Are you sure you want to delete ALL ${platform} keys? This cannot be undone!`)) return
    
    try {
      const response = await fetch(`/api/keys/${platform}/delete-all`, {
        method: 'DELETE'
      })
      const data = await response.json()
      if (data.success) {
        alert(data.message)
        fetchKeys()
      }
    } catch (error) {
      alert('Error deleting all keys: ' + error.message)
    }
  }

  return (
    <div className="keys">
      <div className="header">
        <h1><PlatformIcon className="title-icon" /> {platform.charAt(0).toUpperCase() + platform.slice(1)} Keys</h1>
        <button className="btn btn-danger" onClick={handleDeleteAll}><MdDelete /> Delete All Keys</button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Keys</h3>
          <div className="number">{stats.total}</div>
        </div>
        <div className="stat-card">
          <h3>Active Keys</h3>
          <div className="number">{stats.active}</div>
        </div>
        <div className="stat-card">
          <h3>Expired Keys</h3>
          <div className="number">{stats.expired}</div>
        </div>
        <div className="stat-card">
          <h3>Fully Used</h3>
          <div className="number">{stats.used}</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Key Code</th>
            <th>Status</th>
            <th>Remaining Uses</th>
            <th>Created At</th>
            <th>Expires At</th>
            <th>Used By</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key, index) => (
            <tr key={key.id || index}>
              <td>{index + 1}</td>
              <td><code className="key-code">{key.key_code || key.key}</code></td>
              <td>
                <span className={`badge badge-${key.status}`}>{key.status}</span>
              </td>
              <td>{key.remaining_uses} / {key.uses}</td>
              <td>{key.created_at ? key.created_at.slice(0, 19) : 'N/A'}</td>
              <td>{key.redeemed_at ? key.redeemed_at.slice(0, 19) : 'Never'}</td>
              <td>
                {key.giveaway_winner ? (
                  <span>Giveaway winner: {key.giveaway_winner}</span>
                ) : (
                  <span style={{ color: '#999' }}>Not used yet</span>
                )}
              </td>
            </tr>
          ))}
          {keys.length === 0 && (
            <tr>
              <td colSpan="7" style={{ textAlign: 'center', color: '#999' }}>
                No keys found. Generate keys from the Telegram bot admin panel.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default Keys
