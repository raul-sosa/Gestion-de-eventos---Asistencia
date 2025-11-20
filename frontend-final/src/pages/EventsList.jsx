import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import "./EventsList.css";

function EventsList() {
  const [filter, setFilter] = useState("all");
  const [userRole, setUserRole] = useState(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      const user = JSON.parse(storedUser);
      setUserRole(user.role);
    }
  }, []);

  // Query con caché para eventos
  const { data: events = [], isLoading: loading } = useQuery({
    queryKey: ["events", filter],
    queryFn: async () => {
      const params = filter !== "all" ? { estado: filter } : {};
      const response = await axios.get("/events", { params });
      return response.data;
    },
    staleTime: 20000, // Datos frescos por 20 segundos
  });

  // Mutation para eliminar con invalidación automática de caché
  const deleteMutation = useMutation({
    mutationFn: (eventId) => axios.delete(`/events/${eventId}`),
    onSuccess: () => {
      queryClient.invalidateQueries(["events"]);
      queryClient.invalidateQueries(["globalStats"]);
      queryClient.invalidateQueries(["recentEvents"]);
    },
  });

  // Mutation para finalizar con invalidación automática de caché
  const finalizeMutation = useMutation({
    mutationFn: (eventId) => axios.post(`/events/${eventId}/finalize`),
    onSuccess: () => {
      queryClient.invalidateQueries(["events"]);
      queryClient.invalidateQueries(["globalStats"]);
      alert("Evento finalizado exitosamente");
    },
  });

  const handleDelete = async (eventId) => {
    if (!window.confirm("¿Está seguro de eliminar este evento?")) return;
    try {
      await deleteMutation.mutateAsync(eventId);
    } catch (error) {
      alert("Error al eliminar evento");
    }
  };

  const handleFinalize = async (eventId) => {
    if (!window.confirm("¿Finalizar evento y validar asistencias?")) return;
    try {
      await finalizeMutation.mutateAsync(eventId);
    } catch (error) {
      alert("Error al finalizar evento");
    }
  };

  if (loading) return <div className="loading">Cargando eventos...</div>;

  return (
    <div className="events-list-container">
      <div className="events-header">
        <h1>{userRole === "encargado" ? "Eventos" : "Gestión de Eventos"}</h1>
        {userRole === "admin" && (
          <Link
            to="/events/new"
            className="btn-create-event"
            title="Crear Nuevo Evento"
          >
            <span className="plus-icon">+</span>
            <span className="btn-text">Nuevo</span>
          </Link>
        )}
      </div>

      <div className="events-filters">
        <button
          className={filter === "all" ? "active" : ""}
          onClick={() => setFilter("all")}
        >
          Todos
        </button>
        <button
          className={filter === "activo" ? "active" : ""}
          onClick={() => setFilter("activo")}
        >
          Activos
        </button>
        <button
          className={filter === "finalizado" ? "active" : ""}
          onClick={() => setFilter("finalizado")}
        >
          Finalizados
        </button>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">
          <p>No hay eventos registrados</p>
          <Link to="/events/new">Crear Primer Evento</Link>
        </div>
      ) : (
        <div className="events-grid">
          {events.map((event) => (
            <div key={event.id} className="event-card">
              {event.imagen_url ? (
                <div className="event-card-image">
                  <img
                    src={event.imagen_url}
                    alt={event.nombre}
                    onError={(e) =>
                      (e.target.parentElement.style.display = "none")
                    }
                  />
                </div>
              ) : (
                <div className="event-card-icon">
                  <svg
                    width="60"
                    height="60"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                </div>
              )}
              <div className="event-card-header">
                <h3>{event.nombre}</h3>
                <span className={`badge ${event.estado}`}>{event.estado}</span>
              </div>
              <div className="event-card-body">
                <p>
                  <strong>Inicio:</strong>{" "}
                  {new Date(event.fecha_hora_inicio).toLocaleString()}
                </p>
                {event.ubicacion && (
                  <p>
                    <strong>Ubicación:</strong> {event.ubicacion}
                  </p>
                )}
                {event.capacidad_maxima && (
                  <p>
                    <strong>Capacidad:</strong> {event.capacidad_maxima}
                  </p>
                )}
              </div>
              <div className="event-card-actions">
                <button
                  onClick={() => navigate(`/events/${event.id}/attendance`)}
                >
                  Asistencia
                </button>
                {userRole === "admin" && event.estado === "activo" && (
                  <>
                    <button
                      onClick={() => navigate(`/events/${event.id}/edit`)}
                    >
                      Editar
                    </button>
                    <button onClick={() => handleFinalize(event.id)}>
                      Finalizar
                    </button>
                  </>
                )}
                {userRole === "admin" && (
                  <button
                    onClick={() => handleDelete(event.id)}
                    className="btn-danger"
                  >
                    Eliminar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default EventsList;
