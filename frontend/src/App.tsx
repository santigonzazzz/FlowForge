import { useState } from "react";
import WorkflowsPage from "./pages/WorkflowsPage";
import ExecutionsPage from "./pages/ExecutionsPage";
import "./App.css";

function App() {
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);

  return (
    <>
      {selectedWorkflowId ? (
        <ExecutionsPage workflowId={selectedWorkflowId} onBack={() => setSelectedWorkflowId(null)} />
      ) : (
        <WorkflowsPage onViewExecutions={setSelectedWorkflowId} />
      )}
    </>
  );
}

export default App;
