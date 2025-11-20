import { useState, useEffect, useRef } from "react";
import CameraScanner from "./CameraScanner";
import "./BarcodeScanner.css";

function BarcodeScanner({ onScan, eventId, disabled }) {
  const [barcode, setBarcode] = useState("");
  const [scanning, setScanning] = useState(false);
  const [manualInput, setManualInput] = useState("");
  const [showCamera, setShowCamera] = useState(false);
  const inputRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    // Auto-focus en el input cuando el componente se monta
    if (inputRef.current && !disabled) {
      inputRef.current.focus();
    }
  }, [disabled]);

  const handleKeyPress = (e) => {
    if (disabled) return;

    // Detectar Enter (codigo de barras escaneado)
    if (e.key === "Enter" && barcode.trim()) {
      e.preventDefault();
      handleScan();
    }
  };

  const handleChange = (e) => {
    let value = e.target.value;

    // Solo permitir números y máximo 5 dígitos
    value = value.replace(/\D/g, "").slice(0, 5);
    setBarcode(value);

    // Limpiar timeout anterior
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Auto-scan cuando tenga exactamente 5 dígitos
    if (value.length === 5) {
      timeoutRef.current = setTimeout(() => {
        handleScan();
      }, 100);
    }
  };

  const handleScan = async () => {
    if (!barcode.trim() || !eventId || scanning) return;

    setScanning(true);
    try {
      await onScan(barcode.trim(), eventId);
      setBarcode("");

      // Re-focus en el input
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 100);
    } catch (error) {
      console.error("Error al escanear:", error);
    } finally {
      setScanning(false);
    }
  };

  const handleManualScan = () => {
    if (barcode.length === 5) {
      handleScan();
    }
  };

  const handleCameraScan = (scannedCode) => {
    // Extraer solo números del código escaneado
    const matricula = scannedCode.replace(/\D/g, "").slice(0, 5);
    if (matricula.length === 5) {
      setBarcode(matricula);
      setShowCamera(false);
      // Escanear automáticamente
      setTimeout(() => {
        onScan(matricula, eventId);
      }, 100);
    } else {
      alert("Código inválido. Debe contener 5 dígitos.");
    }
  };

  return (
    <div className="barcode-scanner">
      <div className="scanner-header">
        <h3>Escanear Credencial</h3>
        <div className="scanner-status">
          {scanning ? (
            <span className="status-scanning">Procesando...</span>
          ) : (
            <span className="status-ready">Listo para escanear</span>
          )}
        </div>
      </div>

      <div className="scanner-input-group">
        <input
          ref={inputRef}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          value={barcode}
          onChange={handleChange}
          onKeyPress={handleKeyPress}
          placeholder="Matrícula (5 dígitos)"
          disabled={disabled || scanning}
          className="scanner-input"
          maxLength="5"
          autoFocus
        />
        <button
          onClick={() => setShowCamera(true)}
          disabled={disabled || scanning}
          className="btn-camera"
          title="Escanear con cámara"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
            <circle cx="12" cy="13" r="4" />
          </svg>
        </button>
        <button
          onClick={handleManualScan}
          disabled={barcode.length !== 5 || disabled || scanning}
          className="btn-scan"
        >
          Registrar
        </button>
      </div>

      <div className="scanner-instructions">
        <p>Instrucciones:</p>
        <ul>
          <li>Ingresa la matrícula (5 dígitos) y presiona Enter</li>
          <li>O usa el botón de cámara para escanear el código de barras</li>
          <li>
            El sistema verificará automáticamente si el estudiante está
            registrado
          </li>
        </ul>
      </div>

      {showCamera && (
        <CameraScanner
          onScan={handleCameraScan}
          onClose={() => setShowCamera(false)}
        />
      )}
    </div>
  );
}

export default BarcodeScanner;
