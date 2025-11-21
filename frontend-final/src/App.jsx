import { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";
import axios from "axios";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import StudentDashboard from "./pages/StudentDashboard";
import EventsList from "./pages/EventsList";
import EventForm from "./pages/EventForm";
import AttendanceRegister from "./pages/AttendanceRegister";
import Reports from "./pages/Reports";
import "./App.css";
import "./styles/mobile.css";

// Configurar baseURL de axios para usar el proxy de Vite
axios.defaults.baseURL = "/api";
axios.defaults.timeout = 30000; // 30 segundos timeout

// Configurar React Query con caché optimizado
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // Los datos son frescos por 30 segundos
      cacheTime: 300000, // Mantener en caché por 5 minutos
      refetchOnWindowFocus: false, // No recargar al cambiar de ventana
      retry: 1, // Solo reintentar una vez en caso de error
    },
  },
});

axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error("[API Request Error]", error);
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => {
    console.log(
      `[API Response] ${response.config.method?.toUpperCase()} ${
        response.config.url
      } - ${response.status}`
    );
    return response;
  },
  (error) => {
    console.error(
      `[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}`,
      {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      }
    );

    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const storedUser = localStorage.getItem("user");

    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, userData) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);

    // Redirigir segun rol
    if (userData.role === "estudiante") {
      navigate("/dashboard");
    } else if (userData.role === "encargado") {
      navigate("/events");
    } else {
      navigate("/dashboard");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    navigate("/login");
  };

  const RequireRole = ({ children, allowedRoles }) => {
    if (!user) return <Navigate to="/login" />;
    if (!allowedRoles.includes(user.role)) {
      return <Navigate to="/dashboard" />;
    }
    return children;
  };

  if (loading) {
    return <div className="loading">Cargando...</div>;
  }

  const getDefaultRoute = () => {
    if (!user) return "/login";
    if (user.role === "estudiante") return "/dashboard";
    if (user.role === "encargado") return "/events";
    return "/dashboard";
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        {user && <Sidebar />}
        {user && <Header user={user} onLogout={handleLogout} />}

        <div className={user ? "main-content" : ""}>
          <Routes>
            <Route
              path="/login"
              element={
                user ? (
                  <Navigate to={getDefaultRoute()} />
                ) : (
                  <Login onLogin={handleLogin} />
                )
              }
            />

            <Route
              path="/dashboard"
              element={
                user ? (
                  user.role === "estudiante" ? (
                    <StudentDashboard />
                  ) : (
                    <Dashboard />
                  )
                ) : (
                  <Navigate to="/login" />
                )
              }
            />

            <Route
              path="/events"
              element={
                <RequireRole allowedRoles={["admin", "encargado"]}>
                  <EventsList />
                </RequireRole>
              }
            />

            <Route
              path="/events/new"
              element={
                <RequireRole allowedRoles={["admin"]}>
                  <EventForm />
                </RequireRole>
              }
            />

            <Route
              path="/events/:id/edit"
              element={
                <RequireRole allowedRoles={["admin"]}>
                  <EventForm />
                </RequireRole>
              }
            />

            <Route
              path="/events/:id/attendance"
              element={
                <RequireRole allowedRoles={["admin", "encargado"]}>
                  <AttendanceRegister />
                </RequireRole>
              }
            />

            <Route
              path="/reports"
              element={
                <RequireRole allowedRoles={["admin"]}>
                  <Reports />
                </RequireRole>
              }
            />

            <Route path="/" element={<Navigate to={getDefaultRoute()} />} />
          </Routes>
        </div>
      </div>
    </QueryClientProvider>
  );
}

export default App;
