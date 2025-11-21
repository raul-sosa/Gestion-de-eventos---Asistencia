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

      // Cargar pre-registros del estudiante
      if (user) {
        try {
          const preRegRes = await axios.get(
            `/pre-registros/student/${user.user_id}`
          );
          setMyRegistrations(preRegRes.data);
        } catch (err) {
          console.error("Error al cargar pre-registros:", err);
        }
      }

      setLoading(false);
    } catch (error) {
      console.error("Error al cargar datos:", error);
      setLoading(false);
    }
  };

  const handlePreRegister = async (eventId) => {
    if (!user) {
      alert("Debes iniciar sesión");
      return;
    }

    const studentId = user.user_id || user.id || user.username;
    if (!studentId) {
      alert("No se pudo identificar al estudiante");
      return;
    }

    try {
      await axios.post("/pre-registros", {
        id_evento: eventId,
        id_estudiante: studentId,
      });
      alert("Pre-registro exitoso");
      loadData();
    } catch (error) {
      console.error("Error completo:", error.response?.data);
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

      {myRegistrations.length > 0 && (
        <div className="my-registrations-section">
          <h2>Mis Pre-Registros</h2>
          <div className="registrations-list">
            {myRegistrations.map((reg) => (
              <div key={reg.id} className="registration-item">
                <h4>{reg.evento_nombre}</h4>
                <p>Fecha: {new Date(reg.evento_fecha).toLocaleString()}</p>
                <p>Ubicación: {reg.evento_ubicacion}</p>
                <span className="registration-date">
                  Registrado: {new Date(reg.fecha_registro).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="events-section">
        <h2>Eventos Disponibles</h2>

        {events.length === 0 ? (
          <div className="no-events">
            <p>No hay eventos disponibles en este momento</p>
          </div>
        ) : (
          <div className="events-grid">
            {events.map((event) => {
              const isRegistered = myRegistrations.some(
                (reg) => reg.id_evento === event.id
              );

              return (
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
                    disabled={isRegistered}
                  >
                    {isRegistered ? "Ya Pre-Registrado" : "Pre-Registrarme"}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentDashboard;
