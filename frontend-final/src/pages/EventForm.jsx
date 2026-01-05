import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import "./EventForm.css";

function EventForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [formData, setFormData] = useState({
    nombre: "",
    descripcion: "",
    fecha_hora_inicio: "",
    fecha_hora_fin: "",
    ubicacion: "",
    capacidad_maxima: "",
    imagen_url: "",
  });
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState("");
  const [uploadingImage, setUploadingImage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isEdit) {
      loadEvent();
    }
  }, [id]);

  const loadEvent = async () => {
    try {
      const response = await axios.get(`/events/${id}`);
      const event = response.data;
      setFormData({
        nombre: event.nombre || "",
        descripcion: event.descripcion || "",
        fecha_hora_inicio: event.fecha_hora_inicio
          ? event.fecha_hora_inicio.slice(0, 16)
          : "",
        fecha_hora_fin: event.fecha_hora_fin
          ? event.fecha_hora_fin.slice(0, 16)
          : "",
        ubicacion: event.ubicacion || "",
        capacidad_maxima: event.capacidad_maxima || "",
        imagen_url: event.imagen_url || "",
      });
    } catch (error) {
      setError("Error al cargar evento");
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadImage = async () => {
    if (!imageFile) return null;

    setUploadingImage(true);
    try {
      const formData = new FormData();
      formData.append("file", imageFile);

      const response = await axios.post("/events/upload-image", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("📸 Upload response:", response.data);
      return response.data.imagen_url;
    } catch (error) {
      console.error("Error al subir imagen:", error);
      return null;
    } finally {
      setUploadingImage(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      let imagePath = formData.imagen_url;

      // Si hay una nueva imagen, subirla primero
      if (imageFile) {
        const uploadedPath = await uploadImage();
        if (uploadedPath) {
          imagePath = uploadedPath;
        }
      }

      const submitData = {
        ...formData,
        imagen_url: imagePath,
        capacidad_maxima: formData.capacidad_maxima
          ? parseInt(formData.capacidad_maxima)
          : null,
      };

      if (isEdit) {
        await axios.put(`/events/${id}`, submitData);
      } else {
        await axios.post("/events", submitData);
      }
      navigate("/events");
    } catch (err) {
      setError(err.response?.data?.detail || "Error al guardar evento");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="event-form-container">
      <div className="event-form-card">
        <h1>{isEdit ? "Editar Evento" : "Crear Nuevo Evento"}</h1>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Nombre del Evento *</label>
            <input
              type="text"
              name="nombre"
              value={formData.nombre}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Descripción</label>
            <textarea
              name="descripcion"
              value={formData.descripcion}
              onChange={handleChange}
              rows="3"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Fecha y Hora de Inicio *</label>
              <input
                type="datetime-local"
                name="fecha_hora_inicio"
                value={formData.fecha_hora_inicio}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Fecha y Hora de Fin</label>
              <input
                type="datetime-local"
                name="fecha_hora_fin"
                value={formData.fecha_hora_fin}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Ubicación</label>
              <input
                type="text"
                name="ubicacion"
                value={formData.ubicacion}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Capacidad Máxima</label>
              <input
                type="number"
                name="capacidad_maxima"
                value={formData.capacidad_maxima}
                onChange={handleChange}
                min="1"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Imagen del Evento (opcional)</label>
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="file-input"
            />
            <small className="form-hint">
              Formatos permitidos: JPG, PNG, GIF, WebP
            </small>

            {(imagePreview || formData.imagen_url) && (
              <div className="image-preview">
                <img
                  src={imagePreview || formData.imagen_url}
                  alt="Preview"
                  onError={(e) => (e.target.style.display = "none")}
                />
              </div>
            )}

            {uploadingImage && (
              <div className="upload-progress">Subiendo imagen...</div>
            )}
          </div>

          {error && <div className="error-banner">{error}</div>}

          <div className="form-actions">
            <button
              type="button"
              onClick={() => navigate("/events")}
              className="btn-secondary"
              disabled={loading || uploadingImage}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || uploadingImage}
              className="btn-primary"
            >
              {uploadingImage
                ? "Subiendo imagen..."
                : loading
                ? "Guardando..."
                : "Guardar Evento"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EventForm;
