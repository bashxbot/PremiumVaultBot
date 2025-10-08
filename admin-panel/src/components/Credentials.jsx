import React, { useState, useEffect } from 'react'
import { MdAdd, MdUploadFile, MdEdit, MdDelete } from 'react-icons/md'
import { SiNetflix, SiCrunchyroll } from 'react-icons/si'
import { GiBoxingGlove } from 'react-icons/gi'
import { FaStar, FaTv, FaGamepad, FaXbox } from 'react-icons/fa'
import { MdSportsKabaddi } from 'react-icons/md'
import ClaimedCredentials from './ClaimedCredentials'
import './Credentials.css'
import './LoadingSpinner.css' // Import the CSS for the loading spinner

function Credentials({ platform, refreshStats }) {
  const [credentials, setCredentials] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showClaimerModal, setShowClaimerModal] = useState(false)
  const [selectedClaimer, setSelectedClaimer] = useState(null)
  const [editIndex, setEditIndex] = useState(null)
  const [formData, setFormData] = useState({ email: '', password: '', status: 'active' })
  const [uploadFile, setUploadFile] = useState(null)
  const [isLoading, setIsLoading] = useState(false) // State for loading spinner

  useEffect(() => {
    fetchCredentials()
  }, [platform])

  const fetchCredentials = async () => {
    setIsLoading(true) // Show loading spinner
    try {
      const response = await fetch(`/api/credentials/${platform}`)
      const data = await response.json()
      if (data.success) {
        setCredentials(data.credentials)
      }
    } catch (error) {
      console.error('Error fetching credentials:', error)
    } finally {
      setIsLoading(false) // Hide loading spinner
    }
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    setIsLoading(true) // Show loading spinner
    try {
      const response = await fetch(`/api/credentials/${platform}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      const data = await response.json()
      if (data.success) {
        alert(data.message)
        fetchCredentials()
        refreshStats()
        setShowModal(false)
        setFormData({ email: '', password: '', status: 'active' })
      }
    } catch (error) {
      alert('Error adding credential: ' + error.message)
    } finally {
      setIsLoading(false) // Hide loading spinner
    }
  }

  const handleEdit = async (e) => {
    e.preventDefault()
    setIsLoading(true) // Show loading spinner
    try {
      const response = await fetch(`/api/credentials/${platform}/${editIndex}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      const data = await response.json()
      if (data.success) {
        alert(data.message)
        fetchCredentials()
        refreshStats()
        setShowModal(false)
        setEditIndex(null)
        setFormData({ email: '', password: '', status: 'active' })
      }
    } catch (error) {
      alert('Error updating credential: ' + error.message)
    } finally {
      setIsLoading(false) // Hide loading spinner
    }
  }

  const handleDelete = async (credId) => {
    if (!confirm('Are you sure you want to delete this credential?')) return

    setIsLoading(true) // Show loading spinner
    try {
      const response = await fetch(`/api/credentials/${platform}/${credId}`, {
        method: 'DELETE'
      })
      const data = await response.json()
      if (data.success) {
        alert(data.message)
        fetchCredentials()
        refreshStats()
      }
    } catch (error) {
      alert('Error deleting credential: ' + error.message)
    } finally {
      setIsLoading(false) // Hide loading spinner
    }
  }

  const handleDeleteAll = async () => {
    if (!confirm(`Are you sure you want to delete ALL ${platform} credentials? This cannot be undone!`)) return

    setIsLoading(true) // Show loading spinner
    try {
      const response = await fetch(`/api/credentials/${platform}/delete-all`, {
        method: 'DELETE'
      })
      const data = await response.json()
      if (data.success) {
        alert(data.message)
        fetchCredentials()
        refreshStats()
      }
    } catch (error) {
      alert('Error deleting all credentials: ' + error.message)
    } finally {
      setIsLoading(false) // Hide loading spinner
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!uploadFile) return

    setIsLoading(true) // Show loading spinner
    const formData = new FormData()
    formData.append('file', uploadFile)

    try {
      const response = await fetch(`/api/credentials/${platform}/upload`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        alert(data.message)
        fetchCredentials()
        refreshStats()
        setShowUploadModal(false)
        setUploadFile(null)
      }
    } catch (error) {
      alert('Error uploading credentials: ' + error.message)
    } finally {
      setIsLoading(false) // Hide loading spinner
    }
  }

  const openEditModal = (credId, cred) => {
    setEditIndex(credId)
    setFormData({ email: cred.email, password: cred.password, status: cred.status })
    setShowModal(true)
  }

  const openAddModal = () => {
    setEditIndex(null)
    setFormData({ email: '', password: '', status: 'active' })
    setShowModal(true)
  }

  const openClaimerModal = (cred) => {
    setSelectedClaimer({
      name: cred.claimed_by_name || 'N/A',
      username: cred.claimed_by_username || 'N/A',
      chatId: cred.claimed_by || 'N/A',
      claimedAt: cred.claimed_at
    })
    setShowClaimerModal(true)
  }

  const formatClaimedDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const platformIcons = {
    netflix: SiNetflix,
    crunchyroll: SiCrunchyroll,
    wwe: GiBoxingGlove,
    paramountplus: FaStar,
    dazn: MdSportsKabaddi,
    molotovtv: FaTv,
    disneyplus: FaStar,
    psnfa: FaGamepad, // Assuming psnfa should use FaGamepad as per error
    xbox: FaXbox
  }

  const PlatformIcon = platformIcons[platform]

  return (
    <div className="credentials">
      <div className="header">
        <h1><PlatformIcon className="title-icon" /> {platform.charAt(0).toUpperCase() + platform.slice(1)} Credentials</h1>
        <div className="header-actions">
          <button className="btn btn-success" onClick={openAddModal}><MdAdd /> Add Credential</button>
          <button className="btn btn-primary" onClick={() => setShowUploadModal(true)}><MdUploadFile /> Upload from File</button>
          <button className="btn btn-danger" onClick={handleDeleteAll}><MdDelete /> Delete All</button>
        </div>
      </div>

      {isLoading && (
        <div className="loading-wrapper">
          <div className="spinner"></div>
        </div>
      )}

      {!isLoading && credentials.length === 0 && (
        <div className="no-credentials-message">
          No credentials found. Add some to get started!
        </div>
      )}

      {!isLoading && credentials.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Email</th>
              <th>Password</th>
              <th>Status</th>
              <th>Created At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {credentials.map((cred, index) => (
              <tr key={cred.id}>
                <td>{index + 1}</td>
                <td>{cred.email}</td>
                <td>{cred.password}</td>
                <td>
                  <span className={`badge badge-${cred.status}`}>{cred.status}</span>
                </td>
                <td>{cred.created_at ? cred.created_at.slice(0, 19) : 'N/A'}</td>
                <td>
                  {cred.status === 'claimed' && (
                    <button className="btn btn-sm btn-info" onClick={() => openClaimerModal(cred)} title="View Claimer Details">
                      <MdAdd style={{ transform: 'rotate(45deg)' }} />
                    </button>
                  )}
                  <button className="btn btn-sm btn-warning" onClick={() => openEditModal(cred.id, cred)}><MdEdit /></button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(cred.id)}><MdDelete /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}


      {showModal && (
        <div className="modal" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <span className="close" onClick={() => setShowModal(false)}>&times;</span>
            <h2>{editIndex !== null ? 'Edit Credential' : 'Add New Credential'}</h2>
            <form onSubmit={editIndex !== null ? handleEdit : handleAdd}>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="text"
                  value={formData.password}
                  onChange={e => setFormData({ ...formData, password: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={formData.status}
                  onChange={e => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="claimed">Claimed</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary">
                {editIndex !== null ? 'Update' : 'Add'} Credential
              </button>
            </form>
          </div>
        </div>
      )}

      {showUploadModal && (
        <div className="modal" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <span className="close" onClick={() => setShowUploadModal(false)}>&times;</span>
            <h2>Upload Credentials from File</h2>
            <p className="upload-info">Upload a .txt file with credentials in format:<br />
              <code>email@email.com:password123</code><br />
              <small>Extra data after password (e.g., | info) will be ignored. All credentials set as active.</small>
            </p>
            <form onSubmit={handleUpload}>
              <div className="form-group">
                <label>Select File</label>
                <input
                  type="file"
                  accept=".txt"
                  onChange={e => setUploadFile(e.target.files[0])}
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary">Upload</button>
            </form>
          </div>
        </div>
      )}

      {showClaimerModal && selectedClaimer && (
        <div className="modal" onClick={() => setShowClaimerModal(false)}>
          <div className="modal-content claimer-modal" onClick={e => e.stopPropagation()}>
            <span className="close" onClick={() => setShowClaimerModal(false)}>&times;</span>
            <h2>📋 Claimer Details</h2>
            <div className="claimer-details">
              <div className="detail-row">
                <span className="detail-label">👤 Full Name:</span>
                <span className="detail-value">{selectedClaimer.name}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">🔖 Username:</span>
                <span className="detail-value">@{selectedClaimer.username}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">💬 Chat ID:</span>
                <span className="detail-value"><code>{selectedClaimer.chatId}</code></span>
              </div>
              <div className="detail-row">
                <span className="detail-label">🕒 Claimed At:</span>
                <span className="detail-value">{formatClaimedDate(selectedClaimer.claimedAt)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <ClaimedCredentials platform={platform} />
    </div>
  )
}

export default Credentials