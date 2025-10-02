import React, { useState } from 'react'
import { MdSettings, MdSave, MdPerson, MdLock } from 'react-icons/md'
import './Settings.css'

function Settings({ userRole, username }) {
  const [formData, setFormData] = useState({ currentPassword: '', newUsername: '', newPassword: '', confirmPassword: '' })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setMessage('')
    setError('')

    if (formData.newPassword !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    try {
      const response = await fetch('/api/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          currentPassword: formData.currentPassword,
          newPassword: formData.newPassword
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setMessage('Password changed successfully')
        setFormData({ currentPassword: '', newUsername: '', newPassword: '', confirmPassword: '' })
      } else {
        setError(data.message || 'Failed to change password')
      }
    } catch (error) {
      setError('Connection error. Please try again.')
    }
  }

  const handleChangeUsername = async (e) => {
    e.preventDefault()
    setMessage('')
    setError('')

    try {
      const response = await fetch('/api/change-username', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          newUsername: formData.newUsername
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setMessage('Username changed successfully. Please log in again.')
        setTimeout(() => window.location.reload(), 2000)
      } else {
        setError(data.message || 'Failed to change username')
      }
    } catch (error) {
      setError('Connection error. Please try again.')
    }
  }

  return (
    <div className="settings">
      <div className="header">
        <h1><MdSettings className="title-icon" /> Settings</h1>
      </div>

      <div className="settings-content">
        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}

        <div className="settings-section">
          <h2><MdPerson /> Change Username</h2>
          <p className="section-description">Current username: <strong>{username}</strong></p>
          <form onSubmit={handleChangeUsername}>
            <div className="form-group">
              <label>New Username</label>
              <input
                type="text"
                value={formData.newUsername}
                onChange={(e) => setFormData({ ...formData, newUsername: e.target.value })}
                required
                placeholder="Enter new username"
              />
            </div>
            <button type="submit" className="btn btn-primary"><MdSave /> Save Username</button>
          </form>
        </div>

        <div className="settings-section">
          <h2><MdLock /> Change Password</h2>
          <form onSubmit={handleChangePassword}>
            <div className="form-group">
              <label>Current Password</label>
              <input
                type="password"
                value={formData.currentPassword}
                onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
                required
                placeholder="Enter current password"
              />
            </div>
            <div className="form-group">
              <label>New Password</label>
              <input
                type="password"
                value={formData.newPassword}
                onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                required
                placeholder="Enter new password"
              />
            </div>
            <div className="form-group">
              <label>Confirm New Password</label>
              <input
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                required
                placeholder="Confirm new password"
              />
            </div>
            <button type="submit" className="btn btn-primary"><MdSave /> Save Password</button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Settings
