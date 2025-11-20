import './EventList.css'

function EventList({ events, onSelectEvent, onCreateNew }) {
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
    <div className="event-list-container">
      <div className="event-list-header">
        <h2>Mis Eventos</h2>
        <button onClick={onCreateNew} className="btn-create">
          Crear Evento
        </button>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">
          <h3>No hay eventos registrados</h3>
          <p>Crea tu primer evento para comenzar a registrar asistencias</p>
          <button onClick={onCreateNew} className="btn-create-empty">
            Crear Primer Evento
          </button>
        </div>
      ) : (
        <div className="events-grid">
          {events.map((event) => (
            <div key={event.id} className="event-card">
              <div className="event-card-header">
                <h3>{event.nombre}</h3>
              </div>
              <div className="event-card-body">
                <div className="event-info">
                  <span className="event-label">Fecha y Hora:</span>
                  <span className="event-value">{formatDate(event.fecha_hora)}</span>
                </div>
              </div>
              <div className="event-card-footer">
                <button
                  onClick={() => onSelectEvent(event)}
                  className="btn-register"
                >
                  Registrar Asistencia
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default EventList
