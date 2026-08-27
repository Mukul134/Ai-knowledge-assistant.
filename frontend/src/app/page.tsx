"use client";

import { useEffect, useState } from "react";

interface HealthData {
  status: string;
  project: string;
  environment: string;
  openai_configured: boolean;
  supabase_configured: boolean;
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/health`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setHealth(data);
        setError(null);
      } catch (err: any) {
        console.error("Health check fetch failed:", err);
        setError(err.message || "Failed to connect to backend API");
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-zinc-100 p-6 font-sans">
      <div className="w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-2xl space-y-8 backdrop-blur-md">
        
        {/* Header */}
        <div className="space-y-2 border-b border-zinc-800 pb-6">
          <div className="flex items-center gap-3">
            <div className="h-4 w-4 rounded-full bg-indigo-500 animate-pulse" />
            <span className="text-xs uppercase tracking-widest text-zinc-400 font-semibold">Phase 1 Active</span>
          </div>
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
            AI Knowledge Assistant
          </h1>
          <p className="text-sm text-zinc-400">
            System initialization verification and project workspace config dashboard.
          </p>
        </div>

        {/* Workspace Health Section */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-zinc-300">Monorepo Integration Status</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Backend Service Status */}
            <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-zinc-400">Backend API</span>
                {loading ? (
                  <span className="text-xs text-zinc-500">Checking...</span>
                ) : error ? (
                  <span className="text-xs font-semibold text-rose-500 bg-rose-500/10 px-2 py-0.5 rounded-full">Offline</span>
                ) : (
                  <span className="text-xs font-semibold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">Online</span>
                )}
              </div>
              <div className="text-xs text-zinc-500 space-y-1">
                <p>Host: <span className="font-mono text-zinc-300">localhost:8000</span></p>
                <p>Status: <span className="font-mono text-zinc-300">{health?.status || "Unknown"}</span></p>
              </div>
            </div>

            {/* MCP Server Status */}
            <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-zinc-400">MCP Server</span>
                <span className="text-xs font-semibold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-full">Ready</span>
              </div>
              <div className="text-xs text-zinc-500 space-y-1">
                <p>Transport: <span className="font-mono text-zinc-300">stdio / JSON-RPC</span></p>
                <p>Tools: <span className="font-mono text-zinc-300">search_knowledge, list_docs...</span></p>
              </div>
            </div>

          </div>
        </div>

        {/* API Response Data */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-zinc-300">Live Health Report</h2>
          <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 font-mono text-xs overflow-x-auto min-h-[100px] flex items-center justify-center">
            {loading ? (
              <div className="text-zinc-500 animate-pulse">Requesting system credentials...</div>
            ) : error ? (
              <div className="text-rose-400 w-full">
                <p className="font-bold text-rose-500">Connection Failed</p>
                <p className="mt-1">{error}</p>
                <p className="mt-2 text-[10px] text-zinc-650">Verify python backend app/main.py is running on port 8000.</p>
              </div>
            ) : (
              <pre className="text-zinc-300 w-full">{JSON.stringify(health, null, 2)}</pre>
            )}
          </div>
        </div>

        {/* Navigation instructions */}
        <div className="text-center pt-2 text-xs text-zinc-500">
          Ready for <span className="text-indigo-400 font-semibold">Phase 2</span>: Supabase and Database Migrations.
        </div>
      </div>
    </main>
  );
}
