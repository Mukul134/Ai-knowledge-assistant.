# Deployment Guide: Hostinger VPS & Docker Compose

This document provides a comprehensive step-by-step guide to build, test, and deploy the Agentic AI Knowledge Assistant locally and to a **Hostinger VPS** using **Docker Compose** and **Nginx**.

---

## 1. How to Build the Project Locally

### Step A: Clone the Repository
Clone the codebase to your local environment:
```bash
git clone <your-repository-url>
cd ai-knowledge-assistant
```

### Step B: Create Local Environment Files
Copy the `.env.example` configurations to local `.env` files:
- **Backend**: Copy `backend/.env.example` to `backend/.env`
- **Frontend**: Copy `frontend/.env.example` to `frontend/.env`

---

## 2. How to Run Locally (Without Docker)

### Run the Backend & MCP Server
1. Navigate to the backend directory and activate the virtual environment:
   ```bash
   cd backend
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
2. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI development server:
   ```bash
   python app/main.py
   ```
   The backend API will run on [http://localhost:8000](http://localhost:8000). Swagger documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Run the Frontend Next.js Web App
1. Open a new terminal window, navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```
2. Run the Next.js development server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) to view the client-side workspace dashboard.

---

## 3. How to Run Locally (With Docker)

To run the complete system locally inside isolated containers (mirroring production):
1. Navigate to the `docker/` directory:
   ```bash
   cd docker
   ```
2. Start the services using Docker Compose:
   ```bash
   docker compose up --build
   ```
3. To stop the containers:
   ```bash
   docker compose down
   ```

---

## 4. How to Configure Supabase

1. **Create Project**: Sign up on [Supabase](https://supabase.com) and create a new project.
2. **Execute Migrations**: Go to the **SQL Editor** on the Supabase dashboard, copy the contents of [`database/schema.sql`](file:///C:/Users/hp/ai-knowledge-assistant/database/schema.sql), and click **Run**.
3. **Configure private Storage Bucket**:
   - Go to **Storage** in the sidebar.
   - Click **New Bucket**, name it `documents`, and ensure **Public** is turned **OFF** (private bucket).
4. **Collect API Credentials**: Go to **Project Settings** -> **API** and copy:
   - `Project URL`
   - `anon / public key`
   - `service_role key` (keep secure)

---

## 5. How to Configure OpenAI

1. Navigate to the [OpenAI Developer Platform](https://platform.openai.com).
2. Create an account, fund your platform balance, and go to **API Keys**.
3. Click **Create new secret key** and copy the value.
4. Ensure the key has permissions to invoke the embedding model (`text-embedding-3-small`) and the chat model (`gpt-4o-mini`).

---

## 6. How to Build Production Docker Images

When deploying, build production-optimized containers to minimize footprint:
```bash
# Navigate to the respective module directory containing the Dockerfile:
cd backend
docker build -t your-registry/backend:latest -f Dockerfile .

cd ../frontend
docker build -t your-registry/frontend:latest -f Dockerfile .
```

---

## 7. How to Push the Project to GitHub

1. Initialize git and commit files:
   ```bash
   git init
   git add .
   git commit -m "feat: complete production ready knowledge assistant codebase"
   ```
2. Connect to your GitHub repository and push (ensure `.env` files are ignored by checking `.gitignore`):
   ```bash
   git remote add origin <your-github-repo-url>
   git branch -M main
   git push -u origin main
   ```

---

## 8. How to Configure the Hostinger VPS

1. Purchase a **Hostinger VPS Plan** (Ubuntu 22.04 LTS or 24.04 LTS is recommended).
2. Access the Hostinger VPS Dashboard to view your **Server IP Address** and set your root SSH password.
3. Establish an SSH connection using a terminal:
   ```bash
   ssh root@<your-vps-ip-address>
   ```
4. Update the package registry on the system:
   ```bash
   apt update && apt upgrade -y
   ```

---

## 9. How to Install & Use Docker on the VPS

Run the following commands on your VPS terminal to install Docker:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Start and enable Docker daemon
systemctl start docker
systemctl enable docker

# Install Docker Compose plugin
apt install -y docker-compose-plugin
```

---

## 10. How to Configure Environment Variables on the VPS

1. On the VPS, create a deployment directory:
   ```bash
   mkdir -p /app/knowledge-assistant
   cd /app/knowledge-assistant
   ```
2. Create a production environment variable file `.env`:
   ```bash
   nano .env
   ```
3. Paste and configure the variables (ensure no spaces are present around `=`):
   ```bash
   # Host Domain name
   DOMAIN_NAME=yourdomain.com

    # Supabase Credentials
    SUPABASE_URL=your_supabase_url
    SUPABASE_ANON_KEY=your_supabase_anon_key
    SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
    SUPABASE_JWT_SECRET=your_supabase_jwt_signing_secret

    # OpenAI Key
    OPENAI_API_KEY=your_openai_api_key
    OPENAI_MODEL=gpt-4o-mini
    OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   ```

---

## 11. How to Deploy Docker Compose on the VPS

1. Transfer your project files (specifically `docker-compose.prod.yml`, `nginx.conf`, `backend/`, `frontend/`, and `mcp-server/`) to `/app/knowledge-assistant/` on the VPS using `git clone` or secure copy (`scp`):
   ```bash
   git clone <your-repo> /app/knowledge-assistant
   ```
2. Navigate to the `docker/` directory containing production compose files:
   ```bash
   cd /app/knowledge-assistant/docker
   ```
3. Run the containers in detached (background) mode:
   ```bash
   docker compose -f docker-compose.prod.yml --env-file ../.env up -d --build
   ```

---

## 12. How to Configure the Domain (DNS Settings)

1. Go to the domain registrar dashboard where you purchased your domain (e.g. Hostinger, GoDaddy, Namecheap).
2. Navigate to the **DNS Zone Editor**.
3. Create an **A Record** pointing to your Hostinger VPS IP:
   - **Type**: `A`
   - **Host / Name**: `@` (points to root domain)
   - **Value / IP Address**: `<your-vps-ip-address>`
   - **TTL**: Default (e.g., 3600)
4. Create a **CNAME / A Record** for `www` pointing to the root domain or VPS IP if desired.
5. Wait for DNS propagation (takes 5 minutes to 24 hours).

---

## 13. How to Configure HTTPS/SSL (Let's Encrypt)

Secure traffic with a free SSL certificate using Certbot:
```bash
# 1. Install Certbot on the host
apt install -y certbot

# 2. Stop the docker containers momentarily to free port 80
docker compose -f docker-compose.prod.yml down

# 3. Request the certificate
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# The certificate files will be generated at /etc/letsencrypt/live/yourdomain.com/

# 4. Restart your production containers
docker compose -f docker-compose.prod.yml --env-file ../.env up -d
```
*Note: Nginx in docker-compose.prod.yml mounts the `/etc/letsencrypt` folder from the host, mapping certificates automatically. To bind SSL inside Nginx, update `nginx.conf` on your domain setting, changing ports to `443 ssl` and mapping certificate files.*

---

## 14. How to Update the Application

To deploy updates without losing session configurations:
1. SSH into the VPS and pull the latest changes:
   ```bash
   cd /app/knowledge-assistant
   git pull
   ```
2. Build and restart only the modified services:
   ```bash
   cd docker
   docker compose -f docker-compose.prod.yml --env-file ../.env up -d --build
   ```

---

## 15. How to View Logs

Track running errors or trace completions:
```bash
# View backend container logs
docker logs -f backend_service

# View frontend container logs
docker logs -f frontend_service

# View Nginx proxy logs
docker logs -f proxy_service
```

---

## 16. How to Restart Services

```bash
# Restart all containers
docker compose -f docker-compose.prod.yml restart

# Restart a single service (e.g. backend)
docker restart backend_service
```

---

## 17. How to Back Up Important Configurations

Ensure you save the active environment parameters:
- Create backups of your host env configuration:
  ```bash
  cp /app/knowledge-assistant/.env /app/knowledge-assistant/backup.env
  ```
- *Supabase handles database backups and storage snapshots automatically on its managed dashboard.*

---

## 18. Troubleshooting Common Problems

### A. CORS Failures
- **Symptom**: Frontend console displays blocked origins warnings.
- **Fix**: Check `CORS_ORIGINS` in `.env`. Ensure it exactly matches your domain `["https://yourdomain.com"]` and has no trailing slash.

### B. Connection Refused / Backend Offline
- **Symptom**: Next.js fails to fetch `/api/health`.
- **Fix**: Verify Nginx can reach the backend container. Run `docker ps` to verify all services are running and healthy. Run `docker network inspect docker_app_network` to verify they are connected to the same bridge network.

### C. OpenAI / Supabase API Failures
- **Symptom**: Ingestion status marks failed, or chat yields error events.
- **Fix**: Inspect backend logs using `docker logs backend_service`. Check for expired API keys, insufficient platform balances, or invalid DB permissions.
