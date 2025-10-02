import React, { useState, useEffect } from 'react'
import { MdSettings, MdSave, MdPerson, MdLock, MdTelegram } from 'react-icons/md'
import './Settings.css'

function Settings({ userRole, username }) {
  const [formData, setFormData] = useState({ currentPassword: '', newUsername: '', newPassword: '', confirmPassword: '', telegramUserId: '' })
  const [currentTelegramId, setCurrentTelegramId] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchTelegramId()
  }, [])

  const fetchTelegramId = async () => {
    try {
      const response = await fetch('/api/telegram-id')
      const data = await response.json()
      if (data.success && data.telegram_user_id) {
        setCurrentTelegramId(data.telegram_user_id)
      }
    } catch (error) {
      console.error('Error fetching telegram ID:', error)
    }
  }

  const handleChangeTelegramId = async (e) => {
    e.preventDefault()
    setMessage('')
    setError('')

    try {
      const response = await fetch('/api/telegram-id', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegramUserId: formData.telegramUserId
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setMessage('Telegram User ID updated successfully. You can now use the bot as an admin.')
        setCurrentTelegramId(formData.telegramUserId)
        setFormData({ ...formData, telegramUserId: '' })
      } else {
        setError(data.message || 'Failed to update Telegram User ID')
      }
    } catch (error) {
      setError('Connection error. Please try again.')
    }
  }

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
          <h2><MdTelegram /> Telegram Bot Admin Access</h2>
          <p className="section-description">
            Current Telegram User ID: <strong>{currentTelegramId || 'Not set'}</strong>
          </p>
          <p className="section-description">
            Set your Telegram User ID to get admin access in the bot. You can find your ID by messaging <a href="https://t.me/userinfobot" target="_blank" rel="noopener noreferrer">@userinfobot</a> on Telegram.
          </p>
          <form onSubmit={handleChangeTelegramId}>
            <div className="form-group">
              <label>Telegram User ID</label>
              <input
                type="text"
                value={formData.telegramUserId}
                onChange={(e) => setFormData({ ...formData, telegramUserId: e.target.value })}
                required
                placeholder="Enter your Telegram User ID (e.g., 123456789)"
              />
            </div>
            <button type="submit" className="btn btn-primary"><MdSave /> Save Telegram ID</button>
          </form>
        </div>

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
