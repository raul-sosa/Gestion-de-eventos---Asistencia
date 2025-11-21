import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import BarcodeScanner from "../components/BarcodeScanner";
import "./AttendanceRegister.css";

function AttendanceRegister() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [event, setEvent] = useState(null);
  const [attendances, setAttendances] = useState([]);
  const [preRegistros, setPreRegistros] = useState([]);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastScanned, setLastScanned] = useState(null);

  useEffect(() => {
    loadEventData();
  }, [id]);

  const loadEventData = async () => {
    try {
      const [eventRes, attendancesRes, preRegistrosRes] = await Promise.all([
        axios.get(`/events/${id}`),
        axios.get(`/events/${id}/attendances`),
        axios.get(`/events/${id}/pre-registros`).catch(() => ({ data: [] })),
      ]);
      setEvent(eventRes.data);
      setAttendances(attendancesRes.data);
      setPreRegistros(preRegistrosRes.data);
    } catch (error) {
      console.error("Error loading data:", error);
    }
  };

  const handleScan = async (barcode) => {
    if (!id) return;

    setLoading(true);
    try {
      // Buscar estudiante en la BD
      let studentInfo = null;
      try {
        const studentRes = await axios.get(`/students/search/${barcode}`);
        studentInfo = studentRes.data;
      } catch (err) {
        // Estudiante no encontrado en BD, continuar sin info
      }

      // Registrar asistencia
      const response = await axios.post("/attendances", {
        id_credencial: barcode,
        id_evento: id,
      });

      setLastScanned({
        matricula: barcode,
        nombre: studentInfo?.nombre || "Desconocido",
        carrera: studentInfo?.carrera || "",
        semestre: studentInfo?.semestre || "",
        timestamp: new Date().toLocaleString(),
      });

      setMessage({
        type: "success",
        text: `Asistencia registrada: ${studentInfo?.nombre || barcode}`,
      });
      await loadEventData();
    } catch (error) {
      console.error("Error al registrar:", error.response?.data);
      const errorMsg =
        error.response?.data?.detail || "Error al registrar asistencia";
      setMessage({
        type: "error",
        text: errorMsg,
      });
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(null), 5000);
    }
  };

  const handleValidate = async (attendanceId, validated) => {
    try {
      await axios.put(`/attendances/${attendanceId}/validate`, {
        validado: validated,
      });
      loadEventData();
    } catch (error) {
      console.error("Error al validar asistencia:", error);
      alert("Error al validar asistencia");
    }
  };

  if (!event) return <div className="loading">Cargando...</div>;

  return (
    <div className="attendance-container">
      <button onClick={() => navigate("/events")} className="btn-back">
        Volver a Eventos
      </button>

      <div className="attendance-card">
        <div className="event-info">
          <h1>Registro de Asistencia</h1>
          <h2>{event.nombre}</h2>
          <div className="event-details">
            <p>Fecha: {new Date(event.fecha_hora_inicio).toLocaleString()}</p>
            <p>Ubicacion: {event.ubicacion || "N/A"}</p>
            {event.capacidad_maxima && (
              <p>Capacidad: {event.capacidad_maxima}</p>
            )}
          </div>
        </div>

        <BarcodeScanner onScan={handleScan} eventId={id} disabled={loading} />

        {message && (
          <div className={`message ${message.type}`}>{message.text}</div>
        )}

        {lastScanned && (
          <div className="last-scanned">
            <h4>Ultimo Registro:</h4>
            <div className="student-info">
              <p>
                <strong>Nombre:</strong> {lastScanned.nombre}
              </p>
              <p>
                <strong>Matricula:</strong> {lastScanned.matricula}
              </p>
              <p>
                <strong>Carrera:</strong> {lastScanned.carrera}
              </p>
              <p>
                <strong>Semestre:</strong> {lastScanned.semestre}
              </p>
            </div>
          </div>
        )}

        <div className="stats-section">
          <div className="stat-card">
            <h4>Pre-Registrados</h4>
            <p className="stat-number">{preRegistros.length}</p>
          </div>
          <div className="stat-card">
            <h4>Asistencias</h4>
            <p className="stat-number">{attendances.length}</p>
          </div>
          <div className="stat-card">
            <h4>Validadas</h4>
            <p className="stat-number">
              {attendances.filter((a) => a.validado).length}
            </p>
          </div>
          <div className="stat-card">
            <h4>Pendientes</h4>
            <p className="stat-number">
              {attendances.filter((a) => !a.validado).length}
            </p>
          </div>
        </div>

        <div className="attendances-section">
          <div className="section-header">
            <h3>Asistencias Registradas</h3>
            <span className="badge">{attendances.length}</span>
          </div>

          <div className="attendances-list">
            {attendances.map((attendance) => (
              <div key={attendance.id} className="attendance-item">
                <div className="attendance-student">
                  <span className="student-name">
                    {attendance.estudiante?.nombre || "Desconocido"}
                  </span>
                  <span className="student-matricula">
                    {attendance.id_credencial}
                  </span>
                </div>
                <span className="time-value">
                  {new Date(attendance.hora_registro).toLocaleTimeString()}
                </span>
                <div className="attendance-actions">
                  <span
                    className={`status ${
                      attendance.validado ? "validated" : "pending"
                    }`}
                  >
                    {attendance.validado ? "Validado" : "Pendiente"}
                  </span>
                  {!attendance.validado && (
                    <button
                      onClick={() => handleValidate(attendance.id, true)}
                      className="btn-validate"
                    >
                      Validar
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AttendanceRegister;
