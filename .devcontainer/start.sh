#!/bin/bash
echo "===> Starting Backend and Frontend servers..."

# 1. Start FastAPI backend in the background
cd backend
./venv/bin/python -m app.main > backend.log 2>&1 &
echo "FastAPI backend started in the background (PID: $!)."
cd ..

# 2. Start Next.js frontend in the background
cd frontend
npm run dev > frontend.log 2>&1 &
echo "Next.js frontend dev server started in the background (PID: $!)."
cd ..

echo "===> Servers started! Port 3000 will open in your browser shortly."
