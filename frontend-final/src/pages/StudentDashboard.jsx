import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./StudentDashboard.css";

function StudentDashboard() {
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [myRegistrations, setMyRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const eventsRes = await axios.get("/events");
      const activeEvents = eventsRes.data.filter((e) => e.estado === "activo");
      setEvents(activeEvents);
      setLoading(false);
    } catch (error) {
      console.error("Error al cargar datos:", error);
      setLoading(false);
    }
  };

  const handlePreRegister = async (eventId) => {
    if (!user) return;

    try {
      await axios.post("/pre-registros", {
        id_evento: eventId,
        id_estudiante: user.user_id,
      });
      alert("Pre-registro exitoso");
      loadData();
    } catch (error) {
      alert(error.response?.data?.detail || "Error al pre-registrarse");
    }
  };

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div className="student-dashboard">
      <div className="welcome-section">
        <h1>Bienvenido, Estudiante</h1>
        <p>Aqui puedes ver los eventos disponibles y pre-registrarte</p>
      </div>

      <div className="events-section">
        <h2>Eventos Disponibles</h2>

        {events.length === 0 ? (
          <div className="no-events">
            <p>No hay eventos disponibles en este momento</p>
          </div>
        ) : (
          <div className="events-grid">
            {events.map((event) => (
              <div key={event.id} className="event-card-student">
                <div className="event-header">
                  <h3>{event.nombre}</h3>
                  <span className="event-status">{event.estado}</span>
                </div>

                <div className="event-details">
                  {event.descripcion && (
                    <p className="event-description">{event.descripcion}</p>
                  )}

                  <div className="event-info">
                    <div className="info-item">
                      <strong>Fecha Inicio:</strong>
                      <span>
                        {new Date(event.fecha_hora_inicio).toLocaleString()}
                      </span>
                    </div>

                    {event.fecha_hora_fin && (
                      <div className="info-item">
                        <strong>Fecha Fin:</strong>
                        <span>
                          {new Date(event.fecha_hora_fin).toLocaleString()}
                        </span>
                      </div>
                    )}

                    {event.ubicacion && (
                      <div className="info-item">
                        <strong>Ubicacion:</strong>
                        <span>{event.ubicacion}</span>
                      </div>
                    )}

                    {event.capacidad_maxima && (
                      <div className="info-item">
                        <strong>Capacidad:</strong>
                        <span>{event.capacidad_maxima} personas</span>
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => handlePreRegister(event.id)}
                  className="btn-preregister"
                >
                  Pre-Registrarme
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentDashboard;
