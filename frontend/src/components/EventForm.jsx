import { useState } from 'react'
import axios from 'axios'
import './EventForm.css'

const API_URL = 'http://localhost:8000/api'

function EventForm({ token, onEventCreated, onCancel }) {
  const [nombre, setNombre] = useState('')
  const [fechaHora, setFechaHora] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await axios.post(
        `${API_URL}/events`,
        {
          nombre,
          fecha_hora: fechaHora
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      onEventCreated()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al crear el evento')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="event-form-container">
      <div className="event-form-card">
        <div className="form-header">
          <h2>Crear Nuevo Evento</h2>
          <p>Completa los datos del evento</p>
        </div>

        <form onSubmit={handleSubmit} className="event-form">
          <div className="form-group">
            <label htmlFor="nombre">Nombre del Evento *</label>
            <input
              id="nombre"
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej: Conferencia de Tecnología 2024"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="fechaHora">Fecha y Hora de Inicio *</label>
            <input
              id="fechaHora"
              type="datetime-local"
              value={fechaHora}
              onChange={(e) => setFechaHora(e.target.value)}
              required
            />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-actions">
            <button
              type="button"
              onClick={onCancel}
              className="btn-cancel"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-submit"
              disabled={loading}
            >
              {loading ? 'Creando...' : 'Crear Evento'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default EventForm
