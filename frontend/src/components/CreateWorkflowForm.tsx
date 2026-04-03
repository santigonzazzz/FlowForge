import { useState } from "react";
import api from "../api";

interface Props {
  onCreated: () => void;
}

export default function CreateWorkflowForm({ onCreated }: Props) {
  const [name, setName] = useState("");
  const [definitionStr, setDefinitionStr] = useState(`{\n  "trigger": { "type": "webhook" },\n  "steps": [\n    {\n      "type": "log",\n      "message": "Hola desde la nube!"\n    }\n  ]\n}`);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("El nombre es obligatorio");
      return;
    }

    // Validación estricta local de JSON antes de tocar red
    let definitionJson;
    try {
      definitionJson = JSON.parse(definitionStr);
    } catch (err: any) {
      setError(`Sintaxis JSON inválida: ${err.message}`);
      return;
    }

    setLoading(true);
    try {
      await api.post("/workflows", {
        name: name.trim(),
        definition: definitionJson,
      });
      // Purgar formulario en caso de éxito
      setName("");
      onCreated();
    } catch (err: any) {
      setError(
        `Fallo al crear: ${
          err.response?.data?.detail 
            ? JSON.stringify(err.response.data.detail) 
            : err.message
        }`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      background: "rgba(255, 255, 255, 0.03)",
      border: "1px solid rgba(255, 255, 255, 0.08)",
      padding: "2rem",
      borderRadius: "16px",
      marginBottom: "2.5rem",
      textAlign: "left"
    }}>
      <h3 style={{ marginTop: 0, color: "#f8fafc", marginBottom: "1.5rem" }}>
        Crear Nuevo Workflow
      </h3>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
        
        <div>
          <label style={{ display: "block", marginBottom: "0.5rem", color: "#94a3b8", fontWeight: 600 }}>
            Nombre identificativo
          </label>
          <input 
            type="text" 
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ej: Clasificador de Spam IA"
            style={{
              width: "100%",
              padding: "0.9rem",
              borderRadius: "10px",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              background: "rgba(0, 0, 0, 0.3)",
              color: "white",
              fontSize: "1rem",
              boxSizing: "border-box",
              outline: "none",
              transition: "border-color 0.2s"
            }}
            onFocus={(e) => e.target.style.borderColor = "#8b5cf6"}
            onBlur={(e) => e.target.style.borderColor = "rgba(255, 255, 255, 0.1)"}
          />
        </div>

        <div>
          <label style={{ display: "block", marginBottom: "0.5rem", color: "#94a3b8", fontWeight: 600 }}>
            Definición (Body JSON)
          </label>
          <textarea 
            value={definitionStr}
            onChange={(e) => setDefinitionStr(e.target.value)}
            rows={10}
            style={{
              width: "100%",
              padding: "1rem",
              borderRadius: "10px",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              background: "rgba(0, 0, 0, 0.3)",
              color: "#34d399",  // Color código clásico
              fontFamily: "'Fira Code', monospace",
              fontSize: "0.95rem",
              boxSizing: "border-box",
              resize: "vertical",
              outline: "none",
              transition: "border-color 0.2s"
            }}
            onFocus={(e) => e.target.style.borderColor = "#8b5cf6"}
            onBlur={(e) => e.target.style.borderColor = "rgba(255, 255, 255, 0.1)"}
          />
        </div>

        {error && (
          <div style={{ 
            color: "#fb7185", 
            background: "rgba(251, 113, 133, 0.1)", 
            padding: "1rem", 
            borderRadius: "10px", 
            border: "1px solid rgba(251, 113, 133, 0.2)" 
          }}>
            {error}
          </div>
        )}

        <button type="submit" disabled={loading} style={{ alignSelf: "flex-start", marginTop: "0.5rem" }}>
          {loading ? "Registrando..." : "Crear Workflow"}
        </button>
      </form>
    </div>
  );
}
