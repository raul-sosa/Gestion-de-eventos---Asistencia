import { useState, useEffect, useRef } from "react";
import { Html5Qrcode } from "html5-qrcode";
import "./CameraScanner.css";

function CameraScanner({ onScan, onClose }) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const scannerRef = useRef(null);
  const html5QrCodeRef = useRef(null);

  useEffect(() => {
    return () => {
      // Cleanup al desmontar
      if (html5QrCodeRef.current && html5QrCodeRef.current.isScanning) {
        html5QrCodeRef.current.stop().catch((err) => console.error(err));
      }
    };
  }, []);

  const startScanning = async () => {
    try {
      setError(null);
      setScanning(true);

      const html5QrCode = new Html5Qrcode("qr-reader");
      html5QrCodeRef.current = html5QrCode;

      const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
      };

      await html5QrCode.start(
        { facingMode: "environment" }, // Cámara trasera
        config,
        (decodedText) => {
          // Código escaneado exitosamente
          onScan(decodedText);
          stopScanning();
        },
        (errorMessage) => {
          // Error de escaneo (normal, sigue intentando)
        }
      );
    } catch (err) {
      console.error("Error al iniciar cámara:", err);
      setError("No se pudo acceder a la cámara. Verifica los permisos.");
      setScanning(false);
    }
  };

  const stopScanning = async () => {
    if (html5QrCodeRef.current && html5QrCodeRef.current.isScanning) {
      try {
        await html5QrCodeRef.current.stop();
        html5QrCodeRef.current.clear();
      } catch (err) {
        console.error("Error al detener escáner:", err);
      }
    }
    setScanning(false);
  };

  const handleClose = () => {
    stopScanning();
    onClose();
  };

  return (
    <div className="camera-scanner-overlay">
      <div className="camera-scanner-modal">
        <div className="camera-scanner-header">
          <h3>Escanear Código de Barras</h3>
          <button className="close-btn" onClick={handleClose}>
            ✕
          </button>
        </div>

        <div className="camera-scanner-body">
          {!scanning && !error && (
            <div className="scanner-instructions">
              <svg
                width="80"
                height="80"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                <circle cx="12" cy="13" r="4" />
              </svg>
              <p>Presiona el botón para activar la cámara</p>
              <button className="start-camera-btn" onClick={startScanning}>
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
                Activar Cámara
              </button>
            </div>
          )}

          {error && (
            <div className="scanner-error">
              <p>{error}</p>
              <button onClick={() => setError(null)}>Reintentar</button>
            </div>
          )}

          <div
            id="qr-reader"
            style={{ display: scanning ? "block" : "none" }}
          ></div>

          {scanning && (
            <div className="scanner-controls">
              <p className="scanning-text">
                Apunta la cámara al código de barras
              </p>
              <button className="stop-camera-btn" onClick={stopScanning}>
                Detener Cámara
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CameraScanner;
