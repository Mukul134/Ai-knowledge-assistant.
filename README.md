# AI Knowledge Assistant

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=Mukul134/agentic-ai-knowledge-assistant)

A production-quality Agentic AI Knowledge Assistant that processes user documents, saves page-level embeddings in Supabase (PostgreSQL + pgvector), exposes a standardized interface to an OpenAI-powered Agent via the Anthropic Model Context Protocol (MCP), and serves answers with precise source citations in a Next.js streaming interface.

---

## ⚡ Instant One-Click Play (Web Browser)

Click the **Open in GitHub Codespaces** button above to run the entire workspace instantly in your browser:
1. It automatically builds the container environment and installs Node/Python packages.
2. It auto-generates your API `.env` configs.
3. It boots both the FastAPI backend and Next.js frontend in the background.
4. It opens the web interface in a browser preview tab automatically!

---

## Project Structure

```
ai-knowledge-assistant/
├── frontend/             # Next.js frontend with Tailwind CSS
├── backend/              # FastAPI Python backend (Agent & RAG pipeline)
├── mcp-server/           # Knowledge MCP Server (standardized search/list tools)
├── database/             # Supabase schema definitions and SQL migrations
├── docs/                 # Architectural specifications
└── docker/               # Docker Compose and container configs
```

---

## Quick Start (Phase 1 Setup)

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- npm or yarn

### Installation

1. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Set up Python Virtual Environment (Backend & MCP)**:
   ```bash
   cd backend
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up MCP Server dependencies**:
   ```bash
   cd ../mcp-server
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Running the services in Development Mode

- **Frontend**:
  ```bash
  cd frontend
  npm run dev
  ```
  Runs at [http://localhost:3000](http://localhost:3000).

- **Backend**:
  ```bash
  cd backend
  # Ensure your virtual environment is active and configuration is set in .env
  python app/main.py
  ```
  Runs at [http://localhost:8000](http://localhost:8000). Swagger docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

- **MCP Server** (Usually started as a subprocess by the Backend, but can be run via stdio manually for verification):
  ```bash
  cd mcp-server
  python mcp_server.py
  ```
