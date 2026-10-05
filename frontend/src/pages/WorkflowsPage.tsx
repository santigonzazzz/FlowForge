import { useCallback, useEffect, useMemo, useState } from "react";
import api from "../api";
import CreateWorkflowForm from "../components/CreateWorkflowForm";

interface Props { onViewExecutions: (id: string) => void; demoMode: boolean; }
interface Workflow { id: string; name: string; is_active: boolean; definition?: { trigger?: { type?: string }; steps?: unknown[] }; created_at?: string; runs?: number; success?: number; lastRun?: string; color?: string; icon?: string; }

const DEMO_WORKFLOWS: Workflow[] = [
  { id: "demo-support-ai", name: "AI Support Triage", is_active: true, definition:{trigger:{type:"webhook"},steps:[1,2,3,4]}, runs: 2841, success: 98.4, lastRun:"2 min ago", color:"#e9f7d8", icon:"✦" },
  { id: "demo-lead-enrichment", name: "Lead Enrichment Pipeline", is_active: true, definition:{trigger:{type:"schedule"},steps:[1,2,3]}, runs: 1956, success: 96.7, lastRun:"12 min ago", color:"#e5efff", icon:"↗" },
  { id: "demo-invoice", name: "Invoice Data Extractor", is_active: true, definition:{trigger:{type:"email"},steps:[1,2,3,4,5]}, runs: 1682, success: 99.1, lastRun:"28 min ago", color:"#f7e9d7", icon:"▤" },
  { id: "demo-social", name: "Social Content Generator", is_active: false, definition:{trigger:{type:"schedule"},steps:[1,2,3]}, runs: 1363, success: 94.2, lastRun:"3 hours ago", color:"#f2e6f7", icon:"◇" },
];

const triggerLabel = (value?: string) => ({ webhook:"Webhook", schedule:"Schedule", email:"Email trigger" }[value || ""] || "Manual");

export default function WorkflowsPage({ onViewExecutions, demoMode }: Props) {
  const [workflows, setWorkflows] = useState<Workflow[]>(demoMode ? DEMO_WORKFLOWS : []);
  const [loading, setLoading] = useState(!demoMode);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const [executing, setExecuting] = useState<Record<string, boolean>>({});

  const fetchWorkflows = useCallback(async () => {
    if (demoMode) { setWorkflows(DEMO_WORKFLOWS); setLoading(false); return; }
    setLoading(true);
    try { const res = await api.get("/workflows"); setWorkflows(res.data); }
    catch { setWorkflows([]); }
    finally { setLoading(false); }
  }, [demoMode]);

  useEffect(() => { fetchWorkflows(); }, [fetchWorkflows]);
  const filtered = useMemo(() => workflows.filter(w => w.name.toLowerCase().includes(search.toLowerCase())), [workflows, search]);

  const handleExecute = async (workflow: Workflow) => {
    setExecuting(prev => ({...prev,[workflow.id]:true}));
    if (!demoMode) { try { await api.post(`/workflows/${workflow.id}/execute`); } catch { /* API feedback belongs in execution history. */ } }
    window.setTimeout(() => setExecuting(prev => ({...prev,[workflow.id]:false})), 650);
  };

  return (
    <section className="page">
      <div className="page-heading">
        <div><p className="eyebrow">Automation center</p><h1>Good morning, Santiago.</h1><p>Build, monitor and scale your automated workflows from one place.</p></div>
        <div className="heading-actions"><button className="btn">⇩ Export</button><button className="btn btn-primary" onClick={() => setShowForm(v => !v)}><b>＋</b> New workflow</button></div>
      </div>

      <div className="stats-grid">
        <div className="stat-card"><div className="stat-top"><span>Total workflows</span><i className="stat-icon">⌘</i></div><div className="stat-value"><strong>{workflows.length || 0}</strong><span className="trend neutral">{workflows.filter(w=>w.is_active).length} active</span></div></div>
        <div className="stat-card"><div className="stat-top"><span>Runs this month</span><i className="stat-icon">↗</i></div><div className="stat-value"><strong>7,842</strong><span className="trend">↑ 12.6%</span></div></div>
        <div className="stat-card"><div className="stat-top"><span>Success rate</span><i className="stat-icon">✓</i></div><div className="stat-value"><strong>97.6%</strong><span className="trend">↑ 1.4%</span></div></div>
        <div className="stat-card"><div className="stat-top"><span>Time saved</span><i className="stat-icon">◷</i></div><div className="stat-value"><strong>126h</strong><span className="trend">↑ 18.2%</span></div></div>
      </div>

      {showForm && <CreateWorkflowForm onCreated={() => { fetchWorkflows(); setShowForm(false); }} />}

      <div className="panel">
        <div className="panel-toolbar"><div className="panel-title">All workflows <span>{filtered.length} automations</span></div><div className="toolbar-right"><label className="search-box">⌕<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search workflows..." /></label><button className="btn btn-small">☷ Filter</button></div></div>
        {loading ? <div className="loading-state">Syncing workflows with FlowForge API…</div> : filtered.length === 0 ? <div className="empty-state">No workflows found. Create your first automation to get started.</div> : (
          <table className="workflow-table">
            <thead><tr><th>Workflow</th><th>Trigger</th><th>Status</th><th>Runs</th><th>Success rate</th><th>Last run</th><th /></tr></thead>
            <tbody>{filtered.map((w,index)=><tr key={w.id}>
              <td><div className="workflow-name"><span className="workflow-logo" style={{background:w.color || ["#e9f7d8","#e5efff","#f7e9d7","#f2e6f7"][index%4]}}>{w.icon || "⌁"}</span><div><strong>{w.name}</strong><small>{w.definition?.steps?.length || 1} connected steps</small></div></div></td>
              <td><span className="trigger"><i className="dot" />{triggerLabel(w.definition?.trigger?.type)}</span></td>
              <td><span className={w.is_active?"status":"status paused"}>{w.is_active?"Active":"Paused"}</span></td>
              <td><span className="run-count">{(w.runs || 0).toLocaleString()}</span></td>
              <td><span className="success-rate"><span className="mini-bar"><i style={{width:`${w.success || 0}%`}} /></span>{w.success ? `${w.success}%` : "—"}</span></td>
              <td>{w.lastRun || "Not run yet"}</td>
              <td><div className="row-actions"><button className="action-btn" onClick={()=>onViewExecutions(w.id)}>History</button><button className="action-btn run" disabled={!w.is_active || executing[w.id]} onClick={()=>handleExecute(w)}>{executing[w.id]?"Running…":"▶ Run"}</button></div></td>
            </tr>)}</tbody>
          </table>
        )}
        <div className="panel-footer"><span>Showing {filtered.length} of {filtered.length} workflows</span><div className="pagination"><button className="page-button">‹</button><button className="page-button active">1</button><button className="page-button">›</button></div></div>
      </div>
    </section>
  );
}
