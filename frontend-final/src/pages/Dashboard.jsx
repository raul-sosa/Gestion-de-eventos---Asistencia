import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import "./Dashboard.css";

function Dashboard() {
  // Query para estadísticas globales con caché
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["globalStats"],
    queryFn: async () => {
      const response = await axios.get("/reports/statistics/global");
      return response.data;
    },
    staleTime: 30000,
  });

  // Query para eventos recientes con caché
  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ["recentEvents"],
    queryFn: async () => {
      const response = await axios.get("/events");
      return response.data.slice(0, 5);
    },
    staleTime: 30000,
  });

  const loading = statsLoading || eventsLoading;

  if (loading) return <div className="loading">Cargando dashboard...</div>;

  // Datos para gráfica de pastel (Pre-registros vs Asistencias)
  const pieData = [
    { name: "Pre-registrados", value: stats?.total_pre_registros || 0 },
    { name: "Asistencias", value: stats?.total_attendances || 0 },
  ];

  // Datos para gráfica de barras (Eventos)
  const barData = [
    { name: "Activos", cantidad: stats?.active_events || 0 },
    {
      name: "Finalizados",
      cantidad: (stats?.total_events || 0) - (stats?.active_events || 0),
    },
  ];

  const COLORS = ["#52796f", "#84a98c", "#cad2c5"];

  return (
    <div className="dashboard-container">
      <h1>Dashboard</h1>

      {/* Grid de estadísticas */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Eventos</h3>
          <p className="stat-value">{stats?.total_events || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Eventos Activos</h3>
          <p className="stat-value">{stats?.active_events || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Pre-registrados</h3>
          <p className="stat-value">{stats?.total_pre_registros || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Asistencias</h3>
          <p className="stat-value">{stats?.total_attendances || 0}</p>
        </div>
      </div>

      {/* Grid de gráficas y eventos */}
      <div className="dashboard-grid">
        {/* Gráfica de Pastel - Asistencias */}
        <div className="chart-card">
          <h2>Pre-registros vs Asistencias</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name}: ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfica de Barras - Eventos */}
        <div className="chart-card">
          <h2>Estado de Eventos</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#cad2c5" />
              <XAxis dataKey="name" stroke="#354f52" />
              <YAxis stroke="#354f52" />
              <Tooltip />
              <Legend />
              <Bar dataKey="cantidad" fill="#52796f" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Eventos Recientes */}
        <div className="recent-events-card">
          <h2>Eventos Recientes</h2>
          {events && events.length > 0 ? (
            <div className="events-list">
              {events.map((event) => (
                <div key={event.id} className="event-item">
                  <div className="event-info">
                    <h3>{event.nombre}</h3>
                    <p>{new Date(event.fecha_hora_inicio).toLocaleString()}</p>
                  </div>
                  <Link
                    to={`/events/${event.id}/attendance`}
                    className="btn-link"
                  >
                    Registrar
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-events">No hay eventos recientes</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
