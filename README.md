# AI Workflow Orchestrator

An open-source workflow automation engine inspired by Zapier and Make, featuring native AI integrations. The system allows developers to string together event-driven tasks, process conditional logic, and execute Large Language Model (LLM) operations without writing new Python code. It is designed around an asynchronous event-driven architecture.

---

## 🚀 Key Features

*   **Workflow Engine**: Define sequential or branching automation tasks dynamically via clean JSON structures.
*   **Webhook Triggers**: Fire workflows instantly through external incoming HTTP payloads.
*   **Embedded AI Nodes**: Natively interact with LLMs directly within workflows (Powered by Groq):
    *   `ai_classify`: Route logic dynamically based on semantic content.
    *   `ai_generate`: Autonomously write context-aware outputs or responses.
*   **Asynchronous Workers**: Uses Redis queues to push tasks to background workers, improving API responsiveness.
*   **Retry Mechanism**: Built-in fault tolerance logic that catches failures, delays execution, and safely re-queues them.
*   **Conditional Branching**: Programmable `if/else` steps evaluating dynamic variables injected at runtime.
*   **Execution Logging**: Stores step results, errors, and JSON inputs/outputs durably in the database.

---

## 🏗️ Architecture Overview

The system is built using the following stack:

1.  **Backend (FastAPI)**: The main API service handling routing, validation, and webhook ingestion.
2.  **Worker Process (Python/AsyncIO)**: A concurrent daemon that polls the Redis queue to execute workflow steps.
3.  **Frontend (React)**: A Vite + TypeScript dashboard to create workflows and visualize execution history.
4.  **Message Broker (Redis)**: Enables task queuing between the API and the background workers.
5.  **Database (PostgreSQL)**: Persistent storage for workflow definitions and historical execution states.

---

## 📂 Project Structure

This monorepo is structured as follows:

```text
/
├── backend/    # FastAPI server, database setup, and worker process.
└── frontend/   # React Single Page Application (UI dashboard).
```

---

## ⚙️ How It Works

When a workflow runs, data travels through a decoupled pipeline:

`Webhook Call ➡️ API ➡️ Redis Queue ➡️ Background Worker ➡️ JSON Interpreter/Executor ➡️ PostgreSQL`

> Note: Workflows are executed asynchronously to avoid blocking API requests, ensuring fast responses for webhook triggers.

---

## 🧩 Core Concepts

*   **Workflow Definition (JSON)**: Workflows are strictly defined as JSON schemas containing step configurations, conditions, and LLM prompts.
*   **Execution Context**: Variables are propagated through the workflow as a persistent context dictionary. Output from a previous step is injected dynamically (e.g. `{{steps.category}}`) into future steps.
*   **Step Engine**: The core interpreter pattern iterating through the JSON steps sequentially and routing the execution logic based on conditions.
*   **Async Processing (Redis workers)**: The API enqueues tasks and returns immediately, while independent worker daemons handle execution.
*   **Retry Mechanism**: Designed for resilience against third-party API rate limits or network issues, allowing configurable amounts of retries per workflow failure.

---

## 📝 Example AI Workflow

This JSON workflow listens to a webhook, uses AI to classify the user's intent, and generates a polite apology if it detects a complaint:

```json
{
  "trigger": { "type": "webhook" },
  "steps": [
    {
      "type": "ai_classify",
      "input": "{{input.user_email_text}}",
      "labels": ["complaint", "feedback", "praise"],
      "output_key": "category"
    },
    {
      "type": "condition",
      "expression": "{{steps.category}} == 'complaint'",
      "then": [
        {
          "type": "ai_generate",
          "prompt": "Write a highly polite, professional apology handling this: {{input.user_email_text}}",
          "output_key": "email_response"
        }
      ],
      "else": []
    },
    {
      "type": "response",
      "message": "AI Output Processed: {{steps.email_response}}"
    }
  ]
}
```

---

## 🛠️ Getting Started

### 1. Configure Secrets
Create a `.env` file within the `/backend` folder with the following variables:
```env
GROQ_API_KEY="your_groq_api_key"
REDIS_URL="redis://localhost:6379"
DATABASE_URL="postgresql+asyncpg://user:password@localhost/dbname"
```

### 2. Run the Backend
Open **two terminals** in the `backend/` directory.

Terminal 1 (The API):
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Terminal 2 (The Workers):
```bash
cd backend
python -m app.workers.workflow_worker
```

### 3. Run the Frontend
Open **another terminal** inside the UI project:
```bash
cd frontend
npm install
npm run dev
```
Navigate to **`http://localhost:5173`** to interact with the dashboard.

---

## 💡 Why This Project Matters

This project demonstrates core backend engineering skills and systems architecture:
*   **System Design:** Designing a custom execution engine capable of parsing, managing state, and conditionally routing workloads dynamically.
*   **Asynchronous Processing:** Abstracting heavy computational tasks (like AI inference) away from the HTTP request-response cycle using Redis, guaranteeing fast webhook acknowledgment.
*   **AI Integration:** Building practical tooling around LLMs rather than just superficial wrappers, embedding AI functional logic within business workflows.
*   **Separation of Concerns:** Maintaining hard boundaries between the web server, the worker queues, the execution mechanics, and the persistent storage layer.

---

## 🔮 Future Improvements

- Add OAuth/JWT Authentication to secure internal endpoints.
- Build a visual Node Graph Editor extending the React UI.
- Introduce `CRON` trigger types.
