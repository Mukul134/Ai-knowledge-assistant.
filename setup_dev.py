import os
import subprocess
import sys
import shutil

def run_cmd(args, cwd=None):
    cmd_str = " ".join(args)
    print(f"Running command: {cmd_str} (in {cwd or '.'})")
    try:
        subprocess.check_call(args, cwd=cwd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd_str}")
        print(e)
        sys.exit(1)

def setup_envs():
    print("\n--- Setting up environment variable files ---")
    
    # Backend .env
    backend_env_ex = os.path.join("backend", ".env.example")
    backend_env = os.path.join("backend", ".env")
    if os.path.exists(backend_env_ex) and not os.path.exists(backend_env):
        print(f"Copying {backend_env_ex} -> {backend_env}")
        shutil.copy(backend_env_ex, backend_env)
    else:
        print(f"Backend .env already exists or .env.example is missing.")

    # Frontend .env
    frontend_env_ex = os.path.join("frontend", ".env.example")
    frontend_env = os.path.join("frontend", ".env")
    if os.path.exists(frontend_env_ex) and not os.path.exists(frontend_env):
        print(f"Copying {frontend_env_ex} -> {frontend_env}")
        shutil.copy(frontend_env_ex, frontend_env)
    else:
        print(f"Frontend .env already exists or .env.example is missing.")

def main():
    print("=== AI Knowledge Assistant Development Workspace Setup ===")
    
    # 1. Setup env files
    setup_envs()

    # 2. Install backend dependencies
    print("\n--- Installing Backend dependencies ---")
    run_cmd([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])

    # 3. Install MCP server dependencies
    print("\n--- Installing MCP Server dependencies ---")
    run_cmd([sys.executable, "-m", "pip", "install", "-r", "mcp-server/requirements.txt"])

    # 4. Install frontend dependencies
    print("\n--- Installing Frontend NPM dependencies ---")
    if os.path.exists("frontend"):
        run_cmd(["npm", "install"], cwd="frontend")
    else:
        print("Frontend directory not found! Skipped.")

    print("\n=== Setup completed successfully! ===")
    print("To start the backend: python backend/app/main.py")
    print("To start the frontend: npm run dev --prefix frontend")
    print("To start the MCP server: python mcp-server/mcp_server.py")

if __name__ == "__main__":
    main()
