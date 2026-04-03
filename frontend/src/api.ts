import axios from "axios";

// Instancia global de Axios re-utilizable para consumir FastAPI.
// Utiliza variables de entorno provistas por Vite o recae al entorno local por default.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
