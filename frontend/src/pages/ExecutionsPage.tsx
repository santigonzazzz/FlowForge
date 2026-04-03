import { useState, useEffect } from "react";
import api from "../api";

interface Props {
  workflowId: string;
  onBack: () => void;
}

export default function ExecutionsPage({ workflowId, onBack }: Props) {
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExecutions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/workflows/${workflowId}/executions`);
      setExecutions(res.data);
    } catch (err: any) {
      setError(`Fallo al cargar de la base de datos: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, [workflowId]);

  return (
    <div className="card" style={{ maxWidth: "800px", margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h1>Ejecuciones</h1>
        <button 
          onClick={onBack} 
          style={{ 
            background: "transparent", 
            border: "1px solid rgba(255,255,255,0.2)",
            padding: "0.5rem 1rem",
            boxShadow: "none"
          }}
        >
          &larr; Volver
        </button>
      </div>
      
      <div style={{ textAlign: "left", color: "#94a3b8", marginBottom: "2rem", fontFamily: "monospace" }}>
        Workflow ID: {workflowId}
      </div>

      {error && (
        <div style={{ color: "#fb7185", background: "rgba(251, 113, 133, 0.1)", padding: "1rem", borderRadius: "10px", marginBottom: "1rem", border: "1px solid rgba(251, 113, 133, 0.2)" }}>
          {error}
        </div>
      )}

      <div style={{ textAlign: "left", minHeight: "200px" }}>
        {loading ? (
          <p style={{ textAlign: "center", color: "#64748b" }}>Cargando registros históricos del worker...</p>
        ) : executions.length === 0 ? (
          <p style={{ textAlign: "center", color: "#64748b" }}>Jamás se ha ejecutado este workflow en Postgres.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {executions.map((e: any) => (
              <li key={e.id} style={{
                padding: "1.2rem",
                background: "rgba(255, 255, 255, 0.02)",
                marginBottom: "1rem",
                borderRadius: "12px",
                border: e.status === "success" ? "1px solid rgba(52, 211, 153, 0.2)" 
                    : e.status === "failed" ? "1px solid rgba(251, 113, 133, 0.2)"
                    : "1px solid rgba(245, 158, 11, 0.2)",
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "1rem",
              }}>
                
                <div>
                  <strong style={{ color: "#94a3b8" }}>Estado:</strong>{" "}
                  <span style={{ 
                    color: e.status === "success" ? "#34d399" : e.status === "failed" ? "#fb7185" : "#fcd34d",
                    fontWeight: 600, 
                    textTransform: "uppercase" 
                  }}>{e.status}</span>
                </div>
                
                <div style={{ color: "#e2e8f0" }}>
                  <strong style={{ color: "#94a3b8" }}>Retries:</strong> {e.retry_count} / {e.max_retries}
                </div>

                <div style={{ color: "#e2e8f0", fontSize: "0.9rem" }}>
                  <strong style={{ color: "#94a3b8" }}>Inició:</strong><br/>
                  {new Date(e.started_at).toLocaleString()}
                </div>

                <div style={{ color: "#e2e8f0", fontSize: "0.9rem" }}>
                  <strong style={{ color: "#94a3b8" }}>Terminó:</strong><br/>
                  {e.finished_at ? new Date(e.finished_at).toLocaleString() : "⏳ Corriendo..."}
                </div>

                {e.error_message && (
                  <div style={{ 
                    gridColumn: "1 / -1", 
                    color: "#fecdd3", 
                    fontSize: "0.85rem", 
                    background: "rgba(0,0,0,0.3)", 
                    padding: "0.8rem", 
                    borderRadius: "8px",
                    fontFamily: "monospace",
                    borderLeft: "3px solid #fb7185"
                  }}>
                    {e.error_message}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <button onClick={fetchExecutions} disabled={loading} style={{ marginTop: "2rem" }}>
        {loading ? "Actualizando..." : "Refrescar Logs de Postgres"}
      </button>
    </div>
  );
}
