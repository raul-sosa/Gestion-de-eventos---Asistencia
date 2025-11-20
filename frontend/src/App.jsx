import { useState, useEffect } from 'react'
import axios from 'axios'
import Login from './components/Login'
import EventList from './components/EventList'
import EventForm from './components/EventForm'
import AttendanceRegister from './components/AttendanceRegister'
import './App.css'

const API_URL = 'http://localhost:8000/api'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [username, setUsername] = useState(localStorage.getItem('username') || '')
  const [view, setView] = useState('events') // 'events', 'create', 'attendance'
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [events, setEvents] = useState([])

  useEffect(() => {
    if (token) {
      loadEvents()
    }
  }, [token])

  const loadEvents = async () => {
    try {
      const response = await axios.get(`${API_URL}/events`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setEvents(response.data)
    } catch (error) {
      console.error('Error al cargar eventos:', error)
      if (error.response?.status === 401) {
        handleLogout()
      }
    }
  }

  const handleLogin = (newToken, newUsername) => {
    setToken(newToken)
    setUsername(newUsername)
    localStorage.setItem('token', newToken)
    localStorage.setItem('username', newUsername)
  }

  const handleLogout = () => {
    setToken(null)
    setUsername('')
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setView('events')
    setSelectedEvent(null)
  }

  const handleEventCreated = () => {
    loadEvents()
    setView('events')
  }

  const handleSelectEvent = (event) => {
    setSelectedEvent(event)
    setView('attendance')
  }

  const handleBackToEvents = () => {
    setView('events')
    setSelectedEvent(null)
  }

  if (!token) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Sistema de Asistencias</h1>
          <div className="header-actions">
            <span className="username">Usuario: {username}</span>
            <button onClick={handleLogout} className="btn-logout">
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      <main className="app-main">
        {view === 'events' && (
          <EventList
            events={events}
            onSelectEvent={handleSelectEvent}
            onCreateNew={() => setView('create')}
          />
        )}

        {view === 'create' && (
          <EventForm
            token={token}
            onEventCreated={handleEventCreated}
            onCancel={() => setView('events')}
          />
        )}

        {view === 'attendance' && selectedEvent && (
          <AttendanceRegister
            event={selectedEvent}
            token={token}
            onBack={handleBackToEvents}
          />
        )}
      </main>
    </div>
  )
}

export default App
