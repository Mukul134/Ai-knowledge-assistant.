"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageSquare, ArrowRight, CheckCircle2, Shield, Brain, Files } from "lucide-react";

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
    <main className="min-h-screen bg-zinc-950 text-zinc-100 font-sans flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      
      {/* 1. HERO HEADER SECTION */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-5xl mx-auto w-full text-center space-y-8 my-12">
        
        {/* Release Tag */}
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/25 px-3.5 py-1.5 rounded-full text-xs font-semibold text-indigo-400">
          <span className="h-2 w-2 rounded-full bg-indigo-400 animate-pulse" />
          Production-Ready Release
        </div>

        {/* Title */}
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight max-w-3xl text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 via-purple-300 to-pink-300">
          Your Private Agentic AI Knowledge Assistant
        </h1>

        {/* Subtext */}
        <p className="text-sm md:text-base text-zinc-400 max-w-2xl leading-relaxed">
          Upload PDF files, chunk text segments automatically, and run conversational RAG chats. 
          Powered by an isolated stdio MCP server, pgvector similarity search, and OpenAI models.
        </p>

        {/* Action CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl px-8 py-3.5 text-sm shadow-xl flex items-center justify-center gap-2 transition-all group"
          >
            Go to Workspace Dashboard <ArrowRight size={16} className="group-hover:translate-x-1.5 transition-transform" />
          </Link>
          
          <Link
            href="/login"
            className="w-full sm:w-auto bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 font-semibold rounded-xl px-8 py-3.5 text-sm transition-all text-center"
          >
            Access Account / Log In
          </Link>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12 w-full text-left">
          
          <div className="bg-zinc-900/40 border border-zinc-900 rounded-2xl p-6 space-y-3">
            <div className="h-10 w-10 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex items-center justify-center text-indigo-400">
              <Brain size={20} />
            </div>
            <h3 className="text-sm font-bold text-zinc-200">Grounded RAG Engine</h3>
            <p className="text-xs text-zinc-550 leading-relaxed">
              OpenAI embeddings query PostgreSQL vector stores using strict Row-Level Security isolation.
            </p>
          </div>

          <div className="bg-zinc-900/40 border border-zinc-900 rounded-2xl p-6 space-y-3">
            <div className="h-10 w-10 bg-purple-500/10 border border-purple-500/20 rounded-xl flex items-center justify-center text-purple-400">
              <Files size={20} />
            </div>
            <h3 className="text-sm font-bold text-zinc-200">PDF Document Chunker</h3>
            <p className="text-xs text-zinc-550 leading-relaxed">
              Extracts layout-preserving text from PDFs, token-splits pages, and handles ingestion streams in the background.
            </p>
          </div>

          <div className="bg-zinc-900/40 border border-zinc-900 rounded-2xl p-6 space-y-3">
            <div className="h-10 w-10 bg-pink-500/10 border border-pink-500/20 rounded-xl flex items-center justify-center text-pink-400">
              <Shield size={20} />
            </div>
            <h3 className="text-sm font-bold text-zinc-200">Prompt Injection Guard</h3>
            <p className="text-xs text-zinc-550 leading-relaxed">
              Isolates database retrieved chunks inside XML containers to prevent instructions overrides.
            </p>
          </div>

        </div>

      </div>

      {/* 2. SYSTEM STATUS FOOTER */}
      <footer className="border-t border-zinc-900 bg-zinc-950/80 backdrop-blur-md py-6 px-6">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          
          <div className="flex items-center gap-6">
            {/* Backend Integration Status */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">API Services:</span>
              {loading ? (
                <span className="text-xs text-zinc-500 animate-pulse">Checking status...</span>
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
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">MCP Core:</span>
              <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <MessageSquare size={10} /> Stdio Subprocess
              </span>
            </div>
          </div>

          <div className="text-[10px] text-zinc-650">
            Powered by Next.js App Router, FastAPI, and Supabase Database.
          </div>

        </div>
      </footer>

    </main>
  );
}
