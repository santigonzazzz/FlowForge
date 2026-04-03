import { useState, useEffect } from "react";
import api from "../api";
import CreateWorkflowForm from "../components/CreateWorkflowForm";

interface Props {
  onViewExecutions: (id: string) => void;
}

export default function WorkflowsPage({ onViewExecutions }: Props) {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState<Record<string, boolean>>({});

  const fetchWorkflows = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/workflows");
      setWorkflows(res.data);
    } catch (err: any) {
      setError(`No se ha podido conectar al servidor: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (id: string) => {
    setExecuting(prev => ({ ...prev, [id]: true }));
    try {
      // POST directo para ejecución manual sincrónica
      const res = await api.post(`/workflows/${id}/execute`);
      const data = res.data;
      
      const isSuccess = data.success === true;
      const errorMsg = data.results?.find((r: any) => r.error)?.error || "Fallo en ejecución interna";
      
      const details = isSuccess 
        ? `✅ ÉXITO\n\nPasos ejecutados: ${data.steps_executed}/${data.steps_total}\nRespuesta Final: ${JSON.stringify(data.response, null, 2)}`
        : `❌ FALLÓ\n\nMotivo: ${errorMsg}`;
        
      alert(`Resultados del Ejecutor:\n\n${details}`);
    } catch (err: any) {
      alert(`Error crítico de Red / API:\n${err.response?.data?.detail || err.message}`);
    } finally {
      setExecuting(prev => ({ ...prev, [id]: false }));
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  return (
    <div className="card" style={{ maxWidth: "800px", margin: "0 auto" }}>
      <h1>Workflows</h1>
      <h3>Directorio de automatizaciones</h3>

      <CreateWorkflowForm onCreated={fetchWorkflows} />

      {error && (
        <div style={{ 
          marginBottom: "2rem", 
          color: "#fb7185", 
          background: "rgba(251, 113, 133, 0.1)", 
          padding: "1rem", 
          borderRadius: "10px",
          border: "1px solid rgba(251, 113, 133, 0.2)"
        }}>
          {error}
        </div>
      )}

      <div style={{ textAlign: "left", marginBottom: "2rem", minHeight: "200px" }}>
        {loading ? (
          <p style={{ textAlign: "center", color: "#64748b" }}>Cargando información desde FastAPI...</p>
        ) : workflows.length === 0 && !error ? (
          <p style={{ textAlign: "center", color: "#64748b" }}>No tienes ningún workflow. Crea uno vía API.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {workflows.map((w: any) => (
              <li key={w.id} style={{ 
                padding: "1.2rem 1.5rem", 
                background: "rgba(255, 255, 255, 0.02)", 
                marginBottom: "0.8rem", 
                borderRadius: "12px",
                border: "1px solid rgba(255, 255, 255, 0.05)",
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem",
                transition: "background 0.2s"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ color: "#f8fafc", fontSize: "1.25rem" }}>
                    {w.name}
                  </strong>
                  <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                    {w.is_active ? 
                      <span style={{ color: "#34d399", fontSize: "0.9rem", fontWeight: 600, letterSpacing: "0.5px" }}>🟢 ACTIVO</span> : 
                      <span style={{ color: "#64748b", fontSize: "0.9rem", fontWeight: 600, letterSpacing: "0.5px" }}>⭕ INACTIVO</span>
                    }
                    <button 
                      onClick={() => onViewExecutions(w.id)}
                      style={{ 
                        padding: "0.5em 1em", 
                        fontSize: "0.85rem", 
                        background: "rgba(255,255,255,0.05)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        boxShadow: "none"
                      }}
                    >
                      Historial
                    </button>
                    <button 
                      onClick={() => handleExecute(w.id)}
                      disabled={executing[w.id] || !w.is_active}
                      style={{ 
                        padding: "0.5em 1em", 
                        fontSize: "0.85rem", 
                        background: executing[w.id] ? "#475569" : "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                        boxShadow: "none"
                      }}
                    >
                      {executing[w.id] ? "Corriendo..." : "▶ Ejecutar en línea"}
                    </button>
                  </div>
                </div>
                <div style={{ color: "#94a3b8", fontSize: "0.85rem", fontFamily: "monospace" }}>
                  ID: {w.id}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <button onClick={fetchWorkflows} disabled={loading}>
        {loading ? "Sincronizando..." : "Refrescar Lista"}
      </button>
    </div>
  );
}
