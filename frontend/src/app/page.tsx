"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageSquare, ArrowRight, CheckCircle2, Shield, Brain, Files, Terminal, Database, Cpu } from "lucide-react";

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
    <main className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950/40 via-zinc-950 to-black text-zinc-100 font-sans flex flex-col justify-between selection:bg-indigo-500 selection:text-white relative overflow-hidden">
      
      {/* Decorative background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f29370a_1px,transparent_1px),linear-gradient(to_bottom,#1f29370a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Floating ambient glow */}
      <div className="absolute top-[-10%] left-[20%] w-[600px] h-[300px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-[10%] right-[10%] w-[400px] h-[200px] bg-purple-500/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Hero Header Section */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-5xl mx-auto w-full text-center space-y-8 my-16 relative z-10">
        
        {/* Release Tag */}
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 px-4 py-1.5 rounded-full text-xs font-semibold text-indigo-400 backdrop-blur-md shadow-inner animate-fade-in">
          <span className="h-2 w-2 rounded-full bg-indigo-400 animate-pulse" />
          MukulAI Workspace Platform
        </div>

        {/* Title */}
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-tight max-w-4xl text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 via-indigo-200 to-purple-300">
          Your Private Agentic <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">AI Knowledge Assistant</span>
        </h1>

        {/* Subtext */}
        <p className="text-sm md:text-base text-zinc-400 max-w-2xl leading-relaxed">
          Upload PDF files, chunk text segments automatically, and run conversational RAG chats. 
          Powered by an isolated stdio MCP server, pgvector similarity search, and Gemini models.
        </p>

        {/* Action CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-6 w-full sm:w-auto">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl px-8 py-4 text-sm shadow-xl shadow-indigo-900/20 flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98] group"
          >
            Go to Workspace Dashboard <ArrowRight size={16} className="group-hover:translate-x-1.5 transition-transform" />
          </Link>
          
          <Link
            href="/login"
            className="w-full sm:w-auto bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800/85 text-zinc-300 font-semibold rounded-xl px-8 py-4 text-sm backdrop-blur-md transition-all text-center hover:text-white"
          >
            Access Account / Log In
          </Link>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16 w-full text-left">
          
          <div className="bg-zinc-900/40 border border-zinc-900 rounded-2xl p-6 space-y-4 hover:border-indigo-500/25 transition-all hover:bg-zinc-900/60 group">
            <div className="h-10 w-10 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500/25 transition-all">
              <Brain size={20} />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-zinc-200">Grounded RAG Engine</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Gemini embeddings query PostgreSQL vector stores using strict Row-Level Security isolation.
              </p>
            </div>
          </div>

          <div className="bg-zinc-900/40 border border-zinc-900 rounded-2xl p-6 space-y-4 hover:border-purple-500/25 transition-all hover:bg-zinc-900/60 group">
            <div className="h-10 w-10 bg-purple-500/10 border border-purple-500/20 rounded-xl flex items-center justify-center text-purple-400 group-hover:bg-purple-500/25 transition-all">
              <Files size={20} />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-zinc-200">PDF Document Chunker</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Extracts layout-preserving text from PDFs, token-splits pages, and handles ingestion streams in the background.
              </p>
            </div>
          </div>

          <div className="bg-zinc-900/40 border border-zinc-900 rounded-2xl p-6 space-y-4 hover:border-pink-500/25 transition-all hover:bg-zinc-900/60 group">
            <div className="h-10 w-10 bg-pink-500/10 border border-pink-500/20 rounded-xl flex items-center justify-center text-pink-400 group-hover:bg-pink-500/25 transition-all">
              <Shield size={20} />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-zinc-200">Prompt Injection Guard</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Isolates database-retrieved chunks inside secure XML structures to prevent malicious instruction overrides.
              </p>
            </div>
          </div>

        </div>

      </div>

      {/* System Status Footer */}
      <footer className="border-t border-zinc-900 bg-zinc-950/80 backdrop-blur-md py-6 px-6 relative z-10">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          
          <div className="flex flex-wrap items-center justify-center gap-6">
            {/* Backend Integration Status */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold flex items-center gap-1">
                <Database size={10} /> Database API:
              </span>
              {loading ? (
                <span className="text-xs text-zinc-500 animate-pulse">Checking...</span>
              ) : error ? (
                <span className="text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2.5 py-0.5 rounded-full">Offline</span>
              ) : (
                <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                  <CheckCircle2 size={10} /> Online
                </span>
              )}
            </div>

            {/* MCP Status */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold flex items-center gap-1">
                <Cpu size={10} /> MCP Protocol:
              </span>
              <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <Terminal size={10} /> Stdio Pipe
              </span>
            </div>
          </div>

          <div className="text-[10px] text-zinc-600">
            Next.js 16 • FastAPI • Supabase • Gemini API
          </div>

        </div>
      </footer>

    </main>
  );
}
