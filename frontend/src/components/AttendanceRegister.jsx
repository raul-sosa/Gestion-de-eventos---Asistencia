import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './AttendanceRegister.css'

const API_URL = 'http://localhost:8000/api'

function AttendanceRegister({ event, token, onBack }) {
  const [idCredencial, setIdCredencial] = useState('')
  const [attendances, setAttendances] = useState([])
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    loadAttendances()
  }, [])

  useEffect(() => {
    // Auto-focus en el input después de registrar
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [attendances])

  const loadAttendances = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/events/${event.id}/attendances`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setAttendances(response.data)
    } catch (error) {
      console.error('Error al cargar asistencias:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!idCredencial.trim()) {
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      await axios.post(
        `${API_URL}/attendances`,
        {
          id_credencial: idCredencial,
          id_evento: event.id
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      setMessage({
        type: 'success',
        text: `Asistencia Registrada para ID: ${idCredencial}`
      })
      
      setIdCredencial('')
      loadAttendances()
      
      // Auto-limpiar mensaje después de 3 segundos
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Error al registrar asistencia'
      })
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="attendance-container">
      <div className="attendance-header">
        <button onClick={onBack} className="btn-back">
          ← Volver a Eventos
        </button>
      </div>

      <div className="attendance-card">
        <div className="event-info-section">
          <h2>Registro de Asistencia</h2>
          <div className="event-details">
            <h3>{event.nombre}</h3>
            <p>Fecha: {formatDate(event.fecha_hora)}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="attendance-form">
          <div className="form-group-inline">
            <label htmlFor="idCredencial">ID de Credencial del Estudiante</label>
            <div className="input-group">
              <input
                ref={inputRef}
                id="idCredencial"
                type="text"
                value={idCredencial}
                onChange={(e) => setIdCredencial(e.target.value)}
                placeholder="Ingrese o escanee el ID (ej: 12345)"
                disabled={loading}
                autoFocus
              />
              <button
                type="submit"
                className="btn-register-attendance"
                disabled={loading || !idCredencial.trim()}
              >
                {loading ? 'Registrando...' : 'Registrar'}
              </button>
            </div>
          </div>

          {message && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}
        </form>

        <div className="attendances-section">
          <div className="section-header">
            <h3>Asistencias Registradas</h3>
            <span className="count-badge">{attendances.length}</span>
          </div>

          {attendances.length === 0 ? (
            <div className="empty-attendances">
              <p>No hay asistencias registradas aún</p>
            </div>
          ) : (
            <div className="attendances-list">
              {attendances.map((attendance) => (
                <div key={attendance.id} className="attendance-item">
                  <div className="attendance-id">
                    <span className="id-label">ID:</span>
                    <span className="id-value">{attendance.id_credencial}</span>
                  </div>
                  <div className="attendance-time">
                    {formatTime(attendance.hora_registro)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AttendanceRegister
