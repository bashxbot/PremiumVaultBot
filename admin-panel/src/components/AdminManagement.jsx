import React, { useState, useEffect } from 'react'
import { MdPeople, MdAdd, MdDelete } from 'react-icons/md'
import './AdminManagement.css'

function AdminManagement() {
  const [admins, setAdmins] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({ username: '', password: '' })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchAdmins()
  }, [])

  const fetchAdmins = async () => {
    try {
      const response = await fetch('/api/admins')
      const data = await response.json()
      if (data.success) {
        setAdmins(data.admins)
      }
    } catch (error) {
      console.error('Error fetching admins:', error)
    }
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    setMessage('')
    setError('')

    try {
      const response = await fetch('/api/admins', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      const data = await response.json()
      
      if (data.success) {
        setMessage(data.message)
        fetchAdmins()
        setShowModal(false)
        setFormData({ username: '', password: '' })
      } else {
        setError(data.message)
      }
    } catch (error) {
      setError('Connection error. Please try again.')
    }
  }

  const handleDelete = async (username) => {
    if (!confirm(`Are you sure you want to delete admin "${username}"?`)) return

    try {
      const response = await fetch(`/api/admins/${username}`, {
        method: 'DELETE'
      })
      
      const data = await response.json()
      
      if (data.success) {
        setMessage(data.message)
        fetchAdmins()
      } else {
        setError(data.message)
      }
    } catch (error) {
      setError('Connection error. Please try again.')
    }
  }

  return (
    <div className="admin-management">
      <div className="header">
        <h1><MdPeople className="title-icon" /> Admin Management</h1>
        <button className="btn btn-success" onClick={() => setShowModal(true)}>
          <MdAdd /> Add Admin
        </button>
      </div>

      {message && <div className="success-message">{message}</div>}
      {error && <div className="error-message">{error}</div>}

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Username</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {admins.map((admin, index) => (
            <tr key={index}>
              <td>{index + 1}</td>
              <td>{admin.username}</td>
              <td><span className="badge badge-active">Admin</span></td>
              <td>
                <button 
                  className="btn btn-sm btn-danger" 
                  onClick={() => handleDelete(admin.username)}
                >
                  <MdDelete /> Delete
                </button>
              </td>
            </tr>
          ))}
          {admins.length === 0 && (
            <tr>
              <td colSpan="4" style={{ textAlign: 'center', color: '#999' }}>
                No admins found. Add an admin to get started.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {showModal && (
        <div className="modal">
          <div className="modal-content">
            <span className="close" onClick={() => setShowModal(false)}>&times;</span>
            <h2>Add New Admin</h2>
            <form onSubmit={handleAdd}>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                  placeholder="Enter username"
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  placeholder="Enter password"
                />
              </div>
              <button type="submit" className="btn btn-primary">Add Admin</button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminManagement
