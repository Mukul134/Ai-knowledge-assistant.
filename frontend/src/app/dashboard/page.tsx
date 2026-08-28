"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase-client";
import { apiClient } from "@/lib/api-client";
import {
  MessageSquare,
  Plus,
  Trash2,
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  LogOut,
  Send,
  BookOpen,
  FolderOpen,
  Sparkles,
  Terminal,
  Database,
  RefreshCw,
  Edit2,
  User
} from "lucide-react";

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface Message {
  id?: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  citations?: Array<{ file_name: string; page_number: number }>;
}

interface Document {
  id: string;
  file_name: string;
  file_size: number;
  page_count: number | null;
  status: "uploaded" | "processing" | "completed" | "failed";
  error_message: string | null;
  created_at: string;
}

export default function WorkspacePage() {
  const router = useRouter();

  // Authentication states
  const [userEmail, setUserEmail] = useState<string>("");
  const [userName, setUserName] = useState<string>("");
  const [userJoined, setUserJoined] = useState<string>("");
  const [loadingSession, setLoadingSession] = useState(true);

  // View state: "chat" or "docs" or "profile"
  const [view, setView] = useState<"chat" | "docs" | "profile">("chat");

  // Chat sessions state
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState("Conversation Workspace");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  // Messages state
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // Document states
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Ref to handle auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Hook to check authentication and load base profile
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push("/login");
        return;
      }
      setUserEmail(session.user.email || "");
      setUserName(session.user.user_metadata?.full_name || "AI Assistant Member");
      
      const joinedDate = session.user.created_at
        ? new Date(session.user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
        : "Recent Member";
      setUserJoined(joinedDate);
      setLoadingSession(false);

      // Load sessions and documents
      loadSessions();
      loadDocuments();
    };

    checkAuth();
  }, [router]);

  // Auto-scroll to bottom on new messages or streaming chunks
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  // Load chat session listings
  const loadSessions = async () => {
    try {
      const list = await apiClient.get("/api/chat/session");
      setSessions(list);
      // Auto-select first session if present
      if (list.length > 0 && !activeSessionId) {
        selectSession(list[0].id, list[0].title);
      }
    } catch (err) {
      console.error("Failed to load chat sessions:", err);
    }
  };

  // Load documents metadata listings
  const loadDocuments = async () => {
    try {
      const list = await apiClient.get("/api/documents");
      setDocuments(list);
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  };

  // Set up polling for documents status changes
  useEffect(() => {
    if (view !== "docs") return;

    const interval = setInterval(() => {
      // Refresh documents status list while in document view to check parsing progress
      loadDocuments();
    }, 4000);

    return () => clearInterval(interval);
  }, [view]);

  // Create a new session thread
  const handleCreateSession = async () => {
    try {
      const newSession = await apiClient.post("/api/chat/session", {
        title: "New Conversation"
      });
      setSessions((prev) => [newSession, ...prev]);
      selectSession(newSession.id, newSession.title);
      setView("chat");
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  };

  // Select a session thread to view messages
  const selectSession = async (id: string, title: string) => {
    setActiveSessionId(id);
    setSessionTitle(title);
    setStreamingText("");
    try {
      const history = await apiClient.get(`/api/chat/session/${id}/messages`);
      setMessages(history);
    } catch (err) {
      console.error("Failed to load message history:", err);
    }
  };

  // Delete a session thread
  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.delete(`/api/chat/session/${id}`);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setMessages([]);
        setSessionTitle("Conversation Workspace");
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  // Rename a session thread
  const handleRenameSession = async (id: string) => {
    if (!renameValue.trim()) return;
    try {
      const updated = await apiClient.put(`/api/chat/session/${id}`, {
        title: renameValue
      });
      setSessions((prev) => prev.map((s) => (s.id === id ? updated : s)));
      if (activeSessionId === id) {
        setSessionTitle(updated.title);
      }
      setRenamingId(null);
    } catch (err) {
      console.error("Failed to rename session:", err);
    }
  };

  // Send a message over SSE streaming connection
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeSessionId || isGenerating) return;

    const userPrompt = inputMessage;
    setInputMessage("");
    setStreamingText("");
    setIsGenerating(true);

    // Optimistically update message logs with user prompt
    const userMessage: Message = { role: "user", content: userPrompt };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error("Authentication session expired.");

      const streamUrl = apiClient.getStreamUrl(`/api/chat/session/${activeSessionId}/stream`);

      const response = await fetch(streamUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ message: userPrompt })
      });

      if (!response.ok) {
        throw new Error(`Streaming request failed: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("Failed to read server event streams.");

      let fullAssistantText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const rawChunk = decoder.decode(value);
        const lines = rawChunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;

            try {
              const event = JSON.parse(dataStr);
              
              if (event.type === "text") {
                fullAssistantText += event.content;
                setStreamingText(fullAssistantText);
              } else if (event.type === "error") {
                console.error("SSE Generation error event:", event.content);
                setStreamingText((prev) => prev + `\n[System Error: ${event.content}]`);
              }
            } catch (err) {
              console.warn("Failed to parse SSE payload chunk:", dataStr);
            }
          }
        }
      }

      // Re-fetch messages from the backend to obtain the official saved logs with citations
      const updatedHistory = await apiClient.get(`/api/chat/session/${activeSessionId}/messages`);
      setMessages(updatedHistory);
      setStreamingText("");

    } catch (err: any) {
      console.error("Failed to stream answer:", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message || "Failed to generate answer"}` }
      ]);
    } finally {
      setIsGenerating(false);
    }
  };

  // Upload PDF file
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    try {
      await apiClient.uploadFile("/api/documents/upload", file);
      // Immediately refresh documents list
      await loadDocuments();
    } catch (err: any) {
      console.error("Upload failed:", err);
      setUploadError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  // Delete PDF file
  const handleDeleteDocument = async (id: string) => {
    try {
      await apiClient.delete(`/api/documents/${id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  // Human readable file size conversion helper
  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  };

  if (loadingSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-400 font-mono text-sm relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950/15 via-zinc-950 to-black pointer-events-none" />
        <div className="flex flex-col items-center justify-center gap-3 relative z-10">
          <Loader2 className="h-6 w-6 text-indigo-500 animate-spin" />
          <div className="animate-pulse tracking-wide font-sans text-xs text-zinc-500">Retrieving Secure Identity...</div>
        </div>
      </div>
    );
  }

  return (
    <main className="flex h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden relative">
      
      {/* LEFT SIDEBAR (Thread Management) */}
      <div className="w-80 bg-zinc-900/60 border-r border-zinc-800/80 flex flex-col flex-shrink-0 backdrop-blur-md relative z-10">
        
        {/* Profile Header */}
        <div className="p-5 border-b border-zinc-800/80 flex items-center justify-between">
          <div className="truncate space-y-1">
            <h2 className="font-extrabold text-sm text-zinc-100 tracking-tight flex items-center gap-1.5">
              <Sparkles size={14} className="text-indigo-400" />
              MukulAI Suite
            </h2>
            <p className="text-[10px] text-zinc-500 font-mono truncate">{userEmail}</p>
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            className="p-2 text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/60 rounded-xl transition-all"
          >
            <LogOut size={16} />
          </button>
        </div>

        {/* Action Panel */}
        <div className="p-4 space-y-3 border-b border-zinc-800/85">
          <button
            onClick={handleCreateSession}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl py-3 text-xs shadow-lg shadow-indigo-900/20 flex items-center justify-center gap-2 transition-all hover:scale-[1.01]"
          >
            <Plus size={14} /> New Conversation
          </button>
          
          <div className="grid grid-cols-3 gap-1 p-1 bg-zinc-950 rounded-xl border border-zinc-850">
            <button
              onClick={() => setView("chat")}
              className={`py-2 rounded-lg font-medium text-[10px] transition-all ${
                view === "chat"
                  ? "bg-zinc-800 text-zinc-200"
                  : "bg-transparent text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span className="flex items-center justify-center gap-1">
                <MessageSquare size={11} /> Chat
              </span>
            </button>
            <button
              onClick={() => setView("docs")}
              className={`py-2 rounded-lg font-medium text-[10px] transition-all ${
                view === "docs"
                  ? "bg-zinc-800 text-zinc-200"
                  : "bg-transparent text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span className="flex items-center justify-center gap-1">
                <FolderOpen size={11} /> Files
              </span>
            </button>
            <button
              onClick={() => setView("profile")}
              className={`py-2 rounded-lg font-medium text-[10px] transition-all ${
                view === "profile"
                  ? "bg-zinc-800 text-zinc-200"
                  : "bg-transparent text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span className="flex items-center justify-center gap-1">
                <User size={11} /> Profile
              </span>
            </button>
          </div>
        </div>

        {/* Sessions Thread List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1.5 scrollbar-thin select-none">
          <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-2 mb-2">History</h3>
          {sessions.length === 0 ? (
            <div className="text-center text-xs text-zinc-650 py-12">No active sessions</div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => selectSession(s.id, s.title)}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer border transition-all ${
                  activeSessionId === s.id
                    ? "bg-zinc-800/60 text-zinc-100 border-zinc-700/60 shadow-sm"
                    : "bg-transparent text-zinc-400 border-transparent hover:bg-zinc-850 hover:text-zinc-200"
                }`}
              >
                <div className="flex items-center gap-2.5 truncate flex-1">
                  <MessageSquare size={14} className={`flex-shrink-0 ${activeSessionId === s.id ? "text-indigo-400" : "text-zinc-500"}`} />
                  {renamingId === s.id ? (
                    <input
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onBlur={() => handleRenameSession(s.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRenameSession(s.id);
                        if (e.key === "Escape") setRenamingId(null);
                      }}
                      autoFocus
                      className="bg-zinc-950 border border-zinc-850 rounded text-xs px-2 py-0.5 text-zinc-100 focus:outline-none w-full"
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <span
                      onDoubleClick={(e) => {
                        e.stopPropagation();
                        setRenamingId(s.id);
                        setRenameValue(s.title);
                      }}
                      className="text-xs truncate font-medium"
                    >
                      {s.title}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setRenamingId(s.id);
                      setRenameValue(s.title);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-zinc-500 hover:text-zinc-200 rounded transition-all hover:bg-zinc-800"
                    title="Rename Thread"
                  >
                    <Edit2 size={11} />
                  </button>
                  <button
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-zinc-500 hover:text-rose-400 rounded transition-all hover:bg-zinc-800"
                    title="Delete Thread"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* MAIN WORKSPACE PANEL */}
      <div className="flex-1 flex flex-col min-w-0 bg-zinc-950 relative z-10">
        
        {/* Top Header Bar */}
        <div className="h-16 border-b border-zinc-900 flex items-center justify-between px-8 bg-zinc-950/60 backdrop-blur-md">
          <div className="flex items-center gap-3 truncate">
            <div className="h-2.5 w-2.5 rounded-full bg-indigo-500 shadow-lg shadow-indigo-500/50 flex-shrink-0 animate-pulse" />
            <h1 className="font-extrabold text-sm truncate text-zinc-200">{sessionTitle}</h1>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-400 bg-zinc-900 border border-zinc-850 px-3.5 py-1 rounded-full backdrop-blur-sm">
            {view === "chat" ? "Grounded AI Chat" : view === "docs" ? "Document Engine" : "Account Profile"}
          </span>
        </div>

        {/* View Routing */}
        {view === "chat" && (
          
          /* CHAT VIEWPORT */
          <div className="flex-1 flex flex-col min-h-0 bg-zinc-950">
            {/* Messages scroll viewport */}
            <div className="flex-1 overflow-y-auto p-8 space-y-8 scrollbar-thin">
              {messages.length === 0 && !streamingText ? (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-md mx-auto">
                  <div className="h-14 w-14 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 flex items-center justify-center text-indigo-400 shadow-xl shadow-zinc-950">
                    <Sparkles size={24} />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-zinc-200 font-bold text-sm">Grounded Knowledge workspace</h3>
                    <p className="text-xs text-zinc-550 leading-relaxed">
                      Ask questions about your uploaded documents. The AI agent will search your knowledge base and provide cited answers.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="max-w-3xl mx-auto space-y-6">
                  {messages.map((m, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col space-y-2 max-w-2xl ${
                        m.role === "user" ? "ml-auto items-end animate-slide-in-right" : "mr-auto items-start animate-slide-in-left"
                      }`}
                    >
                      <span className="text-[9px] text-zinc-500 uppercase tracking-widest font-bold font-mono">
                        {m.role === "user" ? "User Query" : "AI Agent"}
                      </span>
                      <div
                        className={`rounded-2xl px-5 py-3.5 text-sm leading-relaxed whitespace-pre-wrap shadow-md ${
                          m.role === "user"
                            ? "bg-indigo-600 text-white rounded-br-none"
                            : "bg-zinc-900/70 border border-zinc-800/60 text-zinc-200 rounded-bl-none"
                        }`}
                      >
                        {m.content}
                      </div>

                      {/* Display Citations */}
                      {m.role === "assistant" && m.citations && m.citations.length > 0 && (
                        <div className="flex flex-wrap gap-2 pt-1.5">
                          {m.citations.map((cite, cIdx) => (
                            <div
                              key={cIdx}
                              className="flex items-center gap-1.5 bg-zinc-900/60 border border-zinc-800/60 text-[9px] text-zinc-400 px-3 py-1 rounded-full font-medium shadow-sm hover:border-zinc-700 hover:text-zinc-300 transition-all cursor-default"
                            >
                              <BookOpen size={9} className="text-indigo-400" />
                              <span>{cite.file_name} • Page {cite.page_number}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Streaming Block */}
                  {streamingText && (
                    <div className="flex flex-col space-y-2 max-w-2xl mr-auto items-start animate-pulse">
                      <span className="text-[9px] text-zinc-500 uppercase tracking-widest font-bold font-mono flex items-center gap-1.5">
                        <Loader2 size={9} className="animate-spin text-indigo-400" /> AI Agent Reasoning...
                      </span>
                      <div className="rounded-2xl px-5 py-3.5 text-sm leading-relaxed bg-zinc-900/70 border border-zinc-800/60 text-zinc-200 rounded-bl-none whitespace-pre-wrap shadow-md">
                        {streamingText}
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="p-6 border-t border-zinc-900/80 bg-zinc-950">
              <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto flex items-center gap-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={
                    !activeSessionId
                      ? "Create or select a chat session first..."
                      : isGenerating
                      ? "Generating agent response..."
                      : "Ask about your documents (e.g. 'What does my resume say?')..."
                  }
                  disabled={!activeSessionId || isGenerating}
                  className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-5 py-3.5 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent transition-all disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!activeSessionId || !inputMessage.trim() || isGenerating}
                  className="p-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-900 text-white disabled:text-zinc-650 rounded-xl shadow-lg shadow-indigo-900/10 transition-all flex items-center justify-center"
                >
                  <Send size={16} />
                </button>
              </form>
            </div>
          </div>
        )}

        {view === "docs" && (
          
          /* DOCUMENT MANAGER VIEW */
          <div className="flex-1 overflow-y-auto p-8 space-y-8 max-w-4xl mx-auto w-full scrollbar-thin">
            
            {/* Upload Section */}
            <div className="space-y-4">
              <div className="space-y-1">
                <h2 className="text-lg font-bold text-zinc-200">File Ingestion Console</h2>
                <p className="text-xs text-zinc-550 leading-relaxed">
                  Upload layout-extracted PDF documents. Chunks and embeddings are processed asynchronously.
                </p>
              </div>
              
              <div className="relative border border-dashed border-zinc-800/80 hover:border-indigo-500/30 rounded-2xl p-10 text-center bg-zinc-900/10 backdrop-blur-sm transition-all group">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />
                <div className="flex flex-col items-center justify-center space-y-4">
                  <div className="h-12 w-12 rounded-2xl bg-zinc-950 border border-zinc-850 flex items-center justify-center text-zinc-400 group-hover:text-indigo-400 group-hover:border-indigo-500/20 shadow-md transition-all">
                    {uploading ? <Loader2 size={20} className="animate-spin text-indigo-500" /> : <UploadCloud size={20} />}
                  </div>
                  <div className="text-xs text-zinc-400">
                    {uploading ? (
                      <span className="font-semibold text-indigo-400">Uploading and registering PDF...</span>
                    ) : (
                      <span>
                        <span className="text-indigo-400 font-semibold hover:underline">Click to upload</span> or drag and drop a PDF file
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-zinc-650">PDF documents only, up to 10MB</p>
                </div>
              </div>

              {uploadError && (
                <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs p-4 rounded-xl flex items-start gap-2.5">
                  <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
                  <span>{uploadError}</span>
                </div>
              )}
            </div>

            {/* Ingested Documents List */}
            <div className="space-y-4">
              <h2 className="text-sm font-bold text-zinc-400 uppercase tracking-widest px-1">Document Registry ({documents.length})</h2>
              
              <div className="grid grid-cols-1 gap-3">
                {documents.length === 0 ? (
                  <div className="text-center py-20 bg-zinc-900/10 border border-zinc-900 rounded-2xl text-xs text-zinc-600 font-medium">
                    No documents registered in workspace database
                  </div>
                ) : (
                  documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="bg-zinc-900/30 border border-zinc-900 hover:border-zinc-800 rounded-xl p-4.5 flex items-center justify-between gap-4 transition-all"
                    >
                      <div className="flex items-center gap-3.5 truncate flex-1">
                        <div className="h-10 w-10 rounded-xl bg-zinc-950 border border-zinc-850 flex items-center justify-center text-indigo-400 flex-shrink-0">
                          <FileText size={18} />
                        </div>
                        <div className="truncate space-y-1">
                          <h3 className="text-xs font-bold text-zinc-200 truncate">{doc.file_name}</h3>
                          <div className="flex items-center gap-3 text-[10px] text-zinc-500 font-medium">
                            <span>{formatBytes(doc.file_size)}</span>
                            {doc.page_count !== null && (
                              <>
                                <span className="h-1.5 w-1.5 rounded-full bg-zinc-800" />
                                <span>{doc.page_count} pages</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {/* Status Badges */}
                        {doc.status === "completed" && (
                          <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full flex items-center gap-1.5">
                            <CheckCircle2 size={10} /> Active
                          </span>
                        )}
                        {doc.status === "processing" && (
                          <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full flex items-center gap-1.5 animate-pulse">
                            <RefreshCw size={10} className="animate-spin" /> Ingesting
                          </span>
                        )}
                        {doc.status === "uploaded" && (
                          <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full flex items-center gap-1.5">
                            <Loader2 size={10} className="animate-spin" /> Registered
                          </span>
                        )}
                        {doc.status === "failed" && (
                          <span
                            title={doc.error_message || "Ingestion process failed"}
                            className="text-[10px] font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded-full flex items-center gap-1.5 cursor-help"
                          >
                            <AlertCircle size={10} /> Failed
                          </span>
                        )}

                        <button
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="p-2 text-zinc-650 hover:text-rose-400 hover:bg-zinc-900 rounded-xl transition-all"
                          title="Remove Document"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {view === "profile" && (
          <div className="flex-1 overflow-y-auto p-8 space-y-8 max-w-4xl mx-auto w-full scrollbar-thin">
            <div className="space-y-4">
              <div className="space-y-1">
                <h2 className="text-lg font-bold text-zinc-200">Account Profile Dashboard</h2>
                <p className="text-xs text-zinc-550 leading-relaxed">
                  Manage your secure identity credentials and monitor storage utilization statistics.
                </p>
              </div>

              {/* Profile Card */}
              <div className="bg-zinc-900/30 border border-zinc-900 rounded-2xl p-6 flex flex-col md:flex-row items-center gap-6 backdrop-blur-sm">
                <div className="h-20 w-20 rounded-2xl bg-indigo-600/10 border border-indigo-500/25 flex items-center justify-center text-indigo-400 font-extrabold text-2xl shadow-xl shadow-zinc-950 flex-shrink-0">
                  {userName ? userName.slice(0, 2).toUpperCase() : "AI"}
                </div>
                <div className="space-y-2 text-center md:text-left flex-1 min-w-0">
                  <div>
                    <h3 className="text-lg font-extrabold text-zinc-100 truncate">{userName}</h3>
                    <p className="text-xs text-zinc-500 font-mono truncate">{userEmail}</p>
                  </div>
                  <div className="flex flex-wrap justify-center md:justify-start gap-4 text-[10px] text-zinc-400">
                    <span className="bg-zinc-950 border border-zinc-850 px-3 py-1 rounded-full font-medium">Joined {userJoined}</span>
                    <span className="bg-zinc-950 border border-zinc-850 px-3 py-1 rounded-full font-medium">Role: Authenticated Member</span>
                  </div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-zinc-900/20 border border-zinc-900 rounded-xl p-5 space-y-2">
                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="text-xs font-semibold">Total Documents</span>
                    <FolderOpen size={16} className="text-indigo-400" />
                  </div>
                  <p className="text-3xl font-extrabold text-zinc-100">{documents.length}</p>
                  <p className="text-[10px] text-zinc-600">PDF files indexed inside your private vector store</p>
                </div>
                
                <div className="bg-zinc-900/20 border border-zinc-900 rounded-xl p-5 space-y-2">
                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="text-xs font-semibold">Conversations</span>
                    <MessageSquare size={16} className="text-purple-400" />
                  </div>
                  <p className="text-3xl font-extrabold text-zinc-100">{sessions.length}</p>
                  <p className="text-[10px] text-zinc-600">Saved chat session threads</p>
                </div>
              </div>

              {/* Settings Core */}
              <div className="space-y-3 pt-4">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest px-1">Infrastructure Settings</h3>
                <div className="bg-zinc-900/20 border border-zinc-900 rounded-xl p-4.5 space-y-3 text-xs text-zinc-300">
                  <div className="flex items-center justify-between py-1 border-b border-zinc-850">
                    <span className="text-zinc-500 font-medium">Database Integration</span>
                    <span className="font-mono text-zinc-400">Supabase pgvector (active)</span>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-zinc-850">
                    <span className="text-zinc-500 font-medium">AI Model Config</span>
                    <span className="font-mono text-zinc-400">Gemini 2.5 Flash</span>
                  </div>
                  <div className="flex items-center justify-between py-1">
                    <span className="text-zinc-500 font-medium">Embedding Engine</span>
                    <span className="font-mono text-zinc-400">Gemini Embedding 2 (1536 dim)</span>
                  </div>
                </div>
              </div>

              {/* Logout panel */}
              <div className="pt-6 flex justify-end">
                <button
                  onClick={handleLogout}
                  className="bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 text-rose-400 font-bold rounded-xl px-6 py-3 text-xs shadow-md shadow-rose-950/20 flex items-center gap-2 transition-all hover:scale-[1.01]"
                >
                  <LogOut size={14} /> Log Out of Profile Session
                </button>
              </div>

            </div>
          </div>
        )}
      </div>

    </main>
  );
}
