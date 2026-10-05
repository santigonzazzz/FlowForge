import { useState } from "react";
import api from "../api";

interface Props { onCreated: () => void; }

export default function CreateWorkflowForm({ onCreated }: Props) {
  const [name,setName]=useState("");
  const [definitionStr,setDefinitionStr]=useState(`{"trigger":{"type":"webhook"},"steps":[{"type":"log","message":"New event"}]}`);
  const [error,setError]=useState<string|null>(null);
  const [loading,setLoading]=useState(false);

  const handleSubmit=async(e:React.FormEvent)=>{e.preventDefault();setError(null);if(!name.trim()){setError("A workflow name is required.");return;}let definition;try{definition=JSON.parse(definitionStr);}catch(err){setError(`Invalid JSON: ${err instanceof Error?err.message:"Unknown syntax error"}`);return;}setLoading(true);try{await api.post("/workflows",{name:name.trim(),definition});setName("");onCreated();}catch(err){setError(`Unable to create workflow: ${err instanceof Error?err.message:"API error"}`);}finally{setLoading(false);}};

  return <div className="panel form-panel">
    <div className="panel-toolbar"><div className="panel-title">Create workflow <span>Define a trigger and its execution steps</span></div></div>
    <form className="workflow-form" onSubmit={handleSubmit}>
      <div className="field"><label>Workflow name</label><input value={name} onChange={e=>setName(e.target.value)} placeholder="e.g. Customer onboarding" /></div>
      <div className="field"><label>JSON definition</label><textarea value={definitionStr} onChange={e=>setDefinitionStr(e.target.value)} spellCheck={false} /></div>
      <button className="btn btn-primary" disabled={loading}>{loading?"Creating…":"Create workflow"}</button>
      {error&&<div className="form-error">{error}</div>}
    </form>
  </div>;
}
