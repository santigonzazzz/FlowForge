import { useCallback, useEffect, useState } from "react";
import api from "../api";

interface Props { workflowId: string; onBack: () => void; demoMode: boolean; }
interface Execution { id:string; status:"success"|"failed"|"running"; retry_count:number; max_retries:number; started_at:string; finished_at:string|null; error_message?:string|null; duration?:string; }

const now = Date.now();
const DEMO_EXECUTIONS: Execution[] = [
  { id:"exe_8f24a1", status:"success", retry_count:0, max_retries:3, started_at:new Date(now-2*60000).toISOString(), finished_at:new Date(now-2*60000+1840).toISOString(), duration:"1.84s" },
  { id:"exe_3d91bc", status:"success", retry_count:0, max_retries:3, started_at:new Date(now-14*60000).toISOString(), finished_at:new Date(now-14*60000+2210).toISOString(), duration:"2.21s" },
  { id:"exe_7b42e0", status:"success", retry_count:1, max_retries:3, started_at:new Date(now-41*60000).toISOString(), finished_at:new Date(now-41*60000+3170).toISOString(), duration:"3.17s" },
  { id:"exe_1a98fd", status:"failed", retry_count:3, max_retries:3, started_at:new Date(now-76*60000).toISOString(), finished_at:new Date(now-76*60000+4610).toISOString(), duration:"4.61s", error_message:"LLM provider timeout after 3 retry attempts" },
  { id:"exe_5c76d2", status:"success", retry_count:0, max_retries:3, started_at:new Date(now-128*60000).toISOString(), finished_at:new Date(now-128*60000+1950).toISOString(), duration:"1.95s" },
];

const relativeTime = (date:string) => { const mins=Math.max(1,Math.round((Date.now()-new Date(date).getTime())/60000)); return mins<60?`${mins} min ago`:`${Math.floor(mins/60)}h ago`; };

export default function ExecutionsPage({ workflowId, onBack, demoMode }: Props) {
  const [executions,setExecutions]=useState<Execution[]>(demoMode?DEMO_EXECUTIONS:[]);
  const [loading,setLoading]=useState(!demoMode);

  const fetchExecutions=useCallback(async()=>{ if(demoMode){setExecutions(DEMO_EXECUTIONS);setLoading(false);return;} setLoading(true);try{const res=await api.get(`/workflows/${workflowId}/executions`);setExecutions(res.data);}catch{setExecutions([]);}finally{setLoading(false);} },[workflowId,demoMode]);
  useEffect(()=>{fetchExecutions();},[fetchExecutions]);
  const successful=executions.filter(e=>e.status==="success").length;

  return <section className="page">
    <button className="back-link" onClick={onBack}>← Back to workflows</button>
    <div className="page-heading">
      <div><p className="eyebrow">AI Support Triage</p><h1>Execution history</h1><p>Real-time visibility into every workflow run and retry.</p></div>
      <div className="heading-actions"><button className="btn" onClick={fetchExecutions}>↻ Refresh</button><button className="btn btn-dark">▶ Run workflow</button></div>
    </div>

    <div className="stats-grid">
      <div className="stat-card"><div className="stat-top"><span>Total executions</span><i className="stat-icon">↗</i></div><div className="stat-value"><strong>2,841</strong><span className="trend">↑ 8.3%</span></div></div>
      <div className="stat-card"><div className="stat-top"><span>Successful</span><i className="stat-icon">✓</i></div><div className="stat-value"><strong>2,795</strong><span className="trend">98.4%</span></div></div>
      <div className="stat-card"><div className="stat-top"><span>Avg. duration</span><i className="stat-icon">◷</i></div><div className="stat-value"><strong>2.4s</strong><span className="trend neutral">−0.3s</span></div></div>
      <div className="stat-card"><div className="stat-top"><span>Retries</span><i className="stat-icon">↻</i></div><div className="stat-value"><strong>38</strong><span className="trend neutral">1.3% of runs</span></div></div>
    </div>

    <div className="execution-layout">
      <div className="panel">
        <div className="panel-toolbar"><div className="panel-title">Recent runs <span>Live activity</span></div><div className="toolbar-right"><button className="btn btn-small">☷ All statuses</button></div></div>
        {loading?<div className="loading-state">Loading execution records…</div>:executions.length===0?<div className="empty-state">This workflow has not been executed yet.</div>:<div className="timeline-panel">{executions.map(e=><div className="execution-item" key={e.id}>
          <span className={`execution-marker ${e.status}`}>{e.status==="success"?"✓":e.status==="failed"?"!":"•"}</span>
          <div className="execution-head"><strong>{e.status==="success"?"Workflow completed":e.status==="failed"?"Execution failed":"Workflow running"}</strong><span className="execution-time">{relativeTime(e.started_at)}</span></div>
          <div className="execution-meta"><span>ID <code>{e.id}</code></span><span className="duration">{e.duration || (e.finished_at?"2.1s":"In progress")}</span><span>{e.retry_count>0?`${e.retry_count} ${e.retry_count===1?"retry":"retries"}`:"No retries"}</span></div>
          {e.error_message&&<div className="error-note">{e.error_message}</div>}
        </div>)}</div>}
        <div className="panel-footer"><span>Showing the 5 most recent executions</span><button className="btn btn-small btn-ghost">View all runs →</button></div>
      </div>

      <aside className="summary-stack">
        <div className="summary-card"><h3>Workflow health</h3><div className="health-ring" /><div className="health-caption">Excellent performance over the last 30 days</div></div>
        <div className="summary-card"><h3>Run details</h3><div className="detail-list"><div className="detail-row"><span>Trigger</span><strong>Webhook</strong></div><div className="detail-row"><span>Connected steps</span><strong>4 nodes</strong></div><div className="detail-row"><span>Last deployment</span><strong>Sep 28, 2026</strong></div><div className="detail-row"><span>Successful in view</span><strong>{successful} / {executions.length}</strong></div><div className="detail-row"><span>Workflow ID</span><strong>{workflowId.slice(0,12)}</strong></div></div></div>
      </aside>
    </div>
  </section>;
}
