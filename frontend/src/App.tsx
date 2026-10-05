import { useState } from "react";
import WorkflowsPage from "./pages/WorkflowsPage";
import ExecutionsPage from "./pages/ExecutionsPage";
import "./App.css";

export type View = "workflows" | "executions";

function Logo() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </div>
  );
}

function App() {
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const demoParam = new URLSearchParams(window.location.search).get("demo");
  const hasConfiguredApi = Boolean(import.meta.env.VITE_API_URL);
  const demoMode = demoParam === "1" || (demoParam !== "0" && !hasConfiguredApi);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Logo />
          <div>
            <strong>FlowForge</strong>
            <small>Automation OS</small>
          </div>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          <button className={!selectedWorkflowId ? "nav-item active" : "nav-item"} onClick={() => setSelectedWorkflowId(null)}>
            <span className="nav-icon">⌘</span> Workflows
            <span className="nav-count">4</span>
          </button>
          <button className={selectedWorkflowId ? "nav-item active" : "nav-item"} onClick={() => setSelectedWorkflowId("demo-support-ai")}>
            <span className="nav-icon">↗</span> Executions
          </button>
          <button className="nav-item"><span className="nav-icon">◫</span> Connections</button>
          <button className="nav-item"><span className="nav-icon">◈</span> Templates</button>
        </nav>

        <div className="sidebar-label">Workspace</div>
        <nav className="nav-list secondary">
          <button className="nav-item"><span className="nav-icon">◎</span> Team</button>
          <button className="nav-item"><span className="nav-icon">⚙</span> Settings</button>
        </nav>

        <div className="sidebar-footer">
          <div className="usage-head"><span>Monthly runs</span><strong>7,842 / 10k</strong></div>
          <div className="usage-bar"><span /></div>
          <div className="profile">
            <div className="avatar">SG</div>
            <div><strong>Santiago G.</strong><small>Developer workspace</small></div>
            <span className="more">•••</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><b>/</b>{selectedWorkflowId ? "Execution history" : "Workflows"}</div>
          <div className="topbar-actions">
            {demoMode && <span className="demo-pill"><i /> Demo workspace</span>}
            <button className="icon-button" aria-label="Search">⌕</button>
            <button className="icon-button notification" aria-label="Notifications">♢</button>
            <button className="help-button">?</button>
          </div>
        </header>

        {selectedWorkflowId ? (
          <ExecutionsPage workflowId={selectedWorkflowId} onBack={() => setSelectedWorkflowId(null)} demoMode={demoMode} />
        ) : (
          <WorkflowsPage onViewExecutions={setSelectedWorkflowId} demoMode={demoMode} />
        )}
      </main>
    </div>
  );
}

export default App;
