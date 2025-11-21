import { useState } from "react";
import "./PreRegisterModal.css";

function PreRegisterModal({ isOpen, onClose, onConfirm, eventName }) {
  const [matricula, setMatricula] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validar formato de matrícula (5 dígitos)
    if (!/^\d{5}$/.test(matricula)) {
      setError("La matrícula debe tener exactamente 5 dígitos");
      return;
    }

    setLoading(true);
    try {
      await onConfirm(matricula);
      setMatricula("");
      onClose();
    } catch (err) {
      setError(err.message || "Error al pre-registrarse");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setMatricula("");
    setError("");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Pre-registro al Evento</h2>
          <button className="modal-close" onClick={handleClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <p className="event-name">{eventName}</p>
          <p className="modal-description">
            Ingresa tu matrícula para pre-registrarte a este evento
          </p>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="matricula">Matrícula (5 dígitos)</label>
              <input
                type="text"
                id="matricula"
                value={matricula}
                onChange={(e) => setMatricula(e.target.value)}
                placeholder="Ej: 64705"
                maxLength="5"
                pattern="\d{5}"
                required
                autoFocus
                disabled={loading}
              />
              {error && <span className="error-message">{error}</span>}
            </div>

            <div className="modal-actions">
              <button
                type="button"
                onClick={handleClose}
                className="btn-cancel"
                disabled={loading}
              >
                Cancelar
              </button>
              <button type="submit" className="btn-confirm" disabled={loading}>
                {loading ? "Registrando..." : "Confirmar Pre-registro"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default PreRegisterModal;
