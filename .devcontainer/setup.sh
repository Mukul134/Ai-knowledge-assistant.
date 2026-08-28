#!/bin/bash
echo "===> Setting up AI Knowledge Assistant Workspace..."

# 1. Install frontend dependencies
echo "===> Installing frontend node packages..."
cd frontend && npm install && cd ..

# 2. Set up backend dependencies (using virtualenv in backend)
echo "===> Installing backend python dependencies..."
cd backend
python -m venv venv
./venv/bin/pip install -r requirements.txt
cd ..

# 3. Create .env files if they don't exist
if [ ! -f backend/.env ]; then
  echo "===> Creating template backend/.env file..."
  cp backend/.env.example backend/.env 2>/dev/null || cat <<EOF > backend/.env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_JWT_SECRET=
OPENAI_API_KEY=your_gemini_api_key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-2.5-flash
OPENAI_EMBEDDING_MODEL=gemini-embedding-2
MCP_SERVER_PATH=../mcp-server/mcp_server.py
ENVIRONMENT=development
EOF
fi

if [ ! -f frontend/.env ]; then
  echo "===> Creating template frontend/.env file..."
  cat <<EOF > frontend/.env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
fi

echo "===> Workspace dependencies setup completed successfully!"
