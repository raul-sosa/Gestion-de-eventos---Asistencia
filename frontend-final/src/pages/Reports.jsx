import { useState, useEffect } from "react";
import axios from "axios";
import "./Reports.css";

function Reports() {
  const [filters, setFilters] = useState({
    event_id: "",
    fecha_inicio: "",
    fecha_fin: "",
    validado: "",
    search_term: "",
  });
  const [attendances, setAttendances] = useState([]);
  const [events, setEvents] = useState([]);
  const [eventStats, setEventStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(true);

  useEffect(() => {
    // Cargar lista de eventos
    const fetchEvents = async () => {
      setLoadingEvents(true);
      try {
        const response = await axios.get("/events");
        setEvents(response.data);
      } catch (error) {
        console.error("Error al cargar eventos:", error);
      } finally {
        setLoadingEvents(false);
      }
    };
    fetchEvents();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    setEventStats(null);
    try {
      // Limpiar filtros vacios y convertir validado a boolean
      const cleanFilters = {};
      if (filters.event_id) cleanFilters.event_id = parseInt(filters.event_id);
      if (filters.fecha_inicio)
        cleanFilters.fecha_inicio = filters.fecha_inicio;
      if (filters.fecha_fin) cleanFilters.fecha_fin = filters.fecha_fin;
      if (filters.validado !== "")
        cleanFilters.validado = filters.validado === "true";
      if (filters.search_term) cleanFilters.search_term = filters.search_term;

      const response = await axios.post("/reports/attendances", cleanFilters);
      setAttendances(response.data);
    } catch (error) {
      console.error("Error al generar reporte:", error);
      alert(
        "Error al generar reporte: " +
          (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const handleEventReport = async () => {
    if (!filters.event_id) {
      alert("Por favor selecciona un evento");
      return;
    }
    setLoading(true);
    try {
      // Obtener evento seleccionado
      const selectedEvent = events.find((e) => e.id === filters.event_id);

      // Obtener asistencias del evento
      const response = await axios.get(
        `/events/${filters.event_id}/attendances`
      );
      const eventAttendances = response.data;

      // Calcular estadísticas
      const totalAttendances = eventAttendances.length;
      const validatedAttendances = eventAttendances.filter(
        (a) => a.validado
      ).length;
      const pendingAttendances = totalAttendances - validatedAttendances;
      const attendanceRate = selectedEvent.capacidad_maxima
        ? ((totalAttendances / selectedEvent.capacidad_maxima) * 100).toFixed(1)
        : totalAttendances > 0
        ? "100"
        : "0";

      setEventStats({
        event_name: selectedEvent.nombre,
        total_attendances: totalAttendances,
        validated_attendances: validatedAttendances,
        pending_attendances: pendingAttendances,
        attendance_rate: attendanceRate,
        attendances_list: eventAttendances, // Guardar lista de asistencias
      });
      setAttendances([]);
    } catch (error) {
      console.error("Error al generar reporte del evento:", error);
      alert(
        "Error al generar reporte: " +
          (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    if (!filters.event_id) {
      alert("Por favor selecciona un evento");
      return;
    }

    try {
      const response = await axios.get(
        `/reports/export/event/${filters.event_id}/pdf`,
        {
          responseType: "blob",
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      const selectedEvent = events.find((e) => e.id === filters.event_id);
      const filename = `reporte_${
        selectedEvent?.nombre.replace(/\s+/g, "_") || "evento"
      }.pdf`;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error al exportar PDF:", error);
      alert(
        "Error al exportar PDF: " +
          (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleExportCSV = () => {
    try {
      let dataToExport = [];
      let filename = "";

      // Si hay estadísticas de evento, exportar esas
      if (eventStats) {
        const selectedEvent = events.find((e) => e.id === filters.event_id);
        dataToExport = [
          ["REPORTE DE EVENTO"],
          ["Evento", eventStats.event_name],
          [
            "Fecha",
            selectedEvent?.fecha_hora_inicio
              ? new Date(selectedEvent.fecha_hora_inicio).toLocaleString()
              : "N/A",
          ],
          ["Ubicación", selectedEvent?.ubicacion || "N/A"],
          ["Capacidad", selectedEvent?.capacidad_maxima || "N/A"],
          [""],
          ["ESTADÍSTICAS"],
          ["Total Asistencias", eventStats.total_attendances],
          ["Asistencias Validadas", eventStats.validated_attendances],
          ["Asistencias Pendientes", eventStats.pending_attendances],
          ["Tasa de Asistencia", eventStats.attendance_rate + "%"],
          [""],
          ["LISTA DE PARTICIPANTES"],
          ["ID Credencial", "Hora de Registro", "Estado"],
          ...eventStats.attendances_list.map((att) => [
            att.id_credencial,
            new Date(att.hora_registro).toLocaleString(),
            att.validado ? "Validado" : "Pendiente",
          ]),
        ];
        filename = `reporte_evento_${eventStats.event_name.replace(
          /\s+/g,
          "_"
        )}_${Date.now()}.csv`;
      }
      // Si hay asistencias, exportar esas
      else if (attendances.length > 0) {
        dataToExport = [
          ["ID Credencial", "Evento", "Hora de Registro", "Estado"],
          ...attendances.map((att) => [
            att.id_credencial,
            att.nombre_evento || "N/A",
            new Date(att.hora_registro).toLocaleString(),
            att.validado ? "Validado" : "Pendiente",
          ]),
        ];
        filename = `reporte_asistencias_${Date.now()}.csv`;
      } else {
        alert("No hay datos para exportar");
        return;
      }

      // Convertir a CSV
      const csvContent = dataToExport
        .map((row) => row.map((cell) => `"${cell}"`).join(","))
        .join("\n");

      // Crear blob con BOM para UTF-8
      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], {
        type: "text/csv;charset=utf-8;",
      });

      // Descargar
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error al exportar CSV:", error);
      alert("Error al exportar CSV: " + error.message);
    }
  };

  return (
    <div className="reports-container">
      <h1>Reportes de Asistencias</h1>

      <div className="filters-section">
        <div className="form-row">
          <select
            value={filters.event_id}
            onChange={(e) =>
              setFilters({ ...filters, event_id: e.target.value })
            }
            disabled={loadingEvents}
          >
            <option value="">
              {loadingEvents ? "Cargando eventos..." : "Seleccionar Evento"}
            </option>
            {events.map((event) => (
              <option key={event.id} value={event.id}>
                {event.nombre} - {event.estado}
              </option>
            ))}
          </select>

          <input
            type="date"
            placeholder="Fecha inicio"
            value={filters.fecha_inicio}
            onChange={(e) =>
              setFilters({ ...filters, fecha_inicio: e.target.value })
            }
          />

          <input
            type="date"
            placeholder="Fecha fin"
            value={filters.fecha_fin}
            onChange={(e) =>
              setFilters({ ...filters, fecha_fin: e.target.value })
            }
          />

          <select
            value={filters.validado}
            onChange={(e) =>
              setFilters({ ...filters, validado: e.target.value })
            }
          >
            <option value="">Todos los estados</option>
            <option value="true">Validados</option>
            <option value="false">Pendientes</option>
          </select>
        </div>

        <div className="actions-row">
          <button
            onClick={handleEventReport}
            disabled={loading || !filters.event_id}
          >
            Reporte del Evento
          </button>
          <button onClick={handleSearch} disabled={loading}>
            {loading ? "Buscando..." : "Buscar Asistencias"}
          </button>
          <button
            onClick={handleExportCSV}
            disabled={!eventStats && attendances.length === 0}
          >
            Exportar CSV
          </button>
          <button onClick={handleExportPDF} disabled={!filters.event_id}>
            Exportar PDF
          </button>
        </div>
      </div>

      {eventStats && (
        <div className="event-stats-section">
          <h2>Estadísticas del Evento: {eventStats.event_name}</h2>
          <div className="stats-cards">
            <div className="stat-card-report">
              <h3>Total Asistencias</h3>
              <p className="stat-number">{eventStats.total_attendances}</p>
            </div>
            <div className="stat-card-report">
              <h3>Validadas</h3>
              <p className="stat-number">{eventStats.validated_attendances}</p>
            </div>
            <div className="stat-card-report">
              <h3>Pendientes</h3>
              <p className="stat-number">{eventStats.pending_attendances}</p>
            </div>
            <div className="stat-card-report">
              <h3>Tasa de Asistencia</h3>
              <p className="stat-number">{eventStats.attendance_rate}%</p>
            </div>
          </div>
        </div>
      )}

      {attendances.length > 0 && (
        <div className="results-section">
          <h2>Resultados: {attendances.length} asistencias</h2>
          <table>
            <thead>
              <tr>
                <th>ID Credencial</th>
                <th>Evento</th>
                <th>Hora de Registro</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {attendances.map((att) => (
                <tr key={att.id}>
                  <td>{att.id_credencial}</td>
                  <td>{att.nombre_evento}</td>
                  <td>{new Date(att.hora_registro).toLocaleString()}</td>
                  <td>
                    <span
                      className={`status-badge ${
                        att.validado ? "validado" : "pendiente"
                      }`}
                    >
                      {att.validado ? "Validado" : "Pendiente"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!eventStats && attendances.length === 0 && (
        <div className="empty-results">
          <p>
            Selecciona un evento y genera un reporte o busca asistencias con los
            filtros
          </p>
        </div>
      )}
    </div>
  );
}

export default Reports;
